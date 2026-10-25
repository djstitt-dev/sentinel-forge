"""Credential-authoritative protected-message transport contract.

This composes existing trust-domain, session, credential-reference, durable
credential-authority, and protected-message metadata. It performs no network or
cryptographic effect and selects no production algorithm.
"""
from __future__ import annotations
from dataclasses import dataclass,asdict
import hashlib,json
from .credential_session import CredentialBoundSession,require_registry_current_credential_session
from .enrollment import EnrollmentError
from .protected_message import ProtectedMessageHeader,build_header,validate_header
from .session import PairwiseSession
from .trust_domain import PairwiseTrustDomain

FORMAT="sentinel-transport-message-context-v1"

@dataclass(frozen=True)
class TransportMessageContext:
 format:str
 relationship_id:str
 session_id:str
 session_generation:int
 credential_generation:int
 key_reference:str
 credential_binding_digest:str
 protected_header_digest:str
 context_digest:str
 def as_dict(self):return asdict(self)

def build_transport_context(domain:PairwiseTrustDomain,session:PairwiseSession,binding:CredentialBoundSession,
                            credential,registry,*,operation:str,artifact_identity:str,
                            sequence:int)->tuple[ProtectedMessageHeader,TransportMessageContext]:
 require_registry_current_credential_session(binding,session,domain,credential,registry)
 header=build_header(domain,session,operation=operation,artifact_identity=artifact_identity,sequence=sequence)
 core={"format":FORMAT,"relationship_id":domain.relationship_id,"session_id":session.session_id,
       "session_generation":session.generation,"credential_generation":credential.generation,
       "key_reference":credential.key_reference,"credential_binding_digest":binding.binding_digest,
       "protected_header_digest":"sha256:"+hashlib.sha256(_canonical(header.as_dict())).hexdigest()}
 return header,TransportMessageContext(**core,context_digest="sha256:"+_sha(core))

def validate_transport_context(header:ProtectedMessageHeader,context:TransportMessageContext,
                               domain:PairwiseTrustDomain,session:PairwiseSession,
                               binding:CredentialBoundSession,credential,registry,*,
                               expected_operation:str,expected_artifact_identity:str,
                               expected_sequence:int)->None:
 require_registry_current_credential_session(binding,session,domain,credential,registry)
 validate_header(header,domain,session,expected_operation=expected_operation,
  expected_artifact_identity=expected_artifact_identity,expected_sequence=expected_sequence)
 expected_header,expected=build_transport_context(domain,session,binding,credential,registry,
  operation=expected_operation,artifact_identity=expected_artifact_identity,sequence=expected_sequence)
 if header!=expected_header or context!=expected:
  raise EnrollmentError("transport message credential/session/context binding mismatch")

def associated_data(context:TransportMessageContext)->bytes:
 return _canonical(context.as_dict())

def _canonical(v):return (json.dumps(v,sort_keys=True,separators=(",",":"))+"\n").encode()
def _sha(v):return hashlib.sha256(_canonical(v)).hexdigest()

def accept_transport_message(header:ProtectedMessageHeader,context:TransportMessageContext,
                             domain:PairwiseTrustDomain,session:PairwiseSession,
                             binding:CredentialBoundSession,credential,credential_registry,
                             replay_registry,*,expected_operation:str,
                             expected_artifact_identity:str,expected_sequence:int)->None:
 """Validate all metadata authority before consuming the anti-replay sequence."""
 validate_transport_context(header,context,domain,session,binding,credential,credential_registry,
  expected_operation=expected_operation,expected_artifact_identity=expected_artifact_identity,
  expected_sequence=expected_sequence)
 replay_registry.accept(session,domain,sequence=expected_sequence)
