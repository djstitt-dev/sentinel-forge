"""Durable intent ledger for enrollment transitions."""

from __future__ import annotations
from .secure_io import private_open
import fcntl,hashlib,json,os
from pathlib import Path
from .enrollment import EnrollmentError

FORMAT="sentinel-enrollment-transition-intent-v1"
TERMINAL={"COMMITTED","ABORTED"}

class TransitionIntentLedger:
 def __init__(self,path:Path):
  self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
  with self._lock(exclusive=True):
   if not self.path.exists():self._write({})
   self._load()
 def prepare(self,*,enrollment_id:str,remote_identity:str,from_state:str|None,to_state:str,
             authorization_reference:str,reason:str)->str:
  with self._lock(exclusive=True):
   db=self._load()
   if enrollment_id in db and db[enrollment_id]["status"] not in TERMINAL:
    raise EnrollmentError("RECONCILIATION_REQUIRED: unresolved enrollment transition intent")
   core={"format":FORMAT,"enrollment_id":enrollment_id,"remote_identity":remote_identity,
         "from_state":from_state,"to_state":to_state,"authorization_reference":authorization_reference,"reason":reason}
   iid="intent:"+hashlib.sha256(_canonical(core)).hexdigest()
   db[enrollment_id]={**core,"intent_id":iid,"status":"PREPARED"};self._write(db);return iid
 def mark_mutated(self,enrollment_id:str,intent_id:str):
  self._set(enrollment_id,intent_id,"MUTATED")
 def commit(self,enrollment_id:str,intent_id:str):
  self._set(enrollment_id,intent_id,"COMMITTED")
 def abort(self,enrollment_id:str,intent_id:str,*,authorization_reference:str):
  if not isinstance(authorization_reference,str) or not authorization_reference.strip():
   raise EnrollmentError("abort authorization reference required")
  with self._lock(exclusive=True):
   db=self._load();r=db.get(enrollment_id)
   if r is None or r["intent_id"]!=intent_id:raise EnrollmentError("transition intent identity mismatch")
   if r["status"]!="PREPARED":raise EnrollmentError("only prepared transition intent can be aborted")
   r["status"]="ABORTED";r["reconciliation_authorization_reference"]=authorization_reference
   self._write(db)
 def unresolved(self,enrollment_id:str):
  with self._lock(exclusive=False):
   r=self._load().get(enrollment_id)
   return r if r and r["status"] not in TERMINAL else None
 def _set(self,eid,iid,status):
  with self._lock(exclusive=True):
   db=self._load();r=db.get(eid)
   if r is None or r["intent_id"]!=iid:raise EnrollmentError("transition intent identity mismatch")
   expected={"MUTATED":"PREPARED","COMMITTED":"MUTATED"}.get(status)
   if expected is None or r["status"]!=expected:raise EnrollmentError(f"invalid transition intent transition from {r['status']}")
   r["status"]=status;self._write(db)
 def _lock(self,*,exclusive:bool):
  return _IntentFileLock(self.path.with_suffix(self.path.suffix+".lock"),exclusive)
 def _load(self):
  try:v=json.loads(self.path.read_text())
  except (OSError,json.JSONDecodeError) as exc:raise EnrollmentError("malformed transition intent ledger") from exc
  if not isinstance(v,dict):raise EnrollmentError("malformed transition intent ledger")
  base={"format","enrollment_id","remote_identity","from_state","to_state","authorization_reference","reason","intent_id","status"}
  for eid,r in v.items():
   if not isinstance(eid,str) or not eid.strip() or not isinstance(r,dict):
    raise EnrollmentError("malformed transition intent record")
   allowed=base|({"reconciliation_authorization_reference"} if r.get("status")=="ABORTED" else set())
   if set(r)!=allowed or r.get("format")!=FORMAT or r.get("enrollment_id")!=eid or r.get("status") not in {"PREPARED","MUTATED","COMMITTED","ABORTED"}:
    raise EnrollmentError("malformed transition intent record")
   for name in ("remote_identity","to_state","authorization_reference","reason","intent_id"):
    if not isinstance(r.get(name),str) or not r[name].strip():raise EnrollmentError("malformed transition intent record")
   if r["from_state"] is not None and (not isinstance(r["from_state"],str) or not r["from_state"].strip()):raise EnrollmentError("malformed transition intent record")
   core={k:r[k] for k in ("format","enrollment_id","remote_identity","from_state","to_state","authorization_reference","reason")}
   if r["intent_id"]!="intent:"+hashlib.sha256(_canonical(core)).hexdigest():raise EnrollmentError("transition intent integrity failure")
   if r["status"]=="ABORTED" and (not isinstance(r["reconciliation_authorization_reference"],str) or not r["reconciliation_authorization_reference"].strip()):raise EnrollmentError("malformed transition intent record")
  return v
 def _write(self,v):
  tmp=self.path.with_suffix(self.path.suffix+".tmp")
  with private_open(tmp,"wb") as f:f.write(_canonical(v));f.flush();os.fsync(f.fileno())
  tmp.replace(self.path)
  dfd=os.open(self.path.parent,os.O_RDONLY)
  try:os.fsync(dfd)
  finally:os.close(dfd)


class _IntentFileLock:
 def __init__(self,path:Path,exclusive:bool):
  self.path=Path(path);self.exclusive=exclusive;self.fd=None
 def __enter__(self):
  try:
   self.fd=os.open(self.path,os.O_RDWR|os.O_CREAT,0o600)
   fcntl.flock(self.fd,fcntl.LOCK_EX if self.exclusive else fcntl.LOCK_SH)
  except OSError as exc:
   if self.fd is not None:os.close(self.fd);self.fd=None
   raise EnrollmentError("transition intent ledger lock unavailable") from exc
  return self
 def __exit__(self,exc_type,exc,tb):
  try:
   if self.fd is not None:fcntl.flock(self.fd,fcntl.LOCK_UN)
  finally:
   if self.fd is not None:os.close(self.fd);self.fd=None

def _canonical(v):return (json.dumps(v,sort_keys=True,separators=(",",":"))+"\n").encode()
