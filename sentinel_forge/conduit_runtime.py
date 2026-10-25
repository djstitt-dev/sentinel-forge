"""Standalone fail-closed Sentinel Conduit command runtime.

This module intentionally depends only on the Python standard library.
It is suitable for extraction into a minimal remote Conduit runtime.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
import shlex


_ALLOWED_OPERATIONS = frozenset({
    "status",
    "capabilities",
})

_PEER_IDENTITY_RE = re.compile(
    r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
)

_MAX_PEER_IDENTITY_LENGTH = 128


class ConduitError(RuntimeError):
    """Raised when a Conduit request fails validation or authorization."""


@dataclass(frozen=True)
class ConduitRequest:
    operation: str
    peer_identity: str


def _validate_peer_identity(peer_identity: str) -> str:
    if not isinstance(peer_identity, str) or not peer_identity:
        raise ConduitError("Conduit peer identity required")

    if len(peer_identity) > _MAX_PEER_IDENTITY_LENGTH:
        raise ConduitError("Conduit peer identity too long")

    if _PEER_IDENTITY_RE.fullmatch(peer_identity) is None:
        raise ConduitError(
            "Conduit peer identity is not canonical"
        )

    return peer_identity


def parse_forced_command(
    original_command: str,
) -> ConduitRequest:
    """Parse one exact canonical Conduit command.

    Accepted form:

        sentinel-conduit <operation> --peer <peer-identity>

    Shell syntax, quoting, alternate whitespace, extra arguments,
    alternate executable paths, and unknown operations fail closed.
    """

    if (
        not isinstance(original_command, str)
        or not original_command.strip()
    ):
        raise ConduitError(
            "Conduit original command required"
        )

    try:
        argv = shlex.split(
            original_command,
            posix=True,
        )
    except ValueError as exc:
        raise ConduitError(
            "Conduit command parsing failed"
        ) from exc

    if len(argv) != 4:
        raise ConduitError(
            "Conduit command shape invalid"
        )

    (
        executable,
        operation,
        peer_flag,
        peer_identity,
    ) = argv

    if executable != "sentinel-conduit":
        raise ConduitError(
            "Conduit command executable invalid"
        )

    if operation not in _ALLOWED_OPERATIONS:
        raise ConduitError(
            "Conduit operation not permitted"
        )

    if peer_flag != "--peer":
        raise ConduitError(
            "Conduit peer binding required"
        )

    _validate_peer_identity(peer_identity)

    canonical = (
        f"sentinel-conduit {operation} "
        f"--peer {peer_identity}"
    )

    if original_command != canonical:
        raise ConduitError(
            "Conduit command is not canonical"
        )

    return ConduitRequest(
        operation=operation,
        peer_identity=peer_identity,
    )


def authorize_request(
    request: ConduitRequest,
    *,
    expected_peer_identity: str,
) -> ConduitRequest:
    """Authorize a parsed request against one exact peer."""

    if not isinstance(request, ConduitRequest):
        raise ConduitError(
            "Conduit request required"
        )

    expected = _validate_peer_identity(
        expected_peer_identity
    )

    _validate_peer_identity(
        request.peer_identity
    )

    if request.peer_identity != expected:
        raise ConduitError(
            "Conduit peer binding mismatch"
        )

    if request.operation not in _ALLOWED_OPERATIONS:
        raise ConduitError(
            "Conduit operation not permitted"
        )

    return request
