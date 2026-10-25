"""DeliveryIntent-bound durable outbound queue; versioned separately from queue-v1."""
from __future__ import annotations
import fcntl,hashlib,json,os
from pathlib import Path
from .delivery_intent import DeliveryIntent,verify_delivery_intent
from .enrollment import EnrollmentError
from .secure_io import private_open,ensure_private_file

FORMAT="sentinel-courier-outbound-queue-v2"
MAX_ITEMS=4096
MAX_RECORD_BYTES=16*1024
FINAL=frozenset({"ACKNOWLEDGED","REJECTED","CANCELLED"})
ACTIVE=frozenset({"QUEUED","PREPARED","IN_FLIGHT","OUTCOME_UNKNOWN"})
STATES=FINAL|ACTIVE
_ALLOWED={("QUEUED","PREPARED"),("PREPARED","IN_FLIGHT"),("IN_FLIGHT","ACKNOWLEDGED"),
 ("IN_FLIGHT","REJECTED"),("IN_FLIGHT","OUTCOME_UNKNOWN"),("OUTCOME_UNKNOWN","ACKNOWLEDGED"),
 ("OUTCOME_UNKNOWN","REJECTED"),("QUEUED","CANCELLED")}
_FIELDS={"format","delivery_id","correlation_id","intent_digest","authorization_reference","relationship_id",
 "artifact_identity","operation","payload_identity","item_id","state","sequence","acknowledgement"}

class IntentCourierQueue:
 def __init__(self,path:Path):
  self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
  with self._lock(True):
   if not self.path.exists():self._write({})
   else:ensure_private_file(self.path)
   self._load()

 def enqueue(self,*,intent:DeliveryIntent,payload_identity:str)->str:
  verify_delivery_intent(intent)
  if not isinstance(payload_identity,str) or not payload_identity.strip():raise EnrollmentError("Courier queue payload identity required")
  if payload_identity!=intent.artifact_identity:raise EnrollmentError("Courier queue intent/payload identity mismatch")
  core=_identity_core(intent,payload_identity);item_id="queue2:"+_sha(core)
  with self._lock(True):
   db=self._load()
   if item_id in db:return item_id
   # A correlation identity is single-use inside one relationship even if an attacker changes another binding.
   for r in db.values():
    if r["relationship_id"]==intent.relationship_id and r["correlation_id"]==intent.correlation_id:
     raise EnrollmentError("Courier delivery correlation conflict")
   if sum(1 for r in db.values() if r["state"] not in FINAL)>=MAX_ITEMS:raise EnrollmentError("Courier queue capacity exceeded")
   record={**core,"item_id":item_id,"state":"QUEUED","sequence":None,"acknowledgement":None}
   if len(_canonical(record))>MAX_RECORD_BYTES:raise EnrollmentError("Courier queue record exceeds bound")
   db[item_id]=record;self._write(db);return item_id

 def transition(self,item_id:str,*,expected:str,new:str,sequence:int|None=None,acknowledgement:str|None=None):
  if (expected,new) not in _ALLOWED:raise EnrollmentError("invalid Courier queue transition")
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
  except (OSError,json.JSONDecodeError) as exc:raise EnrollmentError("Courier queue-v2 unreadable") from exc
  if not isinstance(v,dict):raise EnrollmentError("Courier queue-v2 malformed")
  correlations=set()
  for key,r in v.items():
   if not isinstance(r,dict) or set(r)!=_FIELDS or r["format"]!=FORMAT or r["item_id"]!=key or r["state"] not in STATES:
    raise EnrollmentError("Courier queue-v2 record malformed")
   for n in ("delivery_id","correlation_id","intent_digest","authorization_reference","relationship_id","artifact_identity","operation","payload_identity"):
    if not isinstance(r[n],str) or not r[n].strip():raise EnrollmentError("Courier queue-v2 record malformed")
   if r["artifact_identity"]!=r["payload_identity"]:raise EnrollmentError("Courier queue-v2 payload binding failure")
   embedded=DeliveryIntent("sentinel-courier-delivery-intent-v1",r["delivery_id"],r["correlation_id"],r["relationship_id"],
    r["artifact_identity"],r["operation"],r["authorization_reference"],r["intent_digest"])
   verify_delivery_intent(embedded)
   core={n:r[n] for n in ("format","delivery_id","correlation_id","intent_digest","authorization_reference","relationship_id","artifact_identity","operation","payload_identity")}
   if key!="queue2:"+_sha(core):raise EnrollmentError("Courier queue-v2 identity integrity failure")
   corr=(r["relationship_id"],r["correlation_id"])
   if corr in correlations:raise EnrollmentError("Courier queue-v2 duplicate correlation identity")
   correlations.add(corr)
   seq=r["sequence"]
   if r["state"] in {"QUEUED","CANCELLED"}:
    if seq is not None:raise EnrollmentError("Courier queue-v2 sequence/state mismatch")
   elif not isinstance(seq,int) or isinstance(seq,bool) or seq<1:raise EnrollmentError("Courier queue-v2 sequence/state mismatch")
   ack=r["acknowledgement"]
   if r["state"]=="ACKNOWLEDGED":
    if not isinstance(ack,str) or not ack.strip():raise EnrollmentError("Courier queue-v2 acknowledgement/state mismatch")
   elif ack is not None:raise EnrollmentError("Courier queue-v2 acknowledgement/state mismatch")
  return v

 def _write(self,v):
  tmp=self.path.with_suffix(self.path.suffix+".tmp")
  with private_open(tmp,"wb") as f:f.write(_canonical(v));f.flush();os.fsync(f.fileno())
  os.replace(tmp,self.path);fd=os.open(self.path.parent,os.O_RDONLY)
  try:os.fsync(fd)
  finally:os.close(fd)
 def _lock(self,exclusive):return _Lock(self.path.with_suffix(self.path.suffix+".lock"),exclusive)

def _identity_core(i,payload):
 return {"format":FORMAT,"delivery_id":i.delivery_id,"correlation_id":i.correlation_id,"intent_digest":i.intent_digest,
  "authorization_reference":i.authorization_reference,"relationship_id":i.relationship_id,
  "artifact_identity":i.artifact_identity,"operation":i.operation,"payload_identity":payload}
def _canonical(v):return (json.dumps(v,sort_keys=True,separators=(",",":"))+"\n").encode()
def _sha(v):return hashlib.sha256(_canonical(v)).hexdigest()
class _Lock:
 def __init__(self,path,exclusive):self.path=Path(path);self.exclusive=exclusive;self.fd=None
 def __enter__(self):
  self.fd=os.open(self.path,os.O_RDWR|os.O_CREAT|O_NOFOLLOW,0o600);os.fchmod(self.fd,0o600)
  fcntl.flock(self.fd,fcntl.LOCK_EX if self.exclusive else fcntl.LOCK_SH);return self
 def __exit__(self,*args):
  try:fcntl.flock(self.fd,fcntl.LOCK_UN)
  finally:os.close(self.fd);self.fd=None
O_NOFOLLOW=getattr(os,"O_NOFOLLOW",0)
