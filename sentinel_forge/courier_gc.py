"""Conservative bounded Courier garbage-collection planning."""
from dataclasses import dataclass
from .enrollment import EnrollmentError

TERMINAL=frozenset({"ACKNOWLEDGED","REJECTED","CANCELLED"})

@dataclass(frozen=True)
class GarbageCollectionPlan:
 removable:tuple[str,...]
 retained:tuple[str,...]
 reason:str

def plan_gc(queue,journal,*,max_remove:int=128)->GarbageCollectionPlan:
 if not isinstance(max_remove,int) or isinstance(max_remove,bool) or max_remove<1:
  raise EnrollmentError("Courier GC max_remove must be positive")
 events=journal.verify()
 latest={}
 for e in events:latest[e.item_id]=e
 removable=[];retained=[]
 # Journal order provides deterministic oldest-first consideration.
 seen=set()
 for e in events:
  if e.item_id in seen:continue
  seen.add(e.item_id);last=latest[e.item_id];q=queue.get(e.item_id)
  if q is None:retained.append(e.item_id);continue
  consistent=(q["state"]==last.state and q["relationship_id"]==last.relationship_id and
              q["artifact_identity"]==last.artifact_identity and q["sequence"]==last.delivery_sequence)
  if consistent and q["state"] in TERMINAL and len(removable)<max_remove:removable.append(e.item_id)
  else:retained.append(e.item_id)
 return GarbageCollectionPlan(tuple(removable),tuple(retained),"terminal-consistent-only")

def require_gc_safe(queue,journal,item_id:str)->None:
 plan=plan_gc(queue,journal,max_remove=4096)
 if item_id not in plan.removable:raise EnrollmentError("Courier record is not safe for garbage collection")
