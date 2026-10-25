import tempfile,unittest
from pathlib import Path
from sentinel_forge.enrollment import EnrollmentError
from sentinel_forge.transition_intent import TransitionIntentLedger
class TransitionStateExhaustionTests(unittest.TestCase):
 def new(self,td):
  x=TransitionIntentLedger(Path(td)/"i");i=x.prepare(enrollment_id="e",remote_identity="r",from_state="STAGED",to_state="VERIFIED",authorization_reference="a",reason="x");return x,i
 def test_prepared_cannot_commit_directly(self):
  with tempfile.TemporaryDirectory() as td:
   x,i=self.new(td)
   with self.assertRaises(EnrollmentError):x.commit("e",i)
 def test_prepared_can_mutate(self):
  with tempfile.TemporaryDirectory() as td:x,i=self.new(td);x.mark_mutated("e",i);self.assertEqual("MUTATED",x.unresolved("e")["status"])
 def test_prepared_can_abort(self):
  with tempfile.TemporaryDirectory() as td:x,i=self.new(td);x.abort("e",i,authorization_reference="op");self.assertIsNone(x.unresolved("e"))
 def test_mutated_can_commit(self):
  with tempfile.TemporaryDirectory() as td:x,i=self.new(td);x.mark_mutated("e",i);x.commit("e",i);self.assertIsNone(x.unresolved("e"))
 def test_mutated_cannot_mutate_again(self):
  with tempfile.TemporaryDirectory() as td:
   x,i=self.new(td);x.mark_mutated("e",i)
   with self.assertRaises(EnrollmentError):x.mark_mutated("e",i)
 def test_mutated_cannot_abort(self):
  with tempfile.TemporaryDirectory() as td:
   x,i=self.new(td);x.mark_mutated("e",i)
   with self.assertRaises(EnrollmentError):x.abort("e",i,authorization_reference="op")
 def test_aborted_cannot_mutate(self):
  with tempfile.TemporaryDirectory() as td:
   x,i=self.new(td);x.abort("e",i,authorization_reference="op")
   with self.assertRaises(EnrollmentError):x.mark_mutated("e",i)
 def test_aborted_cannot_commit(self):
  with tempfile.TemporaryDirectory() as td:
   x,i=self.new(td);x.abort("e",i,authorization_reference="op")
   with self.assertRaises(EnrollmentError):x.commit("e",i)
 def test_committed_cannot_commit_again(self):
  with tempfile.TemporaryDirectory() as td:
   x,i=self.new(td);x.mark_mutated("e",i);x.commit("e",i)
   with self.assertRaises(EnrollmentError):x.commit("e",i)
