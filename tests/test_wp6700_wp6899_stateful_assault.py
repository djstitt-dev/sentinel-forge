import random,tempfile,unittest
from pathlib import Path
from sentinel_forge.courier_queue_v2 import IntentCourierQueue,FINAL
from sentinel_forge.delivery_intent import build_delivery_intent
from sentinel_forge.enrollment import EnrollmentError
LEGAL={"QUEUED":("PREPARED","CANCELLED"),"PREPARED":("IN_FLIGHT",),"IN_FLIGHT":("ACKNOWLEDGED","REJECTED","OUTCOME_UNKNOWN"),"OUTCOME_UNKNOWN":("ACKNOWLEDGED","REJECTED")}
class StatefulAssault(unittest.TestCase):
 def test_100_seed_queue_state_walks(self):
  for seed in range(100):
   with self.subTest(seed=seed),tempfile.TemporaryDirectory() as td:
    rng=random.Random(seed);q=IntentCourierQueue(Path(td)/"q");it=build_delivery_intent(correlation_id=f"c{seed}",relationship_id="r",artifact_identity="sha256:a",operation="d",authorization_reference="a");item=q.enqueue(intent=it,payload_identity="sha256:a");state="QUEUED";seq=None
    for _ in range(20):
     if state in FINAL:break
     legal=LEGAL[state];new=rng.choice(legal);use=1 if new not in ("CANCELLED",) else None;ack="ack" if new=="ACKNOWLEDGED" else None
     q.transition(item,expected=state,new=new,sequence=use,acknowledgement=ack);state=new
     self.assertEqual(state,IntentCourierQueue(Path(td)/"q").get(item)["state"])
 def test_100_seed_illegal_transition_attempts_never_mutate(self):
  states=("QUEUED","PREPARED","IN_FLIGHT","OUTCOME_UNKNOWN","ACKNOWLEDGED","REJECTED","CANCELLED")
  for seed in range(100):
   with self.subTest(seed=seed),tempfile.TemporaryDirectory() as td:
    q=IntentCourierQueue(Path(td)/"q");it=build_delivery_intent(correlation_id=f"c{seed}",relationship_id="r",artifact_identity="sha256:a",operation="d",authorization_reference="a");item=q.enqueue(intent=it,payload_identity="sha256:a");before=q.get(item)
    rng=random.Random(seed);a=rng.choice(states);b=rng.choice(states)
    if (a,b) in {(x,y) for x,ys in LEGAL.items() for y in ys}:continue
    with self.assertRaises(EnrollmentError):q.transition(item,expected=a,new=b,sequence=1,acknowledgement="ack")
    self.assertEqual(before,q.get(item))
