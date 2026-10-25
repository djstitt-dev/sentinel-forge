"""Courier completion model: implementation completion is not production activation."""
from __future__ import annotations
from dataclasses import dataclass,asdict
import json
from .enrollment import EnrollmentError

IMPLEMENTATION_GATES=(
 "FRAMING_IMPLEMENTED",
 "PROTECTION_BOUNDARY_IMPLEMENTED",
 "ENROLLMENT_IMPLEMENTED",
 "PAIRWISE_TRUST_IMPLEMENTED",
 "CREDENTIAL_AUTHORITY_IMPLEMENTED",
 "SESSION_REPLAY_IMPLEMENTED",
 "DELIVERY_INTENT_IMPLEMENTED",
 "DURABLE_QUEUE_IMPLEMENTED",
 "ACK_RECONCILIATION_IMPLEMENTED",
 "REVOCATION_ROTATION_IMPLEMENTED",
 "AUDIT_EVIDENCE_IMPLEMENTED",
 "RECOVERY_IMPLEMENTED",
 "BACKUP_RESTORE_CONTRACT_IMPLEMENTED",
 "CROSS_AUTHORITY_AUDIT_IMPLEMENTED",
 "READINESS_FAIL_CLOSED",
 "FULL_REGRESSION_PASS",
)
ACTIVATION_GATES=(
 "PRODUCTION_PROTECTION_APPROVED",
 "PRODUCTION_NETWORK_APPROVED",
 "PRODUCTION_CREDENTIAL_PROVISIONED",
 "ASSISTANT_INDEPENDENCE_VERIFIED",
 "PEER_ENROLLMENT_ACTIVE",
)
OPERATIONAL_GATES=(
 "LIVE_PROVIDER_AVAILABLE",
 "LIVE_PEER_OBSERVED",
 "LIVE_HEALTHY",
)

@dataclass(frozen=True)
class CourierCompletion:
 implementation_complete:bool
 activation_ready:bool
 operational:bool
 implementation_blockers:tuple[str,...]
 activation_blockers:tuple[str,...]
 operational_blockers:tuple[str,...]
 def as_dict(self):return asdict(self)
 def to_json(self):return json.dumps(self.as_dict(),sort_keys=True,separators=(",",":"))+"\n"

def _exact(name,facts):
 if not isinstance(facts,dict):raise EnrollmentError("Courier completion facts must be mapping")
 missing=set(name)-set(facts);extra=set(facts)-set(name)
 if missing or extra:raise EnrollmentError("Courier completion fact set incomplete")
 for k,v in facts.items():
  if type(v) is not bool:raise EnrollmentError("Courier completion facts must be boolean")
 return tuple(k for k in name if not facts[k])

def assess_completion(*,implementation_facts,activation_facts,operational_facts):
 ib=_exact(IMPLEMENTATION_GATES,implementation_facts)
 ab=_exact(ACTIVATION_GATES,activation_facts)
 ob=_exact(OPERATIONAL_GATES,operational_facts)
 implementation=not ib
 activation=implementation and not ab
 operational=activation and not ob
 if not implementation:ab=("IMPLEMENTATION_INCOMPLETE",)+ab
 if not activation:ob=("ACTIVATION_NOT_READY",)+ob
 return CourierCompletion(implementation,activation,operational,ib,tuple(dict.fromkeys(ab)),tuple(dict.fromkeys(ob)))
