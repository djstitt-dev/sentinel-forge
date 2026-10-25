"""Durable authority-free outbound Courier queue."""
from __future__ import annotations
from .secure_io import private_open
import fcntl,hashlib,json,os
from pathlib import Path
from .enrollment import EnrollmentError

FORMAT="sentinel-courier-outbound-queue-v1"
MAX_ITEMS=4096
MAX_RECORD_BYTES=16*1024
FINAL=frozenset({"ACKNOWLEDGED","REJECTED","CANCELLED"})
ACTIVE=frozenset({"QUEUED","PREPARED","IN_FLIGHT","OUTCOME_UNKNOWN"})
STATES=FINAL|ACTIVE

class CourierQueue:
 def __init__(self,path:Path):
  self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
  with self._lock(True):
   if not self.path.exists():self._write({})
   self._load()
 def enqueue(self,*,relationship_id:str,artifact_identity:str,operation:str,payload_identity:str)->str:
  values=(relationship_id,artifact_identity,operation,payload_identity)
  if any(not isinstance(x,str) or not x.strip() for x in values):raise EnrollmentError("Courier queue identity fields required")
  core={"format":FORMAT,"relationship_id":relationship_id,"artifact_identity":artifact_identity,
        "operation":operation,"payload_identity":payload_identity}
  item_id="queue:"+hashlib.sha256(_canonical(core)).hexdigest()
  with self._lock(True):
   db=self._load()
   if item_id in db:return item_id
   if sum(1 for r in db.values() if r["state"] not in FINAL)>=MAX_ITEMS:raise EnrollmentError("Courier queue capacity exceeded")
   record={**core,"item_id":item_id,"state":"QUEUED","sequence":None,"acknowledgement":None}
   if len(_canonical(record))>MAX_RECORD_BYTES:raise EnrollmentError("Courier queue record exceeds bound")
   db[item_id]=record;self._write(db);return item_id

 def transition(self,item_id:str,*,expected:str,new:str,sequence:int|None=None,acknowledgement:str|None=None):
  allowed={("QUEUED","PREPARED"),("PREPARED","IN_FLIGHT"),("IN_FLIGHT","ACKNOWLEDGED"),
           ("IN_FLIGHT","REJECTED"),("IN_FLIGHT","OUTCOME_UNKNOWN"),("OUTCOME_UNKNOWN","ACKNOWLEDGED"),
           ("OUTCOME_UNKNOWN","REJECTED"),("QUEUED","CANCELLED")}
  if (expected,new) not in allowed:raise EnrollmentError("invalid Courier queue transition")
  with self._lock(True):
   db=self._load();r=db.get(item_id)
   if r is None:raise EnrollmentError("Courier queue item unknown")
   if r["state"]!=expected:raise EnrollmentError("Courier queue state changed")
   if new in {"PREPARED","IN_FLIGHT","ACKNOWLEDGED","REJECTED","OUTCOME_UNKNOWN"}:
    seq=sequence if sequence is not None else r["sequence"]
    if not isinstance(seq,int) or isinstance(seq,bool) or seq<1:raise EnrollmentError("Courier queue sequence required")
    if r["sequence"] not in (None,seq):raise EnrollmentError("Courier queue sequence immutable")
    r["sequence"]=seq
   if new=="ACKNOWLEDGED":
    if not isinstance(acknowledgement,str) or not acknowledgement.strip():raise EnrollmentError("Courier acknowledgement required")
    r["acknowledgement"]=acknowledgement
   r["state"]=new;self._write(db)

 def get(self,item_id:str):
  with self._lock(False):
   r=self._load().get(item_id);return dict(r) if r else None
 def pending(self,relationship_id:str):
  with self._lock(False):
   return [dict(r) for r in self._load().values() if r["relationship_id"]==relationship_id and r["state"] not in FINAL]
 def _load(self):
  try:v=json.loads(self.path.read_text())
  except (OSError,json.JSONDecodeError) as exc:raise EnrollmentError("Courier queue unreadable") from exc
  if not isinstance(v,dict):raise EnrollmentError("Courier queue malformed")
  required={"format","relationship_id","artifact_identity","operation","payload_identity","item_id","state","sequence","acknowledgement"}
  for key,r in v.items():
   if not isinstance(r,dict) or set(r)!=required or r["format"]!=FORMAT or r["item_id"]!=key or r["state"] not in STATES:
    raise EnrollmentError("Courier queue record malformed")
   for name in ("relationship_id","artifact_identity","operation","payload_identity"):
    if not isinstance(r[name],str) or not r[name].strip():raise EnrollmentError("Courier queue record malformed")
   core={"format":FORMAT,"relationship_id":r["relationship_id"],"artifact_identity":r["artifact_identity"],
         "operation":r["operation"],"payload_identity":r["payload_identity"]}
   if key!="queue:"+hashlib.sha256(_canonical(core)).hexdigest():raise EnrollmentError("Courier queue identity integrity failure")
   seq=r["sequence"]
   if r["state"]=="QUEUED" or r["state"]=="CANCELLED":
    if seq is not None:raise EnrollmentError("Courier queue sequence/state mismatch")
   elif not isinstance(seq,int) or isinstance(seq,bool) or seq<1:raise EnrollmentError("Courier queue sequence/state mismatch")
   ack=r["acknowledgement"]
   if r["state"]=="ACKNOWLEDGED":
    if not isinstance(ack,str) or not ack.strip():raise EnrollmentError("Courier queue acknowledgement/state mismatch")
   elif ack is not None:raise EnrollmentError("Courier queue acknowledgement/state mismatch")
  return v
 def _write(self,v):
  tmp=self.path.with_suffix(self.path.suffix+".tmp")
  with private_open(tmp,"wb") as f:f.write(_canonical(v));f.flush();os.fsync(f.fileno())
  os.replace(tmp,self.path);fd=os.open(self.path.parent,os.O_RDONLY)
  try:os.fsync(fd)
  finally:os.close(fd)
 def _lock(self,exclusive):return _Lock(self.path.with_suffix(self.path.suffix+".lock"),exclusive)

class _Lock:
 def __init__(self,path,exclusive):self.path=Path(path);self.exclusive=exclusive;self.fd=None
 def __enter__(self):
  self.fd=os.open(self.path,os.O_RDWR|os.O_CREAT,0o600);fcntl.flock(self.fd,fcntl.LOCK_EX if self.exclusive else fcntl.LOCK_SH);return self
 def __exit__(self,*args):
  try:fcntl.flock(self.fd,fcntl.LOCK_UN)
  finally:os.close(self.fd);self.fd=None

def _canonical(v):return (json.dumps(v,sort_keys=True,separators=(",",":"))+"\n").encode()
