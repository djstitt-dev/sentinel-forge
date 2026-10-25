"""Loopback-only persistent llama.cpp provider owned by the Forge console process."""
from __future__ import annotations

from dataclasses import dataclass
import json
import logging
import socket
import threading
from pathlib import Path
import subprocess
import time
from urllib import error, request

from .enrollment import EnrollmentError

_LOG = logging.getLogger(__name__)


def clean_model_response(output: str) -> str:
    output = output.strip()
    if output.startswith("</think>"):
        output = output[len("</think>"):].lstrip()
    elif output.startswith("<think>") and "</think>" in output:
        thought, remainder = output.split("</think>", 1)
        if not thought.removeprefix("<think>").strip():
            output = remainder.strip()
    return output



@dataclass(frozen=True)
class PersistentModelConfig:
    executable: str
    model_path: str
    host: str = "127.0.0.1"
    port: int = 18081
    timeout_seconds: int = 300
    startup_seconds: int = 180
    max_tokens: int = 512
    thinking: bool = False


class PersistentLocalModel:
    provider_id = "sentinel-local-persistent-model-v1"

    def __init__(self, config: PersistentModelConfig, popen=subprocess.Popen):
        if not isinstance(config, PersistentModelConfig):
            raise EnrollmentError("persistent model configuration required")
        if config.host != "127.0.0.1":
            raise EnrollmentError("persistent model must bind loopback")
        if not Path(config.executable).is_absolute() or not Path(config.model_path).is_absolute():
            raise EnrollmentError("persistent model paths must be absolute")
        if type(config.port) is not int or not 1024 <= config.port <= 65535:
            raise EnrollmentError("persistent model port invalid")
        if type(config.timeout_seconds) is not int or not 1 <= config.timeout_seconds <= 900:
            raise EnrollmentError("persistent model timeout invalid")
        if type(config.startup_seconds) is not int or not 1 <= config.startup_seconds <= 300:
            raise EnrollmentError("persistent model startup timeout invalid")
        if type(config.max_tokens) is not int or not 1 <= config.max_tokens <= 4096:
            raise EnrollmentError("persistent model token limit invalid")
        if type(config.thinking) is not bool:
            raise EnrollmentError("persistent model thinking mode invalid")
        self.config = config
        self._popen = popen
        self._process = None
        self._diagnostic_thread = None
        self.diagnostics = {"bytes_drained": 0, "error_blocks": 0, "warning_blocks": 0}
        self.last_exit_code = None

    @property
    def base_url(self) -> str:
        return f"http://{self.config.host}:{self.config.port}"

    def _drain_diagnostics(self, stream) -> None:
        # Never retain or emit raw child bytes: they may contain prompt text,
        # model paths, credentials, or terminal escapes. Counts are bounded state.
        try:
            while True:
                block = stream.read(4096)
                if not block:
                    break
                self.diagnostics["bytes_drained"] += len(block)
                lower = block.lower()
                self.diagnostics["error_blocks"] += int(b"error" in lower)
                self.diagnostics["warning_blocks"] += int(b"warning" in lower)
        finally:
            stream.close()

    def start(self) -> None:
        try:
            self._start()
        except BaseException:
            self.close()
            raise

    def _start(self) -> None:
        if self._process is not None and self._process.poll() is None:
            return
        self.close()
        # Refuse an occupied port before launching; never send prompts to a
        # known pre-existing listener. There remains a bind race (see design note).
        try:
            with socket.socket() as probe:
                probe.bind((self.config.host, self.config.port))
        except OSError as exc:
            raise EnrollmentError("persistent local model port unavailable") from exc
        argv = (
            self.config.executable,
            "-m", self.config.model_path,
            "--host", self.config.host,
            "--port", str(self.config.port),
            "--parallel", "1",
            "--no-webui",
            "--no-slots",
            "--threads", "4",
            "--ctx-size", "8192",
        )
        try:
            self._process = self._popen(
                argv,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=False,
                shell=False,
            )
        except OSError as exc:
            raise EnrollmentError("persistent local model unavailable") from exc

        self.diagnostics = {"bytes_drained": 0, "error_blocks": 0, "warning_blocks": 0}
        self._diagnostic_thread = threading.Thread(
            target=self._drain_diagnostics, args=(self._process.stdout,), daemon=True,
            name="forge-llama-diagnostics",
        )
        self._diagnostic_thread.start()
        _LOG.debug("local model child started")
        deadline = time.monotonic() + self.config.startup_seconds
        while time.monotonic() < deadline:
            if self._process.poll() is not None:
                self.close()
                raise EnrollmentError("persistent local model exited during startup")
            try:
                with request.urlopen(self.base_url + "/health", timeout=2) as response:
                    if response.status == 200:
                        return
            except (error.URLError, TimeoutError, OSError):
                time.sleep(0.25)
        self.close()
        raise EnrollmentError("persistent local model startup timed out")

    def close(self) -> None:
        process = self._process
        if process is not None:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
            self.last_exit_code = process.poll()
            self._process = None
        if self._diagnostic_thread is not None:
            self._diagnostic_thread.join(timeout=2)
            self._diagnostic_thread = None
        if process is not None:
            _LOG.debug("local model child stopped exit=%s diagnostics=%s",
                       self.last_exit_code, self.diagnostics)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def build_prompt(self, command: str, context: str) -> str:
        if not isinstance(command, str) or not command.strip():
            raise EnrollmentError("model command required")
        mode = "" if self.config.thinking else "/no_think\n"
        prompt = (
            mode
            + "SYSTEM: You are Sentinel Forge's offline operator assistant. "
              "Model output is advisory and grants no authority. "
              "Never claim an action was executed unless execution evidence is supplied.\n"
            + ("CONTEXT:\n" + context + "\n" if context else "")
            + "OPERATOR:\n" + command + "\nASSISTANT:\n"
        )
        return prompt

    def respond(self, command: str, context: str) -> str:
        prompt = self.build_prompt(command, context)
        self.start()
        body = json.dumps(
            {
                "prompt": prompt,
                "n_predict": self.config.max_tokens,
                "temperature": 0,
                "stream": False,
            }
        ).encode("utf-8")
        req = request.Request(
            self.base_url + "/completion",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=self.config.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            raise EnrollmentError("persistent local model request failed") from exc
        if not isinstance(payload, dict):
            raise EnrollmentError("persistent local model returned invalid response")
        output = payload.get("content")
        if not isinstance(output, str) or not output.strip():
            raise EnrollmentError("persistent local model returned empty response")
        output = clean_model_response(output)
        if not output:
            raise EnrollmentError("persistent local model returned empty response")
        return output
