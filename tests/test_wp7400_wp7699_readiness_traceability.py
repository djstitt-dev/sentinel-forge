import unittest
from sentinel_forge.acceptance_runner import REQUIRED_OFFLINE,INVARIANT_TESTS,build_report
class ReadinessTraceability(unittest.TestCase):
 def test_every_required_invariant_has_tests(self):
  self.assertEqual(set(REQUIRED_OFFLINE),set(INVARIANT_TESTS))
  for n in REQUIRED_OFFLINE:
   self.assertTrue(INVARIANT_TESTS[n],n)
 def test_each_offline_invariant_failure_blocks_production(self):
  for n in REQUIRED_OFFLINE:
   checks={x:True for x in REQUIRED_OFFLINE};checks[n]=False;r=build_report(checks=checks,framing_complete=True,protection_provider_complete=True,production_protection_approved=True,production_network_approved=True,assistant_independence_verified=True)
   with self.subTest(n=n):self.assertFalse(r.offline_invariants_passed);self.assertFalse(r.production_ready)
 def test_every_production_fact_individually_required(self):
  facts=("framing_complete","protection_provider_complete","production_protection_approved","production_network_approved","assistant_independence_verified")
  base=dict(checks={x:True for x in REQUIRED_OFFLINE},**{x:True for x in facts})
  for n in facts:
   x=dict(base);x[n]=False
   with self.subTest(n=n):self.assertFalse(build_report(**x).production_ready)
 def test_current_defaults_remain_blocked(self):
  r=build_report(checks={x:True for x in REQUIRED_OFFLINE});self.assertFalse(r.production_ready);self.assertTrue(r.offline_invariants_passed)
 def test_empty_checks_fail_all_offline(self):
  r=build_report(checks={});self.assertFalse(r.offline_invariants_passed);self.assertFalse(r.production_ready)
