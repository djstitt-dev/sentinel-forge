"""Pairwise session identity and fail-closed anti-replay state."""

from __future__ import annotations
from .secure_io import private_open
from dataclasses import dataclass,asdict
import fcntl,hashlib,json,os
from pathlib import Path
from .enrollment import EnrollmentError
from .trust_domain import PairwiseTrustDomain

FORMAT="sentinel-pairwise-session-v1"

@dataclass(frozen=True)
class PairwiseSession:
 format:str
 session_id:str
 relationship_id:str
 forge_identity:str
 peer_identity:str
 enrollment_id:str
 generation:int
 challenge_digest:str

 def as_dict(self):return asdict(self)

def derive_session(domain:PairwiseTrustDomain,*,generation:int,challenge:bytes)->PairwiseSession:
 if not isinstance(generation,int) or isinstance(generation,bool) or generation<1:raise EnrollmentError("session generation must be positive")
 if not isinstance(challenge,bytes) or len(challenge)<16:raise EnrollmentError("session challenge must provide at least 128 bits")
 cd="sha256:"+hashlib.sha256(challenge).hexdigest()
 core={"format":FORMAT,"relationship_id":domain.relationship_id,"forge_identity":domain.forge_identity,
       "peer_identity":domain.peer_identity,"enrollment_id":domain.enrollment_id,
       "generation":generation,"challenge_digest":cd}
 sid="session:"+_sha(core)
 return PairwiseSession(FORMAT,sid,domain.relationship_id,domain.forge_identity,domain.peer_identity,
                        domain.enrollment_id,generation,cd)

def require_session(session:PairwiseSession,domain:PairwiseTrustDomain)->None:
 if (session.relationship_id!=domain.relationship_id or session.forge_identity!=domain.forge_identity or
     session.peer_identity!=domain.peer_identity or session.enrollment_id!=domain.enrollment_id):
  raise EnrollmentError("session is not bound to this pairwise trust domain")

class ReplayRegistry:
 """Durable highest-contiguous sequence registry, scoped by relationship/session."""
 def __init__(self,path:Path):
  self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)

 def accept(self,session:PairwiseSession,domain:PairwiseTrustDomain,*,sequence:int)->None:
  require_session(session,domain)
  if not isinstance(sequence,int) or isinstance(sequence,bool) or sequence<1:raise EnrollmentError("message sequence must be positive")
  with self._lock(exclusive=True):
   data=self._read();rel=data.setdefault(domain.relationship_id,{"generation":0,"session_id":None,"highest":0})
   gen=rel["generation"]
   if session.generation<gen:raise EnrollmentError("stale session rejected")
   if session.generation>gen:
    if session.generation!=gen+1:raise EnrollmentError("session generation jump rejected")
    if sequence!=1:raise EnrollmentError("new session must begin at sequence 1")
    rel.update(generation=session.generation,session_id=session.session_id,highest=1);self._write(data);return
   if rel["session_id"]!=session.session_id:raise EnrollmentError("conflicting session identity for generation")
   expected=rel["highest"]+1
   if sequence!=expected:
    if sequence<=rel["highest"]:raise EnrollmentError("replayed or stale message rejected")
    raise EnrollmentError("out-of-order message rejected")
   rel["highest"]=sequence;self._write(data)

 def state(self,relationship_id:str):
  with self._lock(exclusive=False):
   return self._read().get(relationship_id)

 def _lock(self,*,exclusive:bool):
  return _FileLock(self.path.with_suffix(self.path.suffix+".lock"),exclusive)

 def _read(self):
  if not self.path.exists():return {}
  try:v=json.loads(self.path.read_text())
  except Exception as exc:raise EnrollmentError("replay registry unreadable") from exc
  if not isinstance(v,dict):raise EnrollmentError("replay registry malformed")
  for k,r in v.items():
   if not isinstance(k,str) or not isinstance(r,dict) or set(r)!={"generation","session_id","highest"}:
    raise EnrollmentError("replay registry malformed")
   if not isinstance(r["generation"],int) or isinstance(r["generation"],bool) or not isinstance(r["highest"],int) or isinstance(r["highest"],bool) or r["generation"]<0 or r["highest"]<0:raise EnrollmentError("replay registry malformed")
  return v

 def _write(self,data):
  tmp=self.path.with_suffix(self.path.suffix+".tmp")
  raw=json.dumps(data,sort_keys=True,separators=(",",":"))+"\n"
  with private_open(tmp,"w") as f:f.write(raw);f.flush();os.fsync(f.fileno())
  os.replace(tmp,self.path)
  fd=os.open(self.path.parent,os.O_RDONLY)
  try:os.fsync(fd)
  finally:os.close(fd)


class _FileLock:
 def __init__(self,path:Path,exclusive:bool):
  self.path=Path(path);self.exclusive=exclusive;self.fd=None
 def __enter__(self):
  try:
   self.fd=os.open(self.path,os.O_RDWR|os.O_CREAT,0o600)
   fcntl.flock(self.fd,fcntl.LOCK_EX if self.exclusive else fcntl.LOCK_SH)
  except OSError as exc:
   if self.fd is not None:os.close(self.fd);self.fd=None
   raise EnrollmentError("replay registry lock unavailable") from exc
  return self
 def __exit__(self,exc_type,exc,tb):
  try:
   if self.fd is not None:fcntl.flock(self.fd,fcntl.LOCK_UN)
  finally:
   if self.fd is not None:os.close(self.fd);self.fd=None

def _sha(v):return hashlib.sha256((json.dumps(v,sort_keys=True,separators=(",",":"))+"\n").encode()).hexdigest()
