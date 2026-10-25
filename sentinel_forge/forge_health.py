"""Bounded, read-only health snapshot for the local Sentinel Forge node."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess

from .enrollment import EnrollmentError
from .system_baseline import collect_system_baseline

REPO_ROOT = Path(__file__).resolve().parent.parent
MODEL_RELATIVE = Path("models/qwen3-8b/Qwen3-8B-Q4_K_M.gguf")
MODEL_EXPECTED_SHA256 = "d98cdcbd03e17ce47681435b5150e34c1417f50b5c0019dd560e4882c5745785"


def _read_proc_model_processes() -> list[dict[str, object]]:
    found: list[dict[str, object]] = []
    proc = Path("/proc")
    try:
        entries = list(proc.iterdir())
    except OSError as exc:
        raise EnrollmentError("process telemetry unavailable") from exc
    for entry in entries:
        if not entry.name.isdigit():
            continue
        try:
            raw = (entry / "cmdline").read_bytes()
        except (OSError, PermissionError):
            continue
        cmd = raw.replace(b"\0", b" ").decode("utf-8", errors="replace").strip()
        if "llama-cli" not in cmd and "llama-server" not in cmd:
            continue
        try:
            status = (entry / "status").read_text()
        except (OSError, PermissionError):
            status = ""
        rss_kib = 0
        for line in status.splitlines():
            if line.startswith("VmRSS:"):
                parts = line.split()
                if len(parts) >= 2 and parts[1].isdigit():
                    rss_kib = int(parts[1])
                break
        found.append({"pid": int(entry.name), "rss_kib": rss_kib, "command": cmd[:512]})
    return sorted(found, key=lambda item: int(item["pid"]))


def _git(*args: str) -> str:
    try:
        result = subprocess.run(
            ("git", "-C", str(REPO_ROOT), *args),
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
            shell=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise EnrollmentError("repository health telemetry unavailable") from exc
    if result.returncode != 0:
        raise EnrollmentError("repository health telemetry failed")
    return result.stdout.strip()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise EnrollmentError("model integrity telemetry unavailable") from exc
    return digest.hexdigest()


def collect_forge_health(*, verify_model_digest: bool = False) -> dict[str, object]:
    baseline = collect_system_baseline()
    model_path = REPO_ROOT / MODEL_RELATIVE
    model_present = model_path.is_file()
    actual_digest = _sha256(model_path) if model_present and verify_model_digest else None

    status_lines = _git("status", "--porcelain").splitlines()
    branch = _git("rev-parse", "--abbrev-ref", "HEAD")
    head = _git("rev-parse", "HEAD")

    required_components = (
        "ai_engine.py",
        "ai_console.py",
        "ai_runtime.py",
        "system_baseline.py",
        "forge_health.py",
        "courier_completion.py",
        "courier_completion_runner.py",
    )
    components = {
        name: (REPO_ROOT / "sentinel_forge" / name).is_file()
        for name in required_components
    }

    return {
        "collected_at_utc": datetime.now(timezone.utc).isoformat(),
        "node": {
            "hostname": baseline.hostname,
            "cpu_count": baseline.cpu_count,
            "load_1m": baseline.load_1m,
            "load_5m": baseline.load_5m,
            "load_15m": baseline.load_15m,
            "memory_total_bytes": baseline.memory_total_bytes,
            "memory_available_bytes": baseline.memory_available_bytes,
            "swap_total_bytes": baseline.swap_total_bytes,
            "swap_free_bytes": baseline.swap_free_bytes,
            "root_total_bytes": baseline.root_total_bytes,
            "root_used_bytes": baseline.root_used_bytes,
            "root_free_bytes": baseline.root_free_bytes,
        },
        "local_ai": {
            "executable_present": Path("/usr/bin/llama-cli").is_file(),
            "model_present": model_present,
            "model_size_bytes": model_path.stat().st_size if model_present else 0,
            "expected_model_sha256": MODEL_EXPECTED_SHA256,
            "actual_model_sha256": actual_digest,
            "model_digest_verified": actual_digest == MODEL_EXPECTED_SHA256 if actual_digest else None,
            "active_model_processes": _read_proc_model_processes(),
        },
        "repository": {
            "branch": branch,
            "head": head,
            "worktree_change_count": len(status_lines),
            "worktree_clean": len(status_lines) == 0,
        },
        "sentinel_components": components,
        "security": {
            "tool_mode": "read-only",
            "network_probe_performed": False,
            "sudo_used": False,
            "arbitrary_shell_input_accepted": False,
        },
    }


def forge_health_tool(_: str) -> str:
    return json.dumps(collect_forge_health(), sort_keys=True)
