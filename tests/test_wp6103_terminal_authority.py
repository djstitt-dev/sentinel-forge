import tempfile,unittest
from pathlib import Path
from sentinel_forge.enrollment import EnrollmentError
from sentinel_forge.recovery_intent import RecoveryIntentLedger
from sentinel_forge.transition_intent import TransitionIntentLedger
class TerminalAuthorityTests(unittest.TestCase):
 def test_recovery_committed_cannot_apply_again(self):
  with tempfile.TemporaryDirectory() as td:
   x=RecoveryIntentLedger(Path(td)/"r");i=x.prepare(plan_digest="p",target="t",observation_digest="o");x.mark_applied("p",i);x.commit("p",i)
   with self.assertRaises(EnrollmentError):x.mark_applied("p",i)
 def test_recovery_committed_cannot_abort(self):
  with tempfile.TemporaryDirectory() as td:
   x=RecoveryIntentLedger(Path(td)/"r");i=x.prepare(plan_digest="p",target="t",observation_digest="o");x.mark_applied("p",i);x.commit("p",i)
   with self.assertRaises(EnrollmentError):x.abort("p",i)
 def test_recovery_aborted_cannot_apply(self):
  with tempfile.TemporaryDirectory() as td:
   x=RecoveryIntentLedger(Path(td)/"r");i=x.prepare(plan_digest="p",target="t",observation_digest="o");x.abort("p",i)
   with self.assertRaises(EnrollmentError):x.mark_applied("p",i)
 def test_transition_committed_cannot_mutate(self):
  with tempfile.TemporaryDirectory() as td:
   x=TransitionIntentLedger(Path(td)/"i");i=x.prepare(enrollment_id="e",remote_identity="r",from_state="STAGED",to_state="VERIFIED",authorization_reference="a",reason="x");x.mark_mutated("e",i);x.commit("e",i)
   with self.assertRaises(EnrollmentError):x.mark_mutated("e",i)
 def test_transition_committed_cannot_abort(self):
  with tempfile.TemporaryDirectory() as td:
   x=TransitionIntentLedger(Path(td)/"i");i=x.prepare(enrollment_id="e",remote_identity="r",from_state="STAGED",to_state="VERIFIED",authorization_reference="a",reason="x");x.mark_mutated("e",i);x.commit("e",i)
   with self.assertRaises(EnrollmentError):x.abort("e",i,authorization_reference="reconcile")
 def test_transition_wrong_intent_id_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   x=TransitionIntentLedger(Path(td)/"i");i=x.prepare(enrollment_id="e",remote_identity="r",from_state="STAGED",to_state="VERIFIED",authorization_reference="a",reason="x")
   with self.assertRaises(EnrollmentError):x.commit("e","intent:wrong")
