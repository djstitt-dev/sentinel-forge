"""Durable intent ledger for authority-free conservative recovery."""

from __future__ import annotations
from .secure_io import private_open
import fcntl,hashlib,json,os
from pathlib import Path
from .enrollment import EnrollmentError

FORMAT="sentinel-recovery-intent-v1"
TERMINAL=frozenset({"COMMITTED","ABORTED"})
ALLOWED_STATUS=frozenset({"PREPARED","APPLIED","COMMITTED","ABORTED"})

class RecoveryIntentLedger:
 def __init__(self,path:Path):
  self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
  with self._lock(exclusive=True):
   if not self.path.exists():self._write({})
   self._load()

 def prepare(self,*,plan_digest:str,target:str,observation_digest:str)->str:
  for name,value in (("plan_digest",plan_digest),("target",target),("observation_digest",observation_digest)):
   if not isinstance(value,str) or not value.strip():raise EnrollmentError(f"recovery intent {name} required")
  with self._lock(exclusive=True):
   db=self._load();existing=db.get(plan_digest)
   if existing and existing["status"] not in TERMINAL:
    raise EnrollmentError("RECOVERY_RECONCILIATION_REQUIRED: unresolved recovery intent")
   core={"format":FORMAT,"plan_digest":plan_digest,"target":target,"observation_digest":observation_digest}
   iid="recovery-intent:"+hashlib.sha256(_canonical(core)).hexdigest()
   db[plan_digest]={**core,"intent_id":iid,"status":"PREPARED"};self._write(db);return iid

 def mark_applied(self,plan_digest:str,intent_id:str):
  self._transition(plan_digest,intent_id,expected="PREPARED",new="APPLIED")

 def commit(self,plan_digest:str,intent_id:str):
  self._transition(plan_digest,intent_id,expected="APPLIED",new="COMMITTED")

 def abort(self,plan_digest:str,intent_id:str):
  self._transition(plan_digest,intent_id,expected="PREPARED",new="ABORTED")

 def unresolved(self,plan_digest:str):
  with self._lock(exclusive=False):
   r=self._load().get(plan_digest)
   return dict(r) if r and r["status"] not in TERMINAL else None

 def record(self,plan_digest:str):
  with self._lock(exclusive=False):
   r=self._load().get(plan_digest)
   return dict(r) if r else None

 def _transition(self,pd,iid,*,expected,new):
  with self._lock(exclusive=True):
   db=self._load();r=db.get(pd)
   if r is None or r["intent_id"]!=iid:raise EnrollmentError("recovery intent identity mismatch")
   if r["status"]!=expected:raise EnrollmentError(f"invalid recovery intent transition from {r['status']}")
   r["status"]=new;self._write(db)

 def _load(self):
  try:v=json.loads(self.path.read_text())
  except (OSError,json.JSONDecodeError) as exc:raise EnrollmentError("malformed recovery intent ledger") from exc
  if not isinstance(v,dict):raise EnrollmentError("malformed recovery intent ledger")
  for key,r in v.items():
   if not isinstance(r,dict) or set(r)!={"format","plan_digest","target","observation_digest","intent_id","status"}:
    raise EnrollmentError("malformed recovery intent record")
   if r["format"]!=FORMAT or r["plan_digest"]!=key or r["status"] not in ALLOWED_STATUS:
    raise EnrollmentError("invalid recovery intent record")
   if any(not isinstance(r[x],str) or not r[x].strip() for x in ("plan_digest","target","observation_digest","intent_id")):
    raise EnrollmentError("invalid recovery intent record")
   core={"format":FORMAT,"plan_digest":r["plan_digest"],"target":r["target"],"observation_digest":r["observation_digest"]}
   if r["intent_id"]!="recovery-intent:"+hashlib.sha256(_canonical(core)).hexdigest():
    raise EnrollmentError("recovery intent integrity failure")
  return v

 def _write(self,v):
  tmp=self.path.with_suffix(self.path.suffix+".tmp")
  with private_open(tmp,"wb") as f:f.write(_canonical(v));f.flush();os.fsync(f.fileno())
  tmp.replace(self.path)
  dfd=os.open(self.path.parent,os.O_RDONLY)
  try:os.fsync(dfd)
  finally:os.close(dfd)

 def _lock(self,*,exclusive:bool):
  return _RecoveryIntentLock(self.path.with_suffix(self.path.suffix+".lock"),exclusive)

class _RecoveryIntentLock:
 def __init__(self,path:Path,exclusive:bool):self.path=Path(path);self.exclusive=exclusive;self.fd=None
 def __enter__(self):
  try:
   self.fd=os.open(self.path,os.O_RDWR|os.O_CREAT,0o600)
   fcntl.flock(self.fd,fcntl.LOCK_EX if self.exclusive else fcntl.LOCK_SH)
  except OSError as exc:
   if self.fd is not None:os.close(self.fd);self.fd=None
   raise EnrollmentError("recovery intent ledger lock unavailable") from exc
  return self
 def __exit__(self,exc_type,exc,tb):
  try:
   if self.fd is not None:fcntl.flock(self.fd,fcntl.LOCK_UN)
  finally:
   if self.fd is not None:os.close(self.fd);self.fd=None

def _canonical(v):return (json.dumps(v,sort_keys=True,separators=(",",":"))+"\n").encode()
