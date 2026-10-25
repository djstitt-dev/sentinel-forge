"""Logical identity distinguishing exact replay from an intentional new delivery."""
from dataclasses import dataclass,asdict
import hashlib,json
from .enrollment import EnrollmentError
FORMAT="sentinel-courier-delivery-intent-v1"
@dataclass(frozen=True)
class DeliveryIntent:
 format:str
 delivery_id:str
 correlation_id:str
 relationship_id:str
 artifact_identity:str
 operation:str
 authorization_reference:str
 intent_digest:str
 def as_dict(self):return asdict(self)
def build_delivery_intent(*,correlation_id,relationship_id,artifact_identity,operation,authorization_reference):
 vals=(correlation_id,relationship_id,artifact_identity,operation,authorization_reference)
 if any(not isinstance(x,str) or not x.strip() for x in vals):raise EnrollmentError("Courier delivery intent field required")
 core={"format":FORMAT,"correlation_id":correlation_id,"relationship_id":relationship_id,
       "artifact_identity":artifact_identity,"operation":operation,"authorization_reference":authorization_reference}
 digest=_sha(core);return DeliveryIntent(FORMAT,"delivery:"+digest,correlation_id,relationship_id,artifact_identity,operation,authorization_reference,"sha256:"+digest)
def verify_delivery_intent(i:DeliveryIntent,**expected):
 core={"format":i.format,"correlation_id":i.correlation_id,"relationship_id":i.relationship_id,
       "artifact_identity":i.artifact_identity,"operation":i.operation,"authorization_reference":i.authorization_reference}
 digest=_sha(core)
 if i.format!=FORMAT or i.delivery_id!="delivery:"+digest or i.intent_digest!="sha256:"+digest:raise EnrollmentError("Courier delivery intent integrity failure")
 for k,v in expected.items():
  if not hasattr(i,k) or getattr(i,k)!=v:raise EnrollmentError(f"Courier delivery intent {k} binding mismatch")
def _sha(v):return hashlib.sha256((json.dumps(v,sort_keys=True,separators=(",",":"))+"\n").encode()).hexdigest()
