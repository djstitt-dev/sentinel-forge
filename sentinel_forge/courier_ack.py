"""Exact message-bound Courier acknowledgement contract."""
from __future__ import annotations
from dataclasses import dataclass,asdict
import hashlib,json
from .enrollment import EnrollmentError
from .transport_contract import TransportMessageContext

FORMAT="sentinel-courier-ack-v1"
FINAL=frozenset({"ACCEPTED","REJECTED"})

@dataclass(frozen=True)
class CourierAcknowledgement:
 format:str
 relationship_id:str
 session_id:str
 session_generation:int
 credential_generation:int
 sequence:int
 operation:str
 artifact_identity:str
 transport_context_digest:str
 disposition:str
 reason:str
 acknowledgement_digest:str
 def as_dict(self):return asdict(self)

def build_ack(context:TransportMessageContext,*,sequence:int,operation:str,artifact_identity:str,
              disposition:str,reason:str)->CourierAcknowledgement:
 if not isinstance(disposition,str) or disposition not in FINAL:raise EnrollmentError("Courier acknowledgement disposition invalid")
 if not isinstance(sequence,int) or isinstance(sequence,bool) or sequence<1:raise EnrollmentError("Courier acknowledgement sequence invalid")
 for name,value in (("operation",operation),("artifact_identity",artifact_identity),("reason",reason)):
  if not isinstance(value,str) or not value.strip():raise EnrollmentError(f"Courier acknowledgement {name} required")
 core={"format":FORMAT,"relationship_id":context.relationship_id,"session_id":context.session_id,
       "session_generation":context.session_generation,"credential_generation":context.credential_generation,
       "sequence":sequence,"operation":operation,"artifact_identity":artifact_identity,
       "transport_context_digest":context.context_digest,"disposition":disposition,"reason":reason}
 return CourierAcknowledgement(**core,acknowledgement_digest="sha256:"+_sha(core))

def verify_ack(ack:CourierAcknowledgement,context:TransportMessageContext,*,sequence:int,
               operation:str,artifact_identity:str)->None:
 expected=build_ack(context,sequence=sequence,operation=operation,artifact_identity=artifact_identity,
                    disposition=ack.disposition,reason=ack.reason)
 if ack!=expected:raise EnrollmentError("Courier acknowledgement binding mismatch")

def _canonical(v):return (json.dumps(v,sort_keys=True,separators=(",",":"))+"\n").encode()
def _sha(v):return hashlib.sha256(_canonical(v)).hexdigest()
