"""Explicit Courier peer-role compatibility policy."""
from dataclasses import dataclass
from .capability import NegotiatedCapabilities
from .enrollment import EnrollmentError

@dataclass(frozen=True)
class CompatibilityRule:
 peer_role:str
 min_protocol:int
 max_protocol:int
 min_schema:int
 max_schema:int
 required_features:tuple[str,...]

DEFAULT_RULES=(
 CompatibilityRule("reaper",1,1,1,1,("ack","anti-replay")),
 CompatibilityRule("scribe",1,1,1,1,("ack","anti-replay")),
 CompatibilityRule("watchtower",1,1,1,1,("ack","anti-replay")),
)

def rule_for(role:str,rules=DEFAULT_RULES)->CompatibilityRule:
 found=[r for r in rules if r.peer_role==role]
 if len(found)!=1:raise EnrollmentError("Courier peer role has no unique compatibility rule")
 return found[0]

def require_compatible(role:str,negotiated:NegotiatedCapabilities,rules=DEFAULT_RULES)->None:
 if not isinstance(negotiated,NegotiatedCapabilities):raise EnrollmentError("negotiated capabilities invalid")
 if not isinstance(negotiated.peer_identity,str) or not negotiated.peer_identity.strip():raise EnrollmentError("negotiated peer invalid")
 if any(not isinstance(x,int) or isinstance(x,bool) or x<1 for x in (negotiated.protocol_version,negotiated.schema_version)):raise EnrollmentError("negotiated version invalid")
 if any(not isinstance(x,str) or not x.strip() for x in negotiated.features):raise EnrollmentError("negotiated feature invalid")
 r=rule_for(role,rules)
 if not r.min_protocol<=negotiated.protocol_version<=r.max_protocol:raise EnrollmentError("negotiated protocol outside compatibility policy")
 if not r.min_schema<=negotiated.schema_version<=r.max_schema:raise EnrollmentError("negotiated schema outside compatibility policy")
 if not set(r.required_features)<=set(negotiated.features):raise EnrollmentError("negotiated features outside compatibility policy")
