"""Fail-closed production transport readiness assessment."""
from dataclasses import dataclass
from .enrollment import EnrollmentError

@dataclass(frozen=True)
class TransportReadiness:
 ready:bool
 blockers:tuple[str,...]

def assess_transport_readiness(*,enrollment_state:str,revoked:bool,current_credential:bool,
                               current_session:bool,unresolved_effect:bool,unresolved_recovery:bool,
                               audit_available:bool,assistant_independence_verified:bool,
                               protection_provider_approved:bool,network_provider_approved:bool)->TransportReadiness:
 flags=(revoked,current_credential,current_session,unresolved_effect,unresolved_recovery,audit_available,
        assistant_independence_verified,protection_provider_approved,network_provider_approved)
 if not isinstance(enrollment_state,str) or not enrollment_state.strip():raise EnrollmentError("transport readiness enrollment state required")
 if any(not isinstance(x,bool) for x in flags):raise EnrollmentError("transport readiness flags must be boolean")
 blockers=[]
 if enrollment_state!="ACTIVE":blockers.append("ENROLLMENT_NOT_ACTIVE")
 if revoked:blockers.append("RELATIONSHIP_REVOKED")
 if not current_credential:blockers.append("CREDENTIAL_NOT_CURRENT")
 if not current_session:blockers.append("SESSION_NOT_CURRENT")
 if unresolved_effect:blockers.append("UNRESOLVED_EFFECT")
 if unresolved_recovery:blockers.append("UNRESOLVED_RECOVERY")
 if not audit_available:blockers.append("AUDIT_UNAVAILABLE")
 if not assistant_independence_verified:blockers.append("ASSISTANT_INDEPENDENCE_UNVERIFIED")
 if not protection_provider_approved:blockers.append("PROTECTION_PROVIDER_UNAPPROVED")
 if not network_provider_approved:blockers.append("NETWORK_PROVIDER_UNAPPROVED")
 return TransportReadiness(not blockers,tuple(blockers))

def require_transport_ready(readiness:TransportReadiness)->None:
 if not readiness.ready:raise EnrollmentError("transport not ready: "+",".join(readiness.blockers))
