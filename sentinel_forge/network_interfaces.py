"""Read-only current network-interface observation for Sentinel Forge."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import subprocess

from .enrollment import EnrollmentError

IP_EXECUTABLE = "/usr/sbin/ip"


def collect_network_interfaces(*, runner=subprocess.run) -> dict[str, object]:
    argv = (IP_EXECUTABLE, "-j", "address", "show")
    try:
        result = runner(
            argv,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
            shell=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise EnrollmentError("network interface observation unavailable") from exc
    if result.returncode != 0:
        raise EnrollmentError("network interface observation failed")
    try:
        raw = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise EnrollmentError("network interface observation invalid") from exc
    if not isinstance(raw, list):
        raise EnrollmentError("network interface observation invalid")

    interfaces: list[dict[str, object]] = []
    primary_ipv4: list[str] = []
    for item in raw:
        if not isinstance(item, dict):
            raise EnrollmentError("network interface record invalid")
        name = item.get("ifname")
        if not isinstance(name, str) or not name:
            raise EnrollmentError("network interface name invalid")
        addresses: list[dict[str, object]] = []
        addr_info = item.get("addr_info", [])
        if not isinstance(addr_info, list):
            raise EnrollmentError("network address list invalid")
        for addr in addr_info:
            if not isinstance(addr, dict):
                raise EnrollmentError("network address record invalid")
            family = addr.get("family")
            local = addr.get("local")
            prefixlen = addr.get("prefixlen")
            scope = addr.get("scope")
            if family not in {"inet", "inet6"} or not isinstance(local, str):
                continue
            if type(prefixlen) is not int or not isinstance(scope, str):
                raise EnrollmentError("network address fields invalid")
            record = {
                "family": "ipv4" if family == "inet" else "ipv6",
                "address": local,
                "prefix_length": prefixlen,
                "scope": scope,
                "dynamic": addr.get("dynamic") is True,
            }
            addresses.append(record)
            if family == "inet" and scope == "global" and name != "lo":
                primary_ipv4.append(local)
        interfaces.append(
            {
                "name": name,
                "state": item.get("operstate") if isinstance(item.get("operstate"), str) else "UNKNOWN",
                "mtu": item.get("mtu") if type(item.get("mtu")) is int else None,
                "addresses": addresses,
            }
        )

    return {
        "collected_at_utc": datetime.now(timezone.utc).isoformat(),
        "hostname_scope": "local Forge host",
        "primary_global_ipv4": primary_ipv4,
        "interfaces": interfaces,
        "observation": {
            "read_only": True,
            "network_probe_performed": False,
            "configuration_changed": False,
            "arbitrary_shell_input_accepted": False,
            "argv": list(argv),
        },
    }


def network_interfaces_tool(_: str) -> str:
    return json.dumps(collect_network_interfaces(), sort_keys=True)
