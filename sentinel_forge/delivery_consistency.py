"""Independent queue/journal consistency gate."""
from .enrollment import EnrollmentError

def require_delivery_consistent(queue,journal,item_id:str)->None:
 q=queue.get(item_id);j=journal.latest(item_id)
 if q is None and j is None:return
 if q is None or j is None:raise EnrollmentError("Courier queue/journal disagreement")
 if q["relationship_id"]!=j.relationship_id or q["artifact_identity"]!=j.artifact_identity:
  raise EnrollmentError("Courier queue/journal identity disagreement")
 if q["state"]!=j.state:raise EnrollmentError("Courier queue/journal state disagreement")
 if q["sequence"]!=j.delivery_sequence:raise EnrollmentError("Courier queue/journal sequence disagreement")
