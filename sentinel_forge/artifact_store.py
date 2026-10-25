"""Bounded local staging, acceptance, and quarantine stores."""
from __future__ import annotations
from .secure_io import private_open
import hashlib,json,os
from pathlib import Path
from .enrollment import EnrollmentError

MAX_ARTIFACT=16*1024*1024

class ArtifactStore:
 def __init__(self,root:Path):
  self.root=Path(root)
  for n in ("staging","accepted","quarantine"):self._dir(n).mkdir(parents=True,exist_ok=True)

 def stage(self,payload:bytes,*,expected_identity:str)->str:
  identity=_identity(payload)
  if identity!=expected_identity:raise EnrollmentError("staged artifact identity mismatch")
  name=identity.split(":",1)[1];dest=self._dir("staging")/name
  if dest.exists():
   if _identity(dest.read_bytes())!=identity:raise EnrollmentError("staging identity collision")
   return identity
  _atomic_write(dest,payload);return identity

 def accept(self,identity:str)->Path:
  src=self._path("staging",identity);dst=self._path("accepted",identity)
  if dst.exists():
   if _identity(dst.read_bytes())!=identity:raise EnrollmentError("accepted artifact identity collision")
   if src.exists():raise EnrollmentError("artifact exists in both staging and accepted")
   return dst
  if not src.exists():raise EnrollmentError("staged artifact missing")
  if _identity(src.read_bytes())!=identity:raise EnrollmentError("staged artifact corrupted")
  os.replace(src,dst);_fsync_dir(dst.parent);return dst
 def quarantine(self,identity:str,*,reason:str)->Path:
  if not isinstance(reason,str) or not reason.strip():raise EnrollmentError("quarantine reason required")
  src=self._path("staging",identity);dst=self._path("quarantine",identity)
  if not src.exists():raise EnrollmentError("staged artifact missing")
  if _identity(src.read_bytes())!=identity:raise EnrollmentError("staged artifact corrupted")
  os.replace(src,dst);_fsync_dir(dst.parent)
  _atomic_write(dst.with_suffix(".reason.json"),(json.dumps({"identity":identity,"reason":reason},sort_keys=True)+"\n").encode())
  return dst

 def _path(self,kind,identity):
  if not isinstance(identity,str) or not identity.startswith("sha256:") or len(identity)!=71:raise EnrollmentError("artifact identity invalid")
  return self._dir(kind)/identity.split(":",1)[1]
 def _dir(self,n):return self.root/n

def _identity(payload):
 if not isinstance(payload,bytes) or not payload or len(payload)>MAX_ARTIFACT:raise EnrollmentError("artifact payload bound invalid")
 return "sha256:"+hashlib.sha256(payload).hexdigest()
def _atomic_write(path,payload):
 tmp=path.with_suffix(".tmp")
 with private_open(tmp,"xb") as f:f.write(payload);f.flush();os.fsync(f.fileno())
 os.replace(tmp,path);_fsync_dir(path.parent)
def _fsync_dir(path):
 fd=os.open(path,os.O_RDONLY)
 try:os.fsync(fd)
 finally:os.close(fd)
