"""Machine-readable Courier security acceptance assessment."""
from dataclasses import dataclass,asdict
import json

@dataclass(frozen=True)
class CourierAcceptanceReport:
 offline_invariants_passed:bool
 production_ready:bool
 passed:tuple[str,...]
 blockers:tuple[str,...]
 def as_dict(self):return asdict(self)
 def to_json(self):return json.dumps(self.as_dict(),sort_keys=True,separators=(",",":"))+"\n"

REQUIRED_OFFLINE=(
 "PAIRWISE_ISOLATION","DURABLE_SEQUENCE","CURRENT_CREDENTIAL_SESSION","QUEUE_STATE_MACHINE",
 "ACK_BINDING","ANTI_REPLAY","UNKNOWN_EFFECT_RECONCILIATION","LAST_MOMENT_AUTHORITY",
 "REVOCATION_KILL","TARGET_CLASSIFICATION_BINDING","DELIVERY_HISTORY","STAGING_QUARANTINE",
 "DURABLE_FAILURE_FAIL_CLOSED",
)

def assess_courier_acceptance(*,checks:dict[str,bool],framing_complete:bool,protection_provider_complete:bool,
                              production_protection_approved:bool,production_network_approved:bool,
                              assistant_independence_verified:bool)->CourierAcceptanceReport:
 passed=tuple(x for x in REQUIRED_OFFLINE if checks.get(x) is True)
 blockers=[f"OFFLINE_INVARIANT_FAILED:{x}" for x in REQUIRED_OFFLINE if checks.get(x) is not True]
 if not framing_complete:blockers.append("WP6.36_FRAMING_INCOMPLETE")
 if not protection_provider_complete:blockers.append("WP6.37_PROTECTION_PROVIDER_INCOMPLETE")
 if not production_protection_approved:blockers.append("PRODUCTION_PROTECTION_UNAPPROVED")
 if not production_network_approved:blockers.append("PRODUCTION_NETWORK_UNAPPROVED")
 if not assistant_independence_verified:blockers.append("ASSISTANT_INDEPENDENCE_UNVERIFIED")
 offline=all(checks.get(x) is True for x in REQUIRED_OFFLINE)
 return CourierAcceptanceReport(offline,offline and not blockers,passed,tuple(blockers))
