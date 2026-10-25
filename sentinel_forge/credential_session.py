"""Algorithm-neutral credential-generation binding for pairwise sessions."""
from __future__ import annotations
from dataclasses import dataclass,asdict
import hashlib,json
from .credential_reference import RelationshipCredentialReference,verify_credential_reference
from .enrollment import EnrollmentError
from .session import PairwiseSession,require_session
from .trust_domain import PairwiseTrustDomain

FORMAT="sentinel-credential-bound-session-v1"

@dataclass(frozen=True)
class CredentialBoundSession:
 format:str
 session_id:str
 relationship_id:str
 peer_identity:str
 session_generation:int
 credential_generation:int
 key_reference:str
 binding_digest:str
 def as_dict(self):return asdict(self)

def bind_session_credential(session:PairwiseSession,domain:PairwiseTrustDomain,
                            credential:RelationshipCredentialReference)->CredentialBoundSession:
 require_session(session,domain)
 if not verify_credential_reference(credential,domain):
  raise EnrollmentError("credential reference is not bound to session relationship")
 if session.generation!=credential.generation:
  raise EnrollmentError("session generation must equal credential generation")
 core={"format":FORMAT,"session_id":session.session_id,"relationship_id":domain.relationship_id,
       "peer_identity":domain.peer_identity,"session_generation":session.generation,
       "credential_generation":credential.generation,"key_reference":credential.key_reference}
 return CredentialBoundSession(**core,binding_digest="sha256:"+_sha(core))

def verify_session_credential(binding:CredentialBoundSession,session:PairwiseSession,
                              domain:PairwiseTrustDomain,
                              credential:RelationshipCredentialReference)->bool:
 try:return bind_session_credential(session,domain,credential)==binding
 except EnrollmentError:return False

def require_current_credential_session(binding:CredentialBoundSession,session:PairwiseSession,
                                       domain:PairwiseTrustDomain,
                                       credential:RelationshipCredentialReference)->None:
 if not verify_session_credential(binding,session,domain,credential):
  raise EnrollmentError("session is not bound to current relationship credential generation")

def _canonical(v):return (json.dumps(v,sort_keys=True,separators=(",",":"))+"\n").encode()
def _sha(v):return hashlib.sha256(_canonical(v)).hexdigest()

def require_credential_ready_session(binding:CredentialBoundSession,session:PairwiseSession,
                                     domain:PairwiseTrustDomain,
                                     credential:RelationshipCredentialReference)->None:
 """Fail-closed prerequisite for any future protected transport."""
 require_current_credential_session(binding,session,domain,credential)
 if credential.generation<1 or binding.credential_generation!=session.generation:
  raise EnrollmentError("protected transport requires current pairwise credential generation")
 if not credential.key_reference.strip():
  raise EnrollmentError("protected transport requires explicit credential reference")

def require_registry_current_credential_session(binding:CredentialBoundSession,session:PairwiseSession,
                                                domain:PairwiseTrustDomain,credential,
                                                registry)->None:
 """Future transport gate requiring durable current-credential authority."""
 registry.require_current(domain,credential)
 require_credential_ready_session(binding,session,domain,credential)
