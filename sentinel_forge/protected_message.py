"""Algorithm-neutral, session-bound protected-message contract.

No encryption implementation is selected here. This defines mandatory pairwise
identity, session, and associated-data bindings for a future authenticated-
encryption mechanism. Unbound sessions are intentionally not representable
through the public construction/validation API.
"""
from __future__ import annotations
from dataclasses import dataclass,asdict
import hashlib,json
from .enrollment import EnrollmentError
from .trust_domain import PairwiseTrustDomain,bind_message_context
from .session import PairwiseSession,require_session

FORMAT="sentinel-protected-message-v1"

@dataclass(frozen=True)
class ProtectedMessageHeader:
 format:str
 relationship_id:str
 forge_identity:str
 peer_identity:str
 peer_role:str
 enrollment_id:str
 session_id:str
 session_generation:int
 permitted_target:str
 operation:str
 artifact_identity:str
 sequence:int
 context_binding:str
 def as_dict(self):return asdict(self)

def build_header(domain:PairwiseTrustDomain,session:PairwiseSession,*,operation:str,
                 artifact_identity:str,sequence:int)->ProtectedMessageHeader:
 require_session(session,domain)
 if not isinstance(operation,str) or not operation.strip():raise EnrollmentError("operation required")
 if not isinstance(artifact_identity,str) or not artifact_identity.strip():raise EnrollmentError("artifact identity required")
 if not isinstance(sequence,int) or isinstance(sequence,bool) or sequence<1:raise EnrollmentError("positive message sequence required")
 context=bind_message_context(domain,operation=operation,artifact_identity=artifact_identity,sequence=sequence)
 return ProtectedMessageHeader(FORMAT,domain.relationship_id,domain.forge_identity,domain.peer_identity,
  domain.peer_role,domain.enrollment_id,session.session_id,session.generation,domain.permitted_target,
  operation,artifact_identity,sequence,context)

def associated_data(header:ProtectedMessageHeader)->bytes:
 return _canonical(header.as_dict())

def validate_header(header:ProtectedMessageHeader,domain:PairwiseTrustDomain,session:PairwiseSession,*,
                    expected_operation:str,expected_artifact_identity:str,expected_sequence:int)->None:
 expected=build_header(domain,session,operation=expected_operation,
                       artifact_identity=expected_artifact_identity,sequence=expected_sequence)
 if header!=expected:raise EnrollmentError("protected message trust-domain/session/header binding mismatch")

def require_transport_ready_header(header:ProtectedMessageHeader,domain:PairwiseTrustDomain,
                                   session:PairwiseSession,*,expected_operation:str,
                                   expected_artifact_identity:str,expected_sequence:int)->None:
 """Fail-closed gate for any future protected transport implementation."""
 validate_header(header,domain,session,expected_operation=expected_operation,
                 expected_artifact_identity=expected_artifact_identity,expected_sequence=expected_sequence)
 if header.session_generation<1 or not header.session_id.startswith("session:"):
  raise EnrollmentError("protected transport requires bound pairwise session")

def associated_data_digest(header:ProtectedMessageHeader)->str:
 return "sha256:"+hashlib.sha256(associated_data(header)).hexdigest()

def _canonical(v):return (json.dumps(v,sort_keys=True,separators=(",",":"))+"\n").encode()
