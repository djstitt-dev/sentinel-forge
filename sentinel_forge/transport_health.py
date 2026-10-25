"""Evidence-based Courier transport health classification."""
from dataclasses import dataclass

@dataclass(frozen=True)
class TransportHealth:
 status:str
 reasons:tuple[str,...]

def assess_transport_health(*,relationship_active:bool,revoked:bool,current_credential:bool,current_session:bool,
                            queue_consistent:bool,audit_available:bool,unresolved_effect:bool,
                            provider_available:bool,last_probe_known:bool)->TransportHealth:
 reasons=[]
 if revoked:reasons.append("RELATIONSHIP_REVOKED")
 if not relationship_active:reasons.append("RELATIONSHIP_INACTIVE")
 if not current_credential:reasons.append("CREDENTIAL_NOT_CURRENT")
 if not current_session:reasons.append("SESSION_NOT_CURRENT")
 if not queue_consistent:reasons.append("DURABLE_STATE_INCONSISTENT")
 if not audit_available:reasons.append("AUDIT_UNAVAILABLE")
 if unresolved_effect:reasons.append("UNRESOLVED_EFFECT")
 blockers=tuple(reasons)
 if blockers:return TransportHealth("BLOCKED",blockers)
 if not provider_available:return TransportHealth("DEGRADED",("PROVIDER_UNAVAILABLE",))
 if not last_probe_known:return TransportHealth("UNKNOWN",("NO_CURRENT_OBSERVATION",))
 return TransportHealth("HEALTHY",())
