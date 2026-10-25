"""Conservative Courier crash/corruption recovery classification."""
from dataclasses import dataclass
from .enrollment import EnrollmentError

@dataclass(frozen=True)
class CourierRecoveryDecision:
 classification:str
 reason:str

def classify_delivery_recovery(queue,journal,item_id:str)->CourierRecoveryDecision:
 try:q=queue.get(item_id);j=journal.latest(item_id)
 except EnrollmentError:return CourierRecoveryDecision("OPERATOR_REQUIRED","durable state unreadable or corrupt")
 if q is None and j is None:return CourierRecoveryDecision("NO_ACTION","delivery absent")
 if q is None or j is None:return CourierRecoveryDecision("RECONCILIATION_REQUIRED","queue/journal disagreement")
 if q["relationship_id"]!=j.relationship_id or q["artifact_identity"]!=j.artifact_identity or q["sequence"]!=j.delivery_sequence or q["state"]!=j.state:
  return CourierRecoveryDecision("RECONCILIATION_REQUIRED","queue/journal disagreement")
 if q["state"] in {"IN_FLIGHT","OUTCOME_UNKNOWN"}:
  return CourierRecoveryDecision("RECONCILIATION_REQUIRED","external effect may have occurred")
 if q["state"]=="PREPARED":return CourierRecoveryDecision("OPERATOR_REQUIRED","prepared delivery must be revalidated before effect")
 if q["state"]=="QUEUED":return CourierRecoveryDecision("SAFE_TO_REVALIDATE","no external effect recorded")
 if q["state"] in {"ACKNOWLEDGED","REJECTED","CANCELLED"}:return CourierRecoveryDecision("TERMINAL","delivery already final")
 return CourierRecoveryDecision("OPERATOR_REQUIRED","unknown delivery state")
