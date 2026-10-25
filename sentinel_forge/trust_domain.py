"""Algorithm-neutral pairwise trust-domain bindings.

This module defines identity and relationship isolation only. It deliberately
does not choose keys, ciphers, handshakes, credentials, or network transport.
"""

from __future__ import annotations
from dataclasses import dataclass,asdict
import hashlib,json
from .enrollment import EnrollmentBundle,EnrollmentError,verify_bundle

FORMAT="sentinel-pairwise-trust-domain-v1"

@dataclass(frozen=True)
class PairwiseTrustDomain:
 format:str
 relationship_id:str
 forge_identity:str
 peer_identity:str
 peer_role:str
 enrollment_id:str
 permitted_target:str
 policy_reference:str
 context_digest:str

 def as_dict(self):return asdict(self)

def derive_trust_domain(bundle:EnrollmentBundle)->PairwiseTrustDomain:
 if not verify_bundle(bundle):raise EnrollmentError("invalid enrollment cannot define trust domain")
 core={"format":FORMAT,"forge_identity":bundle.forge_identity,"peer_identity":bundle.remote_identity,
       "peer_role":bundle.remote_role,"enrollment_id":bundle.enrollment_id,
       "permitted_target":bundle.permitted_target,"policy_reference":bundle.policy_reference}
 rid="relationship:"+_sha(core)
 digest="sha256:"+_sha({**core,"relationship_id":rid})
 return PairwiseTrustDomain(FORMAT,rid,bundle.forge_identity,bundle.remote_identity,bundle.remote_role,
  bundle.enrollment_id,bundle.permitted_target,bundle.policy_reference,digest)

def verify_trust_domain(domain:PairwiseTrustDomain,bundle:EnrollmentBundle)->bool:
 try:return derive_trust_domain(bundle)==domain
 except EnrollmentError:return False

def require_relationship(domain:PairwiseTrustDomain,*,forge_identity:str,peer_identity:str,
                         peer_role:str,enrollment_id:str,permitted_target:str)->None:
 expected=(forge_identity,peer_identity,peer_role,enrollment_id,permitted_target)
 actual=(domain.forge_identity,domain.peer_identity,domain.peer_role,domain.enrollment_id,domain.permitted_target)
 if actual!=expected:raise EnrollmentError("pairwise trust-domain identity/binding mismatch")

def bind_message_context(domain:PairwiseTrustDomain,*,operation:str,artifact_identity:str,
                         sequence:int)->str:
 if not operation or not artifact_identity or not isinstance(sequence,int) or sequence<1:
  raise EnrollmentError("message context requires operation, artifact identity, and positive sequence")
 body={"format":FORMAT,"relationship_id":domain.relationship_id,"context_digest":domain.context_digest,
       "forge_identity":domain.forge_identity,"peer_identity":domain.peer_identity,
       "peer_role":domain.peer_role,"enrollment_id":domain.enrollment_id,
       "permitted_target":domain.permitted_target,"operation":operation,
       "artifact_identity":artifact_identity,"sequence":sequence}
 return "context:"+_sha(body)

def _canonical(v):return (json.dumps(v,sort_keys=True,separators=(",",":"))+"\n").encode()
def _sha(v):return hashlib.sha256(_canonical(v)).hexdigest()
