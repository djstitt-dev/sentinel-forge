import unittest
import sentinel_forge.api as api

class SafeApiTests(unittest.TestCase):
 def test_exports_are_exact_and_declared(self):
  self.assertEqual(tuple(sorted(api.__all__)),tuple(sorted(n for n in api.__dict__ if not n.startswith("_") and n!="annotations")))
 def test_raw_authority_registries_are_not_exported(self):
  for name in ("EnrollmentRegistry","ChallengeRegistry","RevocationRegistry","EnrollmentStateJournal",
               "TransitionIntentLedger","ReplayRegistry","JournaledEnrollmentLifecycle",
               "GuardedEnrollmentLifecycle","EnrollmentReconciler"):
   self.assertNotIn(name,api.__all__);self.assertFalse(hasattr(api,name),name)
 def test_internal_transition_capabilities_are_not_exported(self):
  for name in ("_ACTIVATION_CAPABILITY","_REMOTE_AUTH_CAPABILITY","_transition_verified_to_active",
               "_mark_remote_authenticated","commit_deferred","stage_deferred","activate_deferred"):
   self.assertNotIn(name,api.__all__);self.assertFalse(hasattr(api,name),name)
 def test_test_only_crypto_is_not_exported(self):
  for name in ("TestOnlyHMACSigner","TestOnlyHMACVerifier"):
   self.assertNotIn(name,api.__all__);self.assertFalse(hasattr(api,name),name)
 def test_no_production_network_or_effect_implementation_is_exported(self):
  for name in ("Transport","SimulatedTransport","DisconnectedTransport","DurableEffectCoordinator",
               "DisconnectedCourier","SQLiteCourier"):
   self.assertNotIn(name,api.__all__);self.assertFalse(hasattr(api,name),name)
 def test_safe_high_level_authority_surfaces_are_exported(self):
  for name in ("AuditedEnrollmentLifecycle","AuditedEnrollmentReconciler",
               "CredentialReferenceRegistry","accept_transport_message",
               "require_production_independence"):
   self.assertIn(name,api.__all__);self.assertTrue(hasattr(api,name),name)
 def test_api_module_has_no_wildcard_dynamic_escape_hatch(self):
  self.assertNotIn("__getattr__",api.__dict__)
  self.assertNotIn("__dir__",api.__dict__)

if __name__=="__main__":unittest.main()

class SafeApiSourceBoundaryTests(unittest.TestCase):
 def test_api_source_does_not_import_raw_authority_modules(self):
  from pathlib import Path
  src=Path(api.__file__).read_text()
  for module in (".enrollment_lifecycle import GuardedEnrollmentLifecycle",
                 ".journaled_lifecycle import JournaledEnrollmentLifecycle",
                 ".transition_intent import TransitionIntentLedger",
                 ".enrollment_state import EnrollmentStateJournal",
                 ".enrollment_session import ChallengeRegistry",
                 ".revocation import RevocationRegistry",
                 ".reconciliation import EnrollmentReconciler",
                 ".authenticity import TestOnlyHMAC"):
   self.assertNotIn(module,src)
 def test_api_source_has_no_dynamic_import_or_star_import(self):
  from pathlib import Path
  src=Path(api.__file__).read_text()
  self.assertNotIn("importlib",src);self.assertNotIn(" import *",src)
