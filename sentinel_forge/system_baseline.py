"""Read-only, bounded local resource baseline collection for Sentinel Forge."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import shutil

from .enrollment import EnrollmentError


@dataclass(frozen=True)
class SystemBaseline:
    collected_at_utc: str
    hostname: str
    os: str
    kernel: str
    cpu_count: int
    load_1m: float
    load_5m: float
    load_15m: float
    memory_total_bytes: int
    memory_available_bytes: int
    swap_total_bytes: int
    swap_free_bytes: int
    root_total_bytes: int
    root_used_bytes: int
    root_free_bytes: int

    def as_dict(self) -> dict[str, object]:
        return self.__dict__.copy()


def _meminfo() -> dict[str, int]:
    out: dict[str, int] = {}
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            key, raw = line.split(":", 1)
            value = raw.strip().split()
            if not value:
                continue
            # Linux meminfo values used here are kB.
            out[key] = int(value[0]) * 1024
    except (OSError, ValueError) as exc:
        raise EnrollmentError("system memory telemetry unavailable") from exc
    return out


def collect_system_baseline() -> SystemBaseline:
    mem = _meminfo()
    required = ("MemTotal", "MemAvailable", "SwapTotal", "SwapFree")
    if any(k not in mem for k in required):
        raise EnrollmentError("system memory telemetry incomplete")
    try:
        load1, load5, load15 = os.getloadavg()
        disk = shutil.disk_usage("/")
    except OSError as exc:
        raise EnrollmentError("system resource telemetry unavailable") from exc

    return SystemBaseline(
        collected_at_utc=datetime.now(timezone.utc).isoformat(),
        hostname=platform.node(),
        os=platform.platform(),
        kernel=platform.release(),
        cpu_count=os.cpu_count() or 0,
        load_1m=load1,
        load_5m=load5,
        load_15m=load15,
        memory_total_bytes=mem["MemTotal"],
        memory_available_bytes=mem["MemAvailable"],
        swap_total_bytes=mem["SwapTotal"],
        swap_free_bytes=mem["SwapFree"],
        root_total_bytes=disk.total,
        root_used_bytes=disk.used,
        root_free_bytes=disk.free,
    )


def baseline_tool(_: str) -> str:
    """ForgeAiEngine tool adapter. Input is deliberately ignored."""
    return json.dumps(collect_system_baseline().as_dict(), sort_keys=True)


def write_baseline_record(directory: str | Path) -> Path:
    base = collect_system_baseline()
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    stamp = base.collected_at_utc.replace(":", "").replace("+00:00", "Z").replace(".", "-")
    path = directory / f"forge-system-baseline-{stamp}.json"
    payload = json.dumps(base.as_dict(), sort_keys=True, indent=2) + "\n"
    # Exclusive creation: a baseline record is evidence, never overwritten.
    with path.open("x", encoding="utf-8") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    return path
