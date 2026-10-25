"""Tamper-evident authoritative enrollment state journal.

Reference local persistence only. Hash chaining detects modification relative to
the possessed journal; it is not an externally anchored tamper-proof store.
"""

from __future__ import annotations
from .secure_io import private_open
import fcntl,hashlib,json,os
from pathlib import Path
from typing import Any
from .enrollment import EnrollmentError

FORMAT="sentinel-enrollment-state-journal-v1"
GENESIS="0"*64
ALLOWED={
 None:{"STAGED"},
 "STAGED":{"REMOTE_AUTHENTICATED","REVOKED"},
 "REMOTE_AUTHENTICATED":{"VERIFIED","REVOKED"},
 "VERIFIED":{"ACTIVE","REVOKED"},
 "ACTIVE":{"REVOKED"},
 "REVOKED":set(),
}

class EnrollmentStateJournal:
 def __init__(self,path:Path):
  self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
  with self._lock(exclusive=True):
   if not self.path.exists():self.path.touch(mode=0o600)
   self.verify()

 def transition(self,*,enrollment_id:str,remote_identity:str,new_state:str,
                authorization_reference:str,reason:str)->dict[str,Any]:
  if not all(isinstance(x,str) and x.strip() for x in
             (enrollment_id,remote_identity,new_state,authorization_reference,reason)):
   raise EnrollmentError("state transition fields must be explicit")
  with self._lock(exclusive=True):
   records=self.verify()
   current=self._current(records,enrollment_id)
   old=None if current is None else current["new_state"]
   if new_state not in ALLOWED.get(old,set()):
    raise EnrollmentError(f"illegal enrollment transition {old!r} -> {new_state!r}")
   if current is not None and current["remote_identity"]!=remote_identity:
    raise EnrollmentError("remote identity cannot change within enrollment")
   prev=GENESIS if not records else records[-1]["record_hash"]
   core={"format":FORMAT,"sequence":len(records)+1,"enrollment_id":enrollment_id,
         "remote_identity":remote_identity,"old_state":old,"new_state":new_state,
         "authorization_reference":authorization_reference,"reason":reason,
         "previous_hash":prev}
   rec={**core,"record_hash":_sha(core)}
   with private_open(self.path,"ab") as f:
    f.write(_canonical(rec));f.flush();os.fsync(f.fileno())
   return rec

 def state(self,enrollment_id:str)->str|None:
  with self._lock(exclusive=False):
   cur=self._current(self.verify(),enrollment_id)
   return None if cur is None else cur["new_state"]

 def _lock(self,*,exclusive:bool):
  return _StateJournalLock(self.path.with_suffix(self.path.suffix+".lock"),exclusive)

 def verify(self)->list[dict[str,Any]]:
  try:raw=self.path.read_bytes()
  except OSError as exc:raise EnrollmentError("cannot read enrollment state journal") from exc
  if raw and not raw.endswith(b"\n"):raise EnrollmentError("truncated enrollment state journal")
  records=[];prev=GENESIS;states={}
  for idx,line in enumerate(raw.splitlines(),1):
   try:r=json.loads(line)
   except json.JSONDecodeError as exc:raise EnrollmentError("malformed enrollment state journal") from exc
   required={"format","sequence","enrollment_id","remote_identity","old_state","new_state",
             "authorization_reference","reason","previous_hash","record_hash"}
   if set(r)!=required:raise EnrollmentError("invalid enrollment state journal schema")
   if r["format"]!=FORMAT or r["sequence"]!=idx or r["previous_hash"]!=prev:
    raise EnrollmentError("enrollment state journal continuity failure")
   core={k:r[k] for k in r if k!="record_hash"}
   if r["record_hash"]!=_sha(core):raise EnrollmentError("enrollment state journal hash failure")
   old=states.get(r["enrollment_id"])
   if r["old_state"]!=old or r["new_state"] not in ALLOWED.get(old,set()):
    raise EnrollmentError("enrollment state journal transition failure")
   states[r["enrollment_id"]]=r["new_state"];prev=r["record_hash"];records.append(r)
  return records

 @staticmethod
 def _current(records,enrollment_id):
  for r in reversed(records):
   if r["enrollment_id"]==enrollment_id:return r
  return None


class _StateJournalLock:
 def __init__(self,path:Path,exclusive:bool):
  self.path=Path(path);self.exclusive=exclusive;self.fd=None
 def __enter__(self):
  try:
   self.fd=os.open(self.path,os.O_RDWR|os.O_CREAT,0o600)
   fcntl.flock(self.fd,fcntl.LOCK_EX if self.exclusive else fcntl.LOCK_SH)
  except OSError as exc:
   if self.fd is not None:os.close(self.fd);self.fd=None
   raise EnrollmentError("enrollment state journal lock unavailable") from exc
  return self
 def __exit__(self,exc_type,exc,tb):
  try:
   if self.fd is not None:fcntl.flock(self.fd,fcntl.LOCK_UN)
  finally:
   if self.fd is not None:os.close(self.fd);self.fd=None

def _canonical(v):return (json.dumps(v,sort_keys=True,separators=(",",":"))+"\n").encode()
def _sha(v):return hashlib.sha256(_canonical(v)).hexdigest()
