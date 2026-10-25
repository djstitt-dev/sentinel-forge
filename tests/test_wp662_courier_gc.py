import tempfile,unittest
from pathlib import Path
from sentinel_forge.courier_gc import plan_gc,require_gc_safe
from sentinel_forge.courier_queue import CourierQueue
from sentinel_forge.delivery_journal import DeliveryJournal
from sentinel_forge.enrollment import EnrollmentError

class GCTests(unittest.TestCase):
 def setUp(self):self.td=tempfile.TemporaryDirectory();r=Path(self.td.name);self.q=CourierQueue(r/"q");self.j=DeliveryJournal(r/"j")
 def tearDown(self):self.td.cleanup()
 def seed(self,n):
  i=self.q.enqueue(relationship_id="r",artifact_identity=f"a{n}",operation="d",payload_identity=f"p{n}")
  self.j.append(item_id=i,relationship_id="r",delivery_sequence=None,prior_state=None,state="QUEUED",artifact_identity=f"a{n}",reason="q");return i
 def finish(self,i,n):
  for a,b in (("QUEUED","PREPARED"),("PREPARED","IN_FLIGHT"),("IN_FLIGHT","REJECTED")):
   self.q.transition(i,expected=a,new=b,sequence=1);self.j.append(item_id=i,relationship_id="r",delivery_sequence=1,prior_state=a,state=b,artifact_identity=f"a{n}",reason=b)
 def test_only_terminal_consistent_is_removable(self):
  a=self.seed(1);b=self.seed(2);self.finish(a,1);p=plan_gc(self.q,self.j);self.assertIn(a,p.removable);self.assertIn(b,p.retained)
 def test_limit_is_bounded(self):
  ids=[]
  for n in range(3):i=self.seed(n);self.finish(i,n);ids.append(i)
  self.assertEqual(2,len(plan_gc(self.q,self.j,max_remove=2).removable))
 def test_unknown_not_removable(self):
  i=self.seed(1);self.q.transition(i,expected="QUEUED",new="PREPARED",sequence=1);self.j.append(item_id=i,relationship_id="r",delivery_sequence=1,prior_state="QUEUED",state="PREPARED",artifact_identity="a1",reason="p");self.q.transition(i,expected="PREPARED",new="IN_FLIGHT",sequence=1);self.j.append(item_id=i,relationship_id="r",delivery_sequence=1,prior_state="PREPARED",state="IN_FLIGHT",artifact_identity="a1",reason="i");self.q.transition(i,expected="IN_FLIGHT",new="OUTCOME_UNKNOWN",sequence=1);self.j.append(item_id=i,relationship_id="r",delivery_sequence=1,prior_state="IN_FLIGHT",state="OUTCOME_UNKNOWN",artifact_identity="a1",reason="u")
  with self.assertRaises(EnrollmentError):require_gc_safe(self.q,self.j,i)
 def test_disagreement_not_removable(self):
  i=self.seed(1);self.q.transition(i,expected="QUEUED",new="CANCELLED")
  self.assertIn(i,plan_gc(self.q,self.j).retained)
