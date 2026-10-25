"""Append-only tamper-evident Courier delivery transition journal."""
from __future__ import annotations
from .secure_io import private_open
from dataclasses import dataclass,asdict
import fcntl,hashlib,json,os
from pathlib import Path
from .enrollment import EnrollmentError

FORMAT="sentinel-courier-delivery-journal-v1"
GENESIS="0"*64
ALLOWED={
 None:{"QUEUED"},"QUEUED":{"PREPARED","CANCELLED"},"PREPARED":{"IN_FLIGHT"},
 "IN_FLIGHT":{"ACKNOWLEDGED","REJECTED","OUTCOME_UNKNOWN"},
 "OUTCOME_UNKNOWN":{"ACKNOWLEDGED","REJECTED"},
}

@dataclass(frozen=True)
class DeliveryEvent:
 sequence:int
 item_id:str
 relationship_id:str
 delivery_sequence:int|None
 prior_state:str|None
 state:str
 artifact_identity:str
 reason:str
 previous_hash:str
 event_hash:str

class DeliveryJournal:
 def __init__(self,path:Path):
  self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
  with self._lock(True):
   if not self.path.exists():self.path.touch(mode=0o600)
   self._verify_unlocked()

 def append(self,*,item_id:str,relationship_id:str,delivery_sequence:int|None,prior_state:str|None,
            state:str,artifact_identity:str,reason:str)->DeliveryEvent:
  if state not in set().union(*ALLOWED.values()):raise EnrollmentError("delivery journal state invalid")
  if state not in ALLOWED.get(prior_state,set()):raise EnrollmentError("delivery journal transition invalid")
  with self._lock(True):
   events=self._verify_unlocked();current=[e for e in events if e.item_id==item_id]
   if current and current[-1].state!=prior_state:raise EnrollmentError("delivery journal prior state mismatch")
   if current and (current[0].relationship_id!=relationship_id or current[0].artifact_identity!=artifact_identity):raise EnrollmentError("delivery journal logical identity changed")
   if not current and prior_state is not None:raise EnrollmentError("delivery journal missing genesis transition")
   assigned=next((x.delivery_sequence for x in current if x.delivery_sequence is not None),None)
   if state in {"QUEUED","CANCELLED"}:
    if delivery_sequence is not None:raise EnrollmentError("delivery journal sequence/state mismatch")
   elif not isinstance(delivery_sequence,int) or isinstance(delivery_sequence,bool) or delivery_sequence<1:
    raise EnrollmentError("delivery journal sequence/state mismatch")
   if assigned is not None and delivery_sequence!=assigned:raise EnrollmentError("delivery journal sequence changed")
   prev=events[-1].event_hash if events else GENESIS
   core={"sequence":len(events)+1,"item_id":item_id,"relationship_id":relationship_id,
         "delivery_sequence":delivery_sequence,"prior_state":prior_state,"state":state,
         "artifact_identity":artifact_identity,"reason":reason,"previous_hash":prev}
   ev=DeliveryEvent(**core,event_hash=_sha(core))
   with private_open(self.path,"ab") as f:f.write(_canonical(asdict(ev)));f.flush();os.fsync(f.fileno())
   return ev
 def verify(self):
  with self._lock(False):return self._verify_unlocked()
 def latest(self,item_id:str):
  events=self.verify();found=[e for e in events if e.item_id==item_id];return found[-1] if found else None
 def _verify_unlocked(self):
  out=[];prev=GENESIS;states={};identities={}
  try:lines=self.path.read_bytes().splitlines()
  except OSError as exc:raise EnrollmentError("delivery journal unreadable") from exc
  for i,line in enumerate(lines,1):
   try:r=json.loads(line)
   except json.JSONDecodeError as exc:raise EnrollmentError("delivery journal malformed") from exc
   if not isinstance(r,dict) or set(r)!={f.name for f in DeliveryEvent.__dataclass_fields__.values()}:
    raise EnrollmentError("delivery journal schema invalid")
   ev=DeliveryEvent(**r);core=asdict(ev);eh=core.pop("event_hash")
   if ev.sequence!=i or ev.previous_hash!=prev or eh!=_sha(core):raise EnrollmentError("delivery journal integrity failure")
   prior=states.get(ev.item_id)
   if ev.prior_state!=prior or ev.state not in ALLOWED.get(prior,set()):raise EnrollmentError("delivery journal transition history invalid")
   prior_events=[x for x in out if x.item_id==ev.item_id]
   assigned=next((x.delivery_sequence for x in prior_events if x.delivery_sequence is not None),None)
   if ev.state in {"QUEUED","CANCELLED"}:
    if ev.delivery_sequence is not None:raise EnrollmentError("delivery journal sequence/state mismatch")
   elif not isinstance(ev.delivery_sequence,int) or isinstance(ev.delivery_sequence,bool) or ev.delivery_sequence<1:
    raise EnrollmentError("delivery journal sequence/state mismatch")
   if assigned is not None and ev.delivery_sequence!=assigned:raise EnrollmentError("delivery journal sequence changed")
   identity=(ev.relationship_id,ev.artifact_identity)
   if ev.item_id in identities and identities[ev.item_id]!=identity:raise EnrollmentError("delivery journal logical identity changed")
   identities.setdefault(ev.item_id,identity)
   states[ev.item_id]=ev.state;prev=eh;out.append(ev)
  return out
 def _lock(self,exclusive):return _Lock(self.path.with_suffix(self.path.suffix+".lock"),exclusive)
class _Lock:
 def __init__(self,path,exclusive):self.path=Path(path);self.exclusive=exclusive;self.fd=None
 def __enter__(self):
  self.fd=os.open(self.path,os.O_RDWR|os.O_CREAT,0o600);fcntl.flock(self.fd,fcntl.LOCK_EX if self.exclusive else fcntl.LOCK_SH);return self
 def __exit__(self,*args):
  try:fcntl.flock(self.fd,fcntl.LOCK_UN)
  finally:os.close(self.fd);self.fd=None
def _canonical(v):return (json.dumps(v,sort_keys=True,separators=(",",":"))+"\n").encode()
def _sha(v):return hashlib.sha256(_canonical(v)).hexdigest()
