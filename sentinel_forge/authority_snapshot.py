"""Cross-authority consistency snapshot for one pairwise relationship."""
from __future__ import annotations
from dataclasses import dataclass,asdict
import hashlib,json
from .enrollment import EnrollmentError
from .credential_session import require_registry_current_credential_session
from .session import require_session

FORMAT="sentinel-authority-snapshot-v1"
@dataclass(frozen=True)
class AuthoritySnapshot:
 format:str;relationship_id:str;enrollment_id:str;peer_identity:str;credential_generation:int;key_reference:str;session_generation:int;session_id:str;send_highest:int;send_pending_item_id:str|None;send_pending_sequence:int|None;receive_highest:int;snapshot_digest:str
 def as_dict(self):return asdict(self)

def build_authority_snapshot(*,domain,session,binding,credential,credential_registry,send_registry,replay_registry)->AuthoritySnapshot:
 require_session(session,domain);require_registry_current_credential_session(binding,session,domain,credential,credential_registry)
 ss=send_registry.state(domain.relationship_id);rs=replay_registry.state(domain.relationship_id)
 if ss is not None:
  if ss["generation"]!=session.generation or ss["session_id"]!=session.session_id:raise EnrollmentError("send authority disagrees with current session")
  sh=ss["highest"];pi=ss.get("pending_item_id");ps=ss.get("pending_sequence")
 else:sh=0;pi=ps=None
 if rs is not None:
  if rs["generation"]!=session.generation or rs["session_id"]!=session.session_id:raise EnrollmentError("receive authority disagrees with current session")
  rh=rs["highest"]
 else:rh=0
 core={"format":FORMAT,"relationship_id":domain.relationship_id,"enrollment_id":domain.enrollment_id,"peer_identity":domain.peer_identity,"credential_generation":credential.generation,"key_reference":credential.key_reference,"session_generation":session.generation,"session_id":session.session_id,"send_highest":sh,"send_pending_item_id":pi,"send_pending_sequence":ps,"receive_highest":rh}
 return AuthoritySnapshot(**core,snapshot_digest="sha256:"+_sha(core))
def verify_authority_snapshot(s):
 if not isinstance(s,AuthoritySnapshot):raise EnrollmentError("authority snapshot contract required")
 d=s.as_dict();digest=d.pop("snapshot_digest")
 if digest!="sha256:"+_sha(d):raise EnrollmentError("authority snapshot integrity failure")
 for n in ("relationship_id","enrollment_id","peer_identity","key_reference","session_id"):
  if not isinstance(d[n],str) or not d[n].strip():raise EnrollmentError("authority snapshot malformed")
 for n in ("credential_generation","session_generation","send_highest","receive_highest"):
  if not isinstance(d[n],int) or isinstance(d[n],bool) or d[n]<0:raise EnrollmentError("authority snapshot malformed")
 if (s.send_pending_item_id is None)!=(s.send_pending_sequence is None):raise EnrollmentError("authority snapshot pending reservation malformed")
 if s.send_pending_sequence is not None and (not isinstance(s.send_pending_sequence,int) or isinstance(s.send_pending_sequence,bool) or s.send_pending_sequence!=s.send_highest or s.send_pending_sequence<1):raise EnrollmentError("authority snapshot pending reservation malformed")
 return True
def _sha(v):return hashlib.sha256((json.dumps(v,sort_keys=True,separators=(",",":"))+"\n").encode()).hexdigest()
