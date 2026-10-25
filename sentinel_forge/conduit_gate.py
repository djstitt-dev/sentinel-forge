"""Fail-closed Sentinel Conduit forced-command parser and peer authorization."""

from __future__ import annotations

from dataclasses import dataclass
import re
import shlex

from .enrollment import EnrollmentError


_ALLOWED_OPERATIONS = frozenset({
    "status",
    "capabilities",
})

_PEER_IDENTITY_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass(frozen=True)
class ConduitRequest:
    operation: str
    peer_identity: str


def _validate_peer_identity(peer_identity: str) -> str:
    if not isinstance(peer_identity, str) or not peer_identity:
        raise EnrollmentError("Conduit peer identity required")

    if len(peer_identity) > 128:
        raise EnrollmentError("Conduit peer identity too long")

    if _PEER_IDENTITY_RE.fullmatch(peer_identity) is None:
        raise EnrollmentError("Conduit peer identity is not canonical")

    return peer_identity


def parse_forced_command(original_command: str) -> ConduitRequest:
    """Parse exactly one approved Sentinel Conduit forced command.

    Accepted syntax:

        sentinel-conduit <operation> --peer <canonical-peer-id>

    No additional arguments, shell syntax, or unknown operations are allowed.
    """

    if not isinstance(original_command, str) or not original_command.strip():
        raise EnrollmentError("Conduit original command required")

    try:
        argv = shlex.split(original_command, posix=True)
    except ValueError as exc:
        raise EnrollmentError("Conduit command parsing failed") from exc

    if len(argv) != 4:
        raise EnrollmentError("Conduit command shape invalid")

    executable, operation, peer_flag, peer_identity = argv

    if executable != "sentinel-conduit":
        raise EnrollmentError("Conduit command executable invalid")

    if operation not in _ALLOWED_OPERATIONS:
        raise EnrollmentError("Conduit operation not permitted")

    if peer_flag != "--peer":
        raise EnrollmentError("Conduit peer binding required")

    _validate_peer_identity(peer_identity)

    # shlex tokenization alone is not sufficient as shell metacharacters may
    # remain embedded in otherwise parseable tokens. Require reconstruction
    # to match the canonical command exactly.
    canonical = f"sentinel-conduit {operation} --peer {peer_identity}"
    if original_command != canonical:
        raise EnrollmentError("Conduit command is not canonical")

    return ConduitRequest(
        operation=operation,
        peer_identity=peer_identity,
    )


def authorize_request(
    request: ConduitRequest,
    *,
    expected_peer_identity: str,
) -> ConduitRequest:
    """Authorize an already parsed request against an exact peer binding."""

    if not isinstance(request, ConduitRequest):
        raise EnrollmentError("Conduit request required")

    expected = _validate_peer_identity(expected_peer_identity)

    if request.peer_identity != expected:
        raise EnrollmentError("Conduit peer binding mismatch")

    if request.operation not in _ALLOWED_OPERATIONS:
        raise EnrollmentError("Conduit operation not permitted")

    return request
