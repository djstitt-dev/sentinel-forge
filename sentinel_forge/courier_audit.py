"""Required evidence helpers for Courier transport state changes."""
from .enrollment import EnrollmentError

def record_courier_event(evidence,*,correlation_id:str,actor:str,target:str,
                         authorization_reference:str,input_identity:str,output_identity:str,
                         outcome:str,reason:str,timestamp:str="UNKNOWN",time_uncertainty:str="UNKNOWN"):
 for name,value in (("correlation_id",correlation_id),("actor",actor),("target",target),("outcome",outcome),("reason",reason)):
  if not isinstance(value,str) or not value.strip():raise EnrollmentError(f"Courier audit {name} required")
 return evidence.append(correlation_id=correlation_id,actor=actor,target=target,
  authorization_reference=authorization_reference,input_identity=input_identity,
  output_identity=output_identity,outcome=outcome,reason=reason,
  source_context="COURIER_TRANSPORT",collector_method="COURIER_AUDIT",
  timestamp=timestamp,time_uncertainty=time_uncertainty)
