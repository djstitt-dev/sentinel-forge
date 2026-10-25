import json,tempfile,unittest
from pathlib import Path
from sentinel_forge.courier_queue import CourierQueue
from sentinel_forge.courier_recovery import classify_delivery_recovery
from sentinel_forge.delivery_journal import DeliveryJournal
class RestartSkewTests(unittest.TestCase):
 def base(self,td):
  r=Path(td);q=CourierQueue(r/"q");j=DeliveryJournal(r/"j");i=q.enqueue(relationship_id="r",artifact_identity="a",operation="d",payload_identity="p");j.append(item_id=i,relationship_id="r",delivery_sequence=None,prior_state=None,state="QUEUED",artifact_identity="a",reason="q");q.transition(i,expected="QUEUED",new="PREPARED",sequence=1);j.append(item_id=i,relationship_id="r",delivery_sequence=1,prior_state="QUEUED",state="PREPARED",artifact_identity="a",reason="p");return r,q,j,i
 def test_queue_sequence_skew_reconcile(self):
  with tempfile.TemporaryDirectory() as td:
   r,q,j,i=self.base(td);db=json.loads(q.path.read_text());db[i]["sequence"]=2;q.path.write_text(json.dumps(db));self.assertEqual("RECONCILIATION_REQUIRED",classify_delivery_recovery(q,j,i).classification)
 def test_queue_artifact_corruption_operator(self):
  with tempfile.TemporaryDirectory() as td:
   r,q,j,i=self.base(td);db=json.loads(q.path.read_text());db[i]["artifact_identity"]="evil";q.path.write_text(json.dumps(db));self.assertEqual("OPERATOR_REQUIRED",classify_delivery_recovery(q,j,i).classification)
 def test_terminal_queue_ahead_reconcile(self):
  with tempfile.TemporaryDirectory() as td:
   r,q,j,i=self.base(td);q.transition(i,expected="PREPARED",new="IN_FLIGHT",sequence=1);j.append(item_id=i,relationship_id="r",delivery_sequence=1,prior_state="PREPARED",state="IN_FLIGHT",artifact_identity="a",reason="i");q.transition(i,expected="IN_FLIGHT",new="REJECTED",sequence=1);self.assertEqual("RECONCILIATION_REQUIRED",classify_delivery_recovery(q,j,i).classification)
 def test_terminal_journal_ahead_reconcile(self):
  with tempfile.TemporaryDirectory() as td:
   r,q,j,i=self.base(td);q.transition(i,expected="PREPARED",new="IN_FLIGHT",sequence=1);j.append(item_id=i,relationship_id="r",delivery_sequence=1,prior_state="PREPARED",state="IN_FLIGHT",artifact_identity="a",reason="i");j.append(item_id=i,relationship_id="r",delivery_sequence=1,prior_state="IN_FLIGHT",state="REJECTED",artifact_identity="a",reason="r");self.assertEqual("RECONCILIATION_REQUIRED",classify_delivery_recovery(q,j,i).classification)
