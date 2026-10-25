"""Canonical logical Courier artifact manifest."""
from dataclasses import dataclass,asdict
import hashlib,json
from .enrollment import EnrollmentError

FORMAT="sentinel-courier-manifest-v1"
@dataclass(frozen=True)
class CourierManifest:
 format:str
 relationship_id:str
 sender_identity:str
 recipient_identity:str
 operation:str
 classification:str
 artifact_identity:str
 payload_identity:str
 policy_reference:str
 manifest_digest:str
 def as_dict(self):return asdict(self)

def build_manifest(*,relationship_id,sender_identity,recipient_identity,operation,classification,
                   artifact_identity,payload_identity,policy_reference):
 values=locals()
 for k,v in values.items():
  if not isinstance(v,str) or not v.strip():raise EnrollmentError(f"Courier manifest {k} required")
 core={"format":FORMAT,**values}
 return CourierManifest(**core,manifest_digest="sha256:"+_sha(core))

def verify_manifest(m:CourierManifest,**expected):
 core=asdict(m);digest=core.pop("manifest_digest")
 if m.format!=FORMAT or digest!="sha256:"+_sha(core):raise EnrollmentError("Courier manifest integrity failure")
 for k,v in expected.items():
  if not hasattr(m,k) or getattr(m,k)!=v:raise EnrollmentError(f"Courier manifest {k} binding mismatch")
def _sha(v):return hashlib.sha256((json.dumps(v,sort_keys=True,separators=(",",":"))+"\n").encode()).hexdigest()
