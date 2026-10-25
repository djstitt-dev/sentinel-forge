"""Conservative reconciliation for Courier delivery uncertainty."""
from __future__ import annotations
from dataclasses import dataclass
from .courier_ack import CourierAcknowledgement,verify_ack
from .enrollment import EnrollmentError

@dataclass(frozen=True)
class DeliveryAssessment:
 item_id:str
 state:str
 conclusion:str
 reason:str

def assess_delivery(queue,item_id:str)->DeliveryAssessment:
 r=queue.get(item_id)
 if r is None:raise EnrollmentError("Courier queue item unknown")
 state=r["state"]
 if state=="OUTCOME_UNKNOWN":return DeliveryAssessment(item_id,state,"RECONCILIATION_REQUIRED","delivery outcome not established")
 if state=="ACKNOWLEDGED":return DeliveryAssessment(item_id,state,"COMPLETED","bound acknowledgement recorded")
 if state=="REJECTED":return DeliveryAssessment(item_id,state,"REJECTED","remote rejection established")
 if state=="IN_FLIGHT":return DeliveryAssessment(item_id,state,"RECONCILIATION_REQUIRED","effect may have occurred")
 return DeliveryAssessment(item_id,state,"NOT_FINAL","delivery has no established external effect")

def reconcile_with_ack(queue,item_id:str,ack:CourierAcknowledgement,context,*,operation:str,artifact_identity:str,sequence:int)->str:
 r=queue.get(item_id)
 if r is None:raise EnrollmentError("Courier queue item unknown")
 if r["state"] not in {"IN_FLIGHT","OUTCOME_UNKNOWN"}:raise EnrollmentError("Courier delivery state does not require acknowledgement reconciliation")
 if r["sequence"]!=sequence or r["artifact_identity"]!=artifact_identity or r["operation"]!=operation:
  raise EnrollmentError("Courier reconciliation queue binding mismatch")
 verify_ack(ack,context,sequence=sequence,operation=operation,artifact_identity=artifact_identity)
 if ack.disposition=="ACCEPTED":
  queue.transition(item_id,expected=r["state"],new="ACKNOWLEDGED",sequence=sequence,acknowledgement=ack.acknowledgement_digest)
  return "ACKNOWLEDGED"
 queue.transition(item_id,expected=r["state"],new="REJECTED",sequence=sequence)
 return "REJECTED"
