import tempfile,unittest
from pathlib import Path
from sentinel_forge.enrollment import EnrollmentError
from sentinel_forge.recovery_intent import RecoveryIntentLedger
class RecoveryStateExhaustionTests(unittest.TestCase):
 def new(self,td):
  x=RecoveryIntentLedger(Path(td)/"r");i=x.prepare(plan_digest="p",target="t",observation_digest="o");return x,i
 def test_prepared_apply(self):
  with tempfile.TemporaryDirectory() as td:x,i=self.new(td);x.mark_applied("p",i);self.assertEqual("APPLIED",x.unresolved("p")["status"])
 def test_prepared_abort(self):
  with tempfile.TemporaryDirectory() as td:x,i=self.new(td);x.abort("p",i);self.assertIsNone(x.unresolved("p"))
 def test_prepared_cannot_commit(self):
  with tempfile.TemporaryDirectory() as td:
   x,i=self.new(td)
   with self.assertRaises(EnrollmentError):x.commit("p",i)
 def test_applied_commit(self):
  with tempfile.TemporaryDirectory() as td:x,i=self.new(td);x.mark_applied("p",i);x.commit("p",i);self.assertIsNone(x.unresolved("p"))
 def test_applied_cannot_apply(self):
  with tempfile.TemporaryDirectory() as td:
   x,i=self.new(td);x.mark_applied("p",i)
   with self.assertRaises(EnrollmentError):x.mark_applied("p",i)
 def test_applied_cannot_abort(self):
  with tempfile.TemporaryDirectory() as td:
   x,i=self.new(td);x.mark_applied("p",i)
   with self.assertRaises(EnrollmentError):x.abort("p",i)
 def test_aborted_cannot_commit(self):
  with tempfile.TemporaryDirectory() as td:
   x,i=self.new(td);x.abort("p",i)
   with self.assertRaises(EnrollmentError):x.commit("p",i)
 def test_committed_cannot_apply(self):
  with tempfile.TemporaryDirectory() as td:
   x,i=self.new(td);x.mark_applied("p",i);x.commit("p",i)
   with self.assertRaises(EnrollmentError):x.mark_applied("p",i)
