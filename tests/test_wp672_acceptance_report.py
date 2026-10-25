import json,unittest
from sentinel_forge.courier_acceptance import REQUIRED_OFFLINE,assess_courier_acceptance
class AcceptanceReportTests(unittest.TestCase):
 def checks(self):return {x:True for x in REQUIRED_OFFLINE}
 def test_offline_pass_can_still_be_production_blocked(self):
  r=assess_courier_acceptance(checks=self.checks(),framing_complete=False,protection_provider_complete=False,production_protection_approved=False,production_network_approved=False,assistant_independence_verified=False)
  self.assertTrue(r.offline_invariants_passed);self.assertFalse(r.production_ready);self.assertIn("WP6.36_FRAMING_INCOMPLETE",r.blockers)
 def test_missing_invariant_is_explicit(self):
  c=self.checks();c["ACK_BINDING"]=False;r=assess_courier_acceptance(checks=c,framing_complete=True,protection_provider_complete=True,production_protection_approved=True,production_network_approved=True,assistant_independence_verified=True)
  self.assertFalse(r.offline_invariants_passed);self.assertIn("OFFLINE_INVARIANT_FAILED:ACK_BINDING",r.blockers)
 def test_all_gates_can_report_ready(self):
  r=assess_courier_acceptance(checks=self.checks(),framing_complete=True,protection_provider_complete=True,production_protection_approved=True,production_network_approved=True,assistant_independence_verified=True)
  self.assertTrue(r.production_ready);self.assertEqual((),r.blockers)
 def test_json_is_deterministic(self):
  r=assess_courier_acceptance(checks=self.checks(),framing_complete=False,protection_provider_complete=False,production_protection_approved=False,production_network_approved=False,assistant_independence_verified=False)
  self.assertEqual(r.to_json(),r.to_json());self.assertFalse(json.loads(r.to_json())["production_ready"])
