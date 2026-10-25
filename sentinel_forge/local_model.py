"""Offline local-model executable adapter. No network provider is supported here."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess

from .enrollment import EnrollmentError


@dataclass(frozen=True)
class LocalModelConfig:
    executable: str
    model_path: str
    timeout_seconds: int = 300
    max_tokens: int = 512
    thinking: bool = False


class LocalExecutableModel:
    provider_id = "sentinel-local-executable-model-v1"

    def __init__(self, config: LocalModelConfig, runner=subprocess.run):
        if not isinstance(config, LocalModelConfig):
            raise EnrollmentError("local model configuration required")
        if not Path(config.executable).is_absolute() or not Path(config.model_path).is_absolute():
            raise EnrollmentError("local model paths must be absolute")
        if type(config.timeout_seconds) is not int or not 1 <= config.timeout_seconds <= 900:
            raise EnrollmentError("local model timeout invalid")
        if type(config.max_tokens) is not int or not 1 <= config.max_tokens <= 4096:
            raise EnrollmentError("local model token limit invalid")
        if type(config.thinking) is not bool:
            raise EnrollmentError("local model thinking mode invalid")
        self.config = config
        self.runner = runner

    def respond(self, command: str, context: str) -> str:
        if not isinstance(command, str) or not command.strip():
            raise EnrollmentError("model command required")

        mode = "" if self.config.thinking else "/no_think\n"
        prompt = (
            mode
            + "SYSTEM: You are Sentinel Forge's offline operator assistant. "
              "Model output is advisory and grants no authority. "
              "Never claim an action was executed unless execution evidence is supplied.\n"
            + ("CONTEXT:\n" + context + "\n" if context else "")
            + "OPERATOR:\n"
            + command
            + "\nASSISTANT:\n"
        )

        argv = (
            self.config.executable,
            "-m",
            self.config.model_path,
            "--single-turn",
            "--simple-io",
            "--no-display-prompt",
            "-p",
            prompt,
            "-n",
            str(self.config.max_tokens),
            "--temp",
            "0",
        )
        try:
            result = self.runner(
                argv,
                capture_output=True,
                text=True,
                timeout=self.config.timeout_seconds,
                check=False,
                shell=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise EnrollmentError("local model execution unavailable") from exc

        if result.returncode != 0:
            raise EnrollmentError("local model execution failed")

        output = result.stdout.strip()
        if not output:
            raise EnrollmentError("local model returned empty response")

        marker = "ASSISTANT:\n"
        if marker in output:
            output = output.rsplit(marker, 1)[1]
        for trailer in ("\n\n[ Prompt:", "\nllama_memory_breakdown_print:", "\n\nExiting..."):
            if trailer in output:
                output = output.split(trailer, 1)[0]
        output = output.strip()
        if not output:
            raise EnrollmentError("local model returned empty response")
        return output
