"""Offline Courier send orchestration up to the protected-wire boundary."""
from __future__ import annotations
from dataclasses import dataclass
from .courier_limits import enforce_backpressure,enforce_payload
from .enrollment import EnrollmentError
from .transport_contract import TransportMessageContext,build_transport_context

@dataclass(frozen=True)
class PreparedDelivery:
 item_id:str
 relationship_id:str
 sequence:int
 operation:str
 artifact_identity:str
 payload_identity:str
 context:TransportMessageContext

def prepare_delivery(*,payload:bytes,artifact_identity:str,operation:str,domain,session,binding,
                     credential,credential_registry,queue,send_sequences)->PreparedDelivery:
 enforce_payload(payload)
 if not isinstance(artifact_identity,str) or not artifact_identity.strip():raise EnrollmentError("Courier artifact identity required")
 if not isinstance(operation,str) or not operation.strip():raise EnrollmentError("Courier operation required")
 import hashlib
 pid="sha256:"+hashlib.sha256(payload).hexdigest()
 if artifact_identity!=pid:raise EnrollmentError("Courier outbound artifact identity mismatch")
 enforce_backpressure(queue,domain.relationship_id)
 item=queue.enqueue(relationship_id=domain.relationship_id,artifact_identity=artifact_identity,
                    operation=operation,payload_identity=pid)
 record=queue.get(item)
 if record["state"]!="QUEUED":raise EnrollmentError("Courier queued item is not eligible for preparation")
 sequence=send_sequences.reserve_for_item(session,domain,item)
 header,context=build_transport_context(domain,session,binding,credential,credential_registry,
  operation=operation,artifact_identity=artifact_identity,sequence=sequence)
 queue.transition(item,expected="QUEUED",new="PREPARED",sequence=sequence)
 send_sequences.commit_item(session,domain,item,sequence)
 return PreparedDelivery(item,domain.relationship_id,sequence,operation,artifact_identity,pid,context)
def mark_effect_started(prepared:PreparedDelivery,queue)->None:
 r=queue.get(prepared.item_id)
 if r is None or r["relationship_id"]!=prepared.relationship_id or r["sequence"]!=prepared.sequence:
  raise EnrollmentError("Courier prepared delivery queue binding mismatch")
 queue.transition(prepared.item_id,expected="PREPARED",new="IN_FLIGHT",sequence=prepared.sequence)

def mark_effect_uncertain(prepared:PreparedDelivery,queue)->None:
 r=queue.get(prepared.item_id)
 if r is None or r["sequence"]!=prepared.sequence:raise EnrollmentError("Courier delivery queue binding mismatch")
 queue.transition(prepared.item_id,expected="IN_FLIGHT",new="OUTCOME_UNKNOWN",sequence=prepared.sequence)

def reconcile_prepared_sequence(*,item_id:str,domain,session,queue,send_sequences)->int:
 """Close only the crash window where queue PREPARED but sequence reservation remains pending."""
 r=queue.get(item_id)
 if r is None or r["relationship_id"]!=domain.relationship_id or r["state"]!="PREPARED":
  raise EnrollmentError("Courier prepared-sequence reconciliation state mismatch")
 seq=r["sequence"];st=send_sequences.state(domain.relationship_id)
 if st is None or st.get("generation")!=session.generation or st.get("session_id")!=session.session_id:
  raise EnrollmentError("Courier prepared-sequence reconciliation session mismatch")
 if st.get("pending_item_id")!=item_id or st.get("pending_sequence")!=seq:
  raise EnrollmentError("Courier prepared-sequence reconciliation reservation mismatch")
 send_sequences.commit_item(session,domain,item_id,seq)
 return seq

def prepare_intent_delivery(*,intent,payload:bytes,domain,session,binding,credential,credential_registry,queue,send_sequences)->PreparedDelivery:
 """Prepare a queue-v2 delivery whose authority identity was established before queue admission."""
 from .delivery_intent import verify_delivery_intent
 import hashlib
 enforce_payload(payload)
 pid="sha256:"+hashlib.sha256(payload).hexdigest()
 verify_delivery_intent(intent,relationship_id=domain.relationship_id,artifact_identity=pid)
 item=queue.enqueue(intent=intent,payload_identity=pid)
 record=queue.get(item)
 if record["state"]!="QUEUED":raise EnrollmentError("Courier queued intent is not eligible for preparation")
 sequence=send_sequences.reserve_for_item(session,domain,item)
 header,context=build_transport_context(domain,session,binding,credential,credential_registry,
  operation=intent.operation,artifact_identity=intent.artifact_identity,sequence=sequence)
 queue.transition(item,expected="QUEUED",new="PREPARED",sequence=sequence)
 send_sequences.commit_item(session,domain,item,sequence)
 return PreparedDelivery(item,domain.relationship_id,sequence,intent.operation,intent.artifact_identity,pid,context)
