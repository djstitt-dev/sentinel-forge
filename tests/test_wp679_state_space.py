import itertools,json,tempfile,unittest
from pathlib import Path
from sentinel_forge.courier_queue import CourierQueue,STATES
from sentinel_forge.delivery_journal import ALLOWED,DeliveryJournal
from sentinel_forge.enrollment import EnrollmentError

LEGAL={(a,b) for a,bs in ALLOWED.items() for b in bs if a is not None}
class StateSpaceTests(unittest.TestCase):
 def test_queue_transition_matrix_exact(self):
  for a,b in itertools.product(STATES,STATES):
   with self.subTest(a=a,b=b),tempfile.TemporaryDirectory() as td:
    q=CourierQueue(Path(td)/"q");i=q.enqueue(relationship_id="r",artifact_identity="a",operation="d",payload_identity="p")
    # Materialize source state only through legal paths.
    paths={"QUEUED":[],"CANCELLED":[("QUEUED","CANCELLED")],"PREPARED":[("QUEUED","PREPARED")],
     "IN_FLIGHT":[("QUEUED","PREPARED"),("PREPARED","IN_FLIGHT")],
     "OUTCOME_UNKNOWN":[("QUEUED","PREPARED"),("PREPARED","IN_FLIGHT"),("IN_FLIGHT","OUTCOME_UNKNOWN")],
     "REJECTED":[("QUEUED","PREPARED"),("PREPARED","IN_FLIGHT"),("IN_FLIGHT","REJECTED")],
     "ACKNOWLEDGED":[("QUEUED","PREPARED"),("PREPARED","IN_FLIGHT"),("IN_FLIGHT","ACKNOWLEDGED")]}
    for x,y in paths[a]:q.transition(i,expected=x,new=y,sequence=1,acknowledgement="ack" if y=="ACKNOWLEDGED" else None)
    kwargs={"sequence":1}
    if b=="ACKNOWLEDGED":kwargs["acknowledgement"]="ack"
    if (a,b) in LEGAL:
     q.transition(i,expected=a,new=b,**kwargs);self.assertEqual(b,q.get(i)["state"])
    else:
     with self.assertRaises(EnrollmentError):q.transition(i,expected=a,new=b,**kwargs)
 def test_persisted_item_id_tamper_fails(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"q";q=CourierQueue(p);i=q.enqueue(relationship_id="r",artifact_identity="a",operation="d",payload_identity="p")
   db=json.loads(p.read_text());db[i]["artifact_identity"]="evil";p.write_text(json.dumps(db))
   with self.assertRaisesRegex(EnrollmentError,"identity integrity"):CourierQueue(p)
 def test_persisted_sequence_state_mismatch_fails(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"q";q=CourierQueue(p);i=q.enqueue(relationship_id="r",artifact_identity="a",operation="d",payload_identity="p")
   db=json.loads(p.read_text());db[i]["sequence"]=1;p.write_text(json.dumps(db))
   with self.assertRaisesRegex(EnrollmentError,"sequence/state"):CourierQueue(p)
