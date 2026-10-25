"""Last-moment Courier authority and binding revalidation."""
from dataclasses import dataclass
from .credential_session import require_credential_ready_session
from .enrollment import EnrollmentError
from .transport_readiness import assess_transport_readiness,require_transport_ready

@dataclass(frozen=True)
class EffectAuthorization:
 item_id:str
 relationship_id:str
 sequence:int
 artifact_identity:str
 operation:str
 target:str
 classification:str

def authorize_effect(*,prepared,queue,domain,session,binding,credential,credential_registry,
                     enrollment_state:str,revoked:bool,unresolved_effect:bool,unresolved_recovery:bool,
                     audit_available:bool,assistant_independence_verified:bool,
                     protection_provider_approved:bool,network_provider_approved:bool,
                     expected_target:str,actual_target:str,expected_classification:str,actual_classification:str)->EffectAuthorization:
 r=queue.get(prepared.item_id)
 if r is None or r["state"]!="PREPARED":raise EnrollmentError("Courier delivery not PREPARED")
 if r["relationship_id"]!=domain.relationship_id or prepared.relationship_id!=domain.relationship_id:
  raise EnrollmentError("Courier relationship changed before effect")
 if r["artifact_identity"]!=prepared.artifact_identity or r["operation"]!=prepared.operation or r["sequence"]!=prepared.sequence:
  raise EnrollmentError("Courier prepared delivery binding changed")
 if expected_target!=actual_target or actual_target!=domain.permitted_target:
  raise EnrollmentError("Courier target binding changed")
 if expected_classification!=actual_classification:raise EnrollmentError("Courier classification binding changed")
 require_credential_ready_session(binding,session,domain,credential)
 credential_registry.require_current(domain,credential)
 readiness=assess_transport_readiness(enrollment_state=enrollment_state,revoked=revoked,current_credential=True,
  current_session=True,unresolved_effect=unresolved_effect,unresolved_recovery=unresolved_recovery,
  audit_available=audit_available,assistant_independence_verified=assistant_independence_verified,
  protection_provider_approved=protection_provider_approved,network_provider_approved=network_provider_approved)
 require_transport_ready(readiness)
 return EffectAuthorization(prepared.item_id,domain.relationship_id,prepared.sequence,prepared.artifact_identity,
                            prepared.operation,actual_target,actual_classification)
