"""Target-bound child Courier bootstrap specification; performs no network effect."""
from __future__ import annotations
from dataclasses import dataclass,asdict
import hashlib,json
from .enrollment import EnrollmentError

FORMAT="sentinel-courier-child-bootstrap-v1"
@dataclass(frozen=True)
class ChildBootstrap:
 format:str;child_identity:str;endpoint:str;enrollment_id:str;challenge_id:str;artifact_digest:str;notification:str
 def as_dict(self):return asdict(self)

def build_child_bootstrap(*,child_identity,endpoint,enrollment_id,challenge_id,artifact_digest):
 vals=(child_identity,endpoint,enrollment_id,challenge_id,artifact_digest)
 if any(not isinstance(x,str) or not x.strip() for x in vals):raise EnrollmentError("child bootstrap fields required")
 if not artifact_digest.startswith("sha256:"):raise EnrollmentError("bootstrap artifact digest required")
 return ChildBootstrap(FORMAT,child_identity,endpoint,enrollment_id,challenge_id,artifact_digest,"Sentinel Courier connected to Forge.")

def bootstrap_digest(b):
 if not isinstance(b,ChildBootstrap):raise EnrollmentError("child bootstrap required")
 raw=json.dumps(b.as_dict(),sort_keys=True,separators=(",",":")).encode()
 return "sha256:"+hashlib.sha256(raw).hexdigest()
