import json,unittest
from unittest.mock import patch
from sentinel_forge.acceptance_runner import REQUIRED_OFFLINE,build_report,main,run_invariant_checks
class AcceptanceRunnerTests(unittest.TestCase):
 def test_real_security_suite_passes(self):self.assertTrue(all(run_invariant_checks().values()))
 def test_passed_offline_tests_do_not_claim_production(self):
  r=build_report(tests_passed=True);self.assertTrue(r.offline_invariants_passed);self.assertFalse(r.production_ready);self.assertIn("WP6.36_FRAMING_INCOMPLETE",r.blockers)
 def test_failed_suite_fails_every_offline_invariant(self):
  r=build_report(tests_passed=False);self.assertFalse(r.offline_invariants_passed);self.assertEqual(13,sum(x.startswith("OFFLINE_INVARIANT_FAILED:") for x in r.blockers))
 def test_cli_exit_tracks_offline_not_production(self):
  with patch("sentinel_forge.acceptance_runner.run_invariant_checks",return_value={x:True for x in REQUIRED_OFFLINE}):self.assertEqual(0,main([]))
  with patch("sentinel_forge.acceptance_runner.run_invariant_checks",return_value={x:False for x in REQUIRED_OFFLINE}):self.assertEqual(1,main([]))
