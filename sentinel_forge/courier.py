"""Disconnected Courier authority model for repository-only validation.

This is an in-memory reference implementation. It performs no I/O transport and
creates no Scribe or deployment authority.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping

from .contract import ContractBundle

class CourierError(ValueError): pass
class ConflictingReplay(CourierError): pass
class CourierRejected(CourierError): pass

@dataclass(frozen=True)
class CourierReceipt:
    receipt: dict[str, Any]
    request_fingerprint: str
    replayed: bool = False

@dataclass
class _Record:
    fingerprint: str
    receipt: dict[str, Any]

class DisconnectedCourier:
    """Single-process reference authority with exact-replay semantics."""

    def __init__(self, courier_identity: str = "courier-reference"):
        if not courier_identity:
            raise CourierError("courier identity is required")
        self._identity = courier_identity
        self._records: dict[str, _Record] = {}

    def submit(self, objects: Mapping[str, Mapping[str, Any]]) -> CourierReceipt:
        # Validate the Forge proposal as a whole before Courier independently
        # considers its own effect.
        result = ContractBundle(objects).validate()
        if not result.accepted:
            raise CourierRejected("proposal fails governing logical validation")

        request = dict(objects["TransferRequest"])
        correlation = request["correlation_identity"]
        fingerprint = _fingerprint(request)

        prior = self._records.get(correlation)
        if prior is not None:
            if prior.fingerprint != fingerprint:
                raise ConflictingReplay("correlation identity reused for a different request")
            return CourierReceipt(dict(prior.receipt), fingerprint, replayed=True)

        # The disconnected reference implementation can validate and record
        # custody semantics, but cannot truthfully claim a real destination
        # transfer. Therefore its authoritative outcome remains PROPOSED.
        receipt = {
            "courier_identity": self._identity,
            "source_identity": request["source_identity"],
            "destination": request["destination"],
            "transfer_operation": request["transfer_operation"],
            "work_package_revision": request["work_package_revision"],
            "authorization_reference": request["authorization_reference"],
            "artifact_identity": request["artifact_identity"],
            "correlation_identity": correlation,
            "policy_classification": request["classification_handling"],
            "transfer_disposition": "PROPOSED",
            "validation_outcome": "PASS_OFFLINE_ONLY",
            "completeness_state": "COMPLETE",
            "retry_reconciliation_state": request["prior_attempt_reconciliation_state"],
            "provenance": "DISCONNECTED_REFERENCE_COURIER",
        }
        self._records[correlation] = _Record(fingerprint, dict(receipt))
        return CourierReceipt(receipt, fingerprint)

    def lookup(self, correlation_identity: str) -> CourierReceipt | None:
        prior = self._records.get(correlation_identity)
        if prior is None:
            return None
        return CourierReceipt(dict(prior.receipt), prior.fingerprint, replayed=True)

def _fingerprint(request: Mapping[str, Any]) -> str:
    payload = (json.dumps(dict(request), sort_keys=True, separators=(",", ":")) + "\n").encode()
    return "sha256:" + hashlib.sha256(payload).hexdigest()
