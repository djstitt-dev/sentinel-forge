"""Evidence-emitting wrapper for the durable effect coordinator."""

from __future__ import annotations
from typing import Mapping, Any
from .courier_effects import DurableEffectCoordinator, ReconciliationRequired
from .evidence import EvidenceJournal
from .transport import Transport, TransportOutcome

class AuditedEffectCoordinator:
    def __init__(self, coordinator: DurableEffectCoordinator, journal: EvidenceJournal):
        self.coordinator=coordinator; self.journal=journal

    def execute(self, objects: Mapping[str,Mapping[str,Any]], transport: Transport) -> TransportOutcome:
        req=objects["TransferRequest"]
        base=dict(correlation_id=req["correlation_identity"],actor=req["source_identity"],
          target=req["destination"],authorization_reference=req["authorization_reference"],
          input_identity=req["artifact_identity"],source_context="courier-effect-coordinator",
          collector_method="local-reference",timestamp=None,time_uncertainty="UNKNOWN")
        self.journal.append(**base,output_identity=None,outcome="ATTEMPT_REQUESTED",reason="effect coordinator invoked")
        try:
            out=self.coordinator.execute(objects,transport)
        except ReconciliationRequired as exc:
            self.journal.append(**base,output_identity=None,outcome="OUTCOME_UNKNOWN",reason=str(exc))
            raise
        self.journal.append(**base,output_identity=out.acknowledgement,
                            outcome=out.state,reason="durable effect outcome")
        return out

    def reconcile(self, correlation_id: str, *, established_state: str, acknowledgement: str|None=None):
        before=self.coordinator.state(correlation_id)
        self.coordinator.reconcile(correlation_id,established_state=established_state,acknowledgement=acknowledgement)
        self.journal.append(correlation_id=correlation_id,actor="operator-reconciliation",
          target="courier-effect-state",authorization_reference=None,input_identity=None,
          output_identity=acknowledgement,outcome=established_state,
          reason=f"explicit reconciliation from {before.state if before else 'UNKNOWN'}",
          source_context="courier-effect-coordinator",collector_method="local-reference",
          timestamp=None,time_uncertainty="UNKNOWN")
