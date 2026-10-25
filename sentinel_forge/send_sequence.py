"""Durable monotonic outbound sequence authority."""
from __future__ import annotations
from .secure_io import private_open
import fcntl,json,os
from pathlib import Path
from .enrollment import EnrollmentError
from .session import PairwiseSession
from .trust_domain import PairwiseTrustDomain
from .session import require_session

class SendSequenceRegistry:
 def __init__(self,path:Path):
  self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
  with self._lock(True):
   if not self.path.exists():self._write({})
   self._load()

 def reserve(self,session:PairwiseSession,domain:PairwiseTrustDomain)->int:
  require_session(session,domain)
  with self._lock(True):
   db=self._load();r=db.get(domain.relationship_id);seq=self._reserve_locked(db,r,session,domain)
   self._write(db);return seq

 def reserve_for_item(self,session:PairwiseSession,domain:PairwiseTrustDomain,item_id:str)->int:
  require_session(session,domain)
  if not isinstance(item_id,str) or not item_id.strip():raise EnrollmentError("outbound reservation item identity required")
  with self._lock(True):
   db=self._load();r=db.get(domain.relationship_id)
   if r is not None and r.get("pending_item_id") is not None:
    if r["generation"]==session.generation and r["session_id"]==session.session_id and r["pending_item_id"]==item_id:
     return r["pending_sequence"]
    raise EnrollmentError("unresolved outbound sequence reservation")
   seq=self._reserve_locked(db,r,session,domain)
   rec=db[domain.relationship_id];rec["pending_item_id"]=item_id;rec["pending_sequence"]=seq
   self._write(db);return seq
 def commit_item(self,session:PairwiseSession,domain:PairwiseTrustDomain,item_id:str,sequence:int)->None:
  require_session(session,domain)
  with self._lock(True):
   db=self._load();r=db.get(domain.relationship_id)
   if r is None or r.get("pending_item_id")!=item_id or r.get("pending_sequence")!=sequence:
    raise EnrollmentError("outbound sequence reservation binding mismatch")
   if r["generation"]!=session.generation or r["session_id"]!=session.session_id:
    raise EnrollmentError("outbound sequence reservation session mismatch")
   r.pop("pending_item_id");r.pop("pending_sequence");self._write(db)
 def _reserve_locked(self,db,r,session,domain):
  if r is None:
   if session.generation!=1:raise EnrollmentError("first outbound session generation must be 1")
   seq=1;db[domain.relationship_id]={"generation":1,"session_id":session.session_id,"highest":1}
  else:
   if r.get("pending_item_id") is not None:raise EnrollmentError("unresolved outbound sequence reservation")
   if session.generation<r["generation"]:raise EnrollmentError("stale outbound session rejected")
   if session.generation>r["generation"]:
    if session.generation!=r["generation"]+1:raise EnrollmentError("outbound session generation jump rejected")
    seq=1;r.update(generation=session.generation,session_id=session.session_id,highest=1)
   else:
    if r["session_id"]!=session.session_id:raise EnrollmentError("conflicting outbound session identity")
    seq=r["highest"]+1;r["highest"]=seq
  return seq
 def state(self,relationship_id:str):
  with self._lock(False):
   r=self._load().get(relationship_id);return dict(r) if r else None

 def _load(self):
  try:v=json.loads(self.path.read_text())
  except (OSError,json.JSONDecodeError) as exc:raise EnrollmentError("send sequence registry unreadable") from exc
  if not isinstance(v,dict):raise EnrollmentError("send sequence registry malformed")
  for k,r in v.items():
   base={"generation","session_id","highest"};pending={"pending_item_id","pending_sequence"}
   if not isinstance(k,str) or not isinstance(r,dict) or set(r) not in (base,base|pending):
    raise EnrollmentError("send sequence registry malformed")
   if not isinstance(r["generation"],int) or isinstance(r["generation"],bool) or r["generation"]<1 or not isinstance(r["highest"],int) or isinstance(r["highest"],bool) or r["highest"]<1 or not isinstance(r["session_id"],str) or not r["session_id"].strip():
    raise EnrollmentError("send sequence registry malformed")
   if "pending_item_id" in r:
    if not isinstance(r["pending_item_id"],str) or not r["pending_item_id"].strip() or not isinstance(r["pending_sequence"],int) or isinstance(r["pending_sequence"],bool) or r["pending_sequence"]<1 or r["pending_sequence"]!=r["highest"]:
     raise EnrollmentError("send sequence registry malformed")
  return v
 def _write(self,v):
  tmp=self.path.with_suffix(self.path.suffix+".tmp")
  raw=(json.dumps(v,sort_keys=True,separators=(",",":"))+"\n").encode()
  with private_open(tmp,"wb") as f:f.write(raw);f.flush();os.fsync(f.fileno())
  os.replace(tmp,self.path);fd=os.open(self.path.parent,os.O_RDONLY)
  try:os.fsync(fd)
  finally:os.close(fd)
 def _lock(self,exclusive):return _Lock(self.path.with_suffix(self.path.suffix+".lock"),exclusive)
class _Lock:
 def __init__(self,path,exclusive):self.path=Path(path);self.exclusive=exclusive;self.fd=None
 def __enter__(self):
  self.fd=os.open(self.path,os.O_RDWR|os.O_CREAT,0o600)
  fcntl.flock(self.fd,fcntl.LOCK_EX if self.exclusive else fcntl.LOCK_SH);return self
 def __exit__(self,*args):
  try:fcntl.flock(self.fd,fcntl.LOCK_UN)
  finally:os.close(self.fd);self.fd=None
