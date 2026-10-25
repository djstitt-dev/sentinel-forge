import unittest
from unittest.mock import patch
from sentinel_forge.acceptance_runner import INVARIANT_TESTS,REQUIRED_OFFLINE,build_report,run_invariant_checks
class AcceptanceIntegrityTests(unittest.TestCase):
 def test_every_required_invariant_has_test_group(self):self.assertEqual(set(REQUIRED_OFFLINE),set(INVARIANT_TESTS))
 def test_no_invariant_has_empty_test_group(self):self.assertTrue(all(INVARIANT_TESTS[x] for x in REQUIRED_OFFLINE))
 def test_groups_are_explicit_test_modules(self):
  for group in INVARIANT_TESTS.values():
   for name in group:self.assertTrue(name.startswith("tests.test_wp6"))
 def test_single_failed_invariant_isolated_in_report(self):
  for name in REQUIRED_OFFLINE:
   with self.subTest(name=name):
    checks={x:True for x in REQUIRED_OFFLINE};checks[name]=False;r=build_report(checks=checks)
    failed=[x for x in r.blockers if x.startswith("OFFLINE_INVARIANT_FAILED:")]
    self.assertEqual([f"OFFLINE_INVARIANT_FAILED:{name}"],failed)
 def test_production_false_by_default(self):self.assertFalse(build_report(checks={x:True for x in REQUIRED_OFFLINE}).production_ready)
 def test_all_explicit_production_facts_required(self):
  base=dict(checks={x:True for x in REQUIRED_OFFLINE},framing_complete=True,protection_provider_complete=True,production_protection_approved=True,production_network_approved=True,assistant_independence_verified=True)
  self.assertTrue(build_report(**base).production_ready)
  for k in tuple(base)[1:]:
   x=dict(base);x[k]=False;self.assertFalse(build_report(**x).production_ready)
