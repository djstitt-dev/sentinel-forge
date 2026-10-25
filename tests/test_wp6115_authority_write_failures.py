import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from sentinel_forge.recovery_intent import RecoveryIntentLedger
from sentinel_forge.revocation import RevocationRegistry,make_revocation
from sentinel_forge.transition_intent import TransitionIntentLedger
class AuthorityWriteFailureTests(unittest.TestCase):
 def test_transition_replace_failure_preserves_prior(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"i";x=TransitionIntentLedger(p);i=x.prepare(enrollment_id="e",remote_identity="r",from_state="S",to_state="V",authorization_reference="a",reason="x")
   with patch("pathlib.Path.replace",side_effect=OSError("full")):
    with self.assertRaises(OSError):x.mark_mutated("e",i)
   self.assertEqual("PREPARED",TransitionIntentLedger(p).unresolved("e")["status"])
 def test_transition_fsync_failure_not_success(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"i";x=TransitionIntentLedger(p);i=x.prepare(enrollment_id="e",remote_identity="r",from_state="S",to_state="V",authorization_reference="a",reason="x")
   with patch("sentinel_forge.transition_intent.os.fsync",side_effect=OSError("full")):
    with self.assertRaises(OSError):x.mark_mutated("e",i)
 def test_recovery_replace_failure_preserves_prior(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"r";x=RecoveryIntentLedger(p);i=x.prepare(plan_digest="p",target="t",observation_digest="o")
   with patch("pathlib.Path.replace",side_effect=OSError("full")):
    with self.assertRaises(OSError):x.mark_applied("p",i)
   self.assertEqual("PREPARED",RecoveryIntentLedger(p).unresolved("p")["status"])
 def test_recovery_fsync_failure_not_success(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"r";x=RecoveryIntentLedger(p);i=x.prepare(plan_digest="p",target="t",observation_digest="o")
   with patch("sentinel_forge.recovery_intent.os.fsync",side_effect=OSError("full")):
    with self.assertRaises(OSError):x.mark_applied("p",i)
 def test_revocation_replace_failure_does_not_revoke(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"r";x=RevocationRegistry(p);rec=make_revocation(enrollment_id="e",remote_identity="r",operator_authorization_reference="a",reason="x",prior_state="ACTIVE")
   with patch("pathlib.Path.replace",side_effect=OSError("full")):
    with self.assertRaises(OSError):x.revoke(rec)
   self.assertFalse(RevocationRegistry(p).is_revoked("e"))
 def test_revocation_fsync_failure_not_success(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"r";x=RevocationRegistry(p);rec=make_revocation(enrollment_id="e",remote_identity="r",operator_authorization_reference="a",reason="x",prior_state="ACTIVE")
   with patch("sentinel_forge.revocation.os.fsync",side_effect=OSError("full")):
    with self.assertRaises(OSError):x.revoke(rec)
