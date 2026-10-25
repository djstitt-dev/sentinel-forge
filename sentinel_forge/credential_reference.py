"""Algorithm-neutral pairwise credential-reference policy.

References identify externally managed relationship credentials. No secret,
private key, cipher, signature, handshake, or production crypto algorithm is
selected or stored here.
"""

from __future__ import annotations
from dataclasses import dataclass,asdict
import hashlib,json
from .enrollment import EnrollmentError
from .trust_domain import PairwiseTrustDomain

FORMAT="sentinel-pairwise-credential-reference-v1"

@dataclass(frozen=True)
class RelationshipCredentialReference:
 format:str
 relationship_id:str
 forge_identity:str
 peer_identity:str
 enrollment_id:str
 generation:int
 key_reference:str
 reference_digest:str

 def as_dict(self):return asdict(self)

def build_credential_reference(domain:PairwiseTrustDomain,*,generation:int,key_reference:str)->RelationshipCredentialReference:
 if not isinstance(generation,int) or isinstance(generation,bool) or generation<1:
  raise EnrollmentError("credential generation must be positive")
 if not isinstance(key_reference,str) or not key_reference.strip():
  raise EnrollmentError("credential key reference must be explicit")
 core={"format":FORMAT,"relationship_id":domain.relationship_id,"forge_identity":domain.forge_identity,
       "peer_identity":domain.peer_identity,"enrollment_id":domain.enrollment_id,
       "generation":generation,"key_reference":key_reference}
 digest="sha256:"+_sha(core)
 return RelationshipCredentialReference(**core,reference_digest=digest)

def verify_credential_reference(reference:RelationshipCredentialReference,domain:PairwiseTrustDomain)->bool:
 try:return build_credential_reference(domain,generation=reference.generation,key_reference=reference.key_reference)==reference
 except EnrollmentError:return False

def validate_pairwise_credential_set(references:list[RelationshipCredentialReference],
                                     domains:list[PairwiseTrustDomain])->None:
 if not references or len(references)!=len(domains):
  raise EnrollmentError("credential set must cover each pairwise relationship exactly once")
 by_relationship={}
 key_owners={}
 for domain in domains:
  if domain.relationship_id in by_relationship:
   raise EnrollmentError("duplicate pairwise trust domain")
  by_relationship[domain.relationship_id]=domain
 seen=set()
 for reference in references:
  domain=by_relationship.get(reference.relationship_id)
  if domain is None or not verify_credential_reference(reference,domain):
   raise EnrollmentError("credential reference is not bound to declared relationship")
  if reference.relationship_id in seen:
   raise EnrollmentError("duplicate credential reference for relationship")
  seen.add(reference.relationship_id)
  owner=key_owners.setdefault(reference.key_reference,reference.relationship_id)
  if owner!=reference.relationship_id:
   raise EnrollmentError("fleet-wide credential reuse across pairwise relationships is prohibited")
 if seen!=set(by_relationship):
  raise EnrollmentError("credential set missing pairwise relationship")

def require_rotation(previous:RelationshipCredentialReference,current:RelationshipCredentialReference,
                     domain:PairwiseTrustDomain)->None:
 if not verify_credential_reference(previous,domain) or not verify_credential_reference(current,domain):
  raise EnrollmentError("credential rotation references must belong to the same relationship")
 if current.generation!=previous.generation+1:
  raise EnrollmentError("credential rotation generation must advance exactly once")
 if current.key_reference==previous.key_reference:
  raise EnrollmentError("credential rotation must use a new key reference")

def _canonical(v):return (json.dumps(v,sort_keys=True,separators=(",",":"))+"\n").encode()
def _sha(v):return hashlib.sha256(_canonical(v)).hexdigest()
