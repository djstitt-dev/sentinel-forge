"""Secret- and payload-free Courier telemetry contract for Watchtower."""
from dataclasses import dataclass,asdict
from .enrollment import EnrollmentError

FORBIDDEN=("payload","secret","password","token","private_key","key_material","ciphertext")
@dataclass(frozen=True)
class CourierTelemetry:
 relationship_id:str
 peer_identity:str
 event_type:str
 outcome:str
 reason:str
 sequence:int|None
 correlation_id:str

def build_telemetry(**values)->CourierTelemetry:
 lowered={k.lower() for k in values}
 if any(x in lowered for x in FORBIDDEN):raise EnrollmentError("Watchtower telemetry contains forbidden field")
 required=("relationship_id","peer_identity","event_type","outcome","reason","correlation_id")
 for k in required:
  if not isinstance(values.get(k),str) or not values[k].strip():raise EnrollmentError(f"telemetry {k} required")
 seq=values.get("sequence")
 if seq is not None and (not isinstance(seq,int) or isinstance(seq,bool) or seq<1):raise EnrollmentError("telemetry sequence invalid")
 if set(values)-set(required)-{"sequence"}:raise EnrollmentError("telemetry contains unknown field")
 return CourierTelemetry(*(values[k] for k in required[:-1]),seq,values["correlation_id"])
