import unittest
from sentinel_forge.courier_acceptance import REQUIRED_OFFLINE,assess_courier_acceptance
from sentinel_forge.readiness_report import build_readiness_report
from sentinel_forge.transport_health import assess_transport_health
class ReadinessTests(unittest.TestCase):
 def acceptance(self,prod=False):
  return assess_courier_acceptance(checks={x:True for x in REQUIRED_OFFLINE},framing_complete=prod,protection_provider_complete=prod,production_protection_approved=prod,production_network_approved=prod,assistant_independence_verified=prod)
 def health(self,known=True):
  return assess_transport_health(relationship_active=True,revoked=False,current_credential=True,current_session=True,queue_consistent=True,audit_available=True,unresolved_effect=False,provider_available=True,last_probe_known=known)
 def test_current_architecture_can_be_offline_ready_but_prod_blocked(self):
  r=build_readiness_report(acceptance=self.acceptance(False),health=self.health(),compatibility_valid=True,configuration_valid=True,activation_plan_valid=True,backup_contract_valid=True,telemetry_contract_valid=True)
  self.assertTrue(r.offline_ready);self.assertFalse(r.production_ready);self.assertIn("WP6.36_FRAMING_INCOMPLETE",r.blockers)
 def test_unknown_health_blocks_production(self):
  r=build_readiness_report(acceptance=self.acceptance(True),health=self.health(False),compatibility_valid=True,configuration_valid=True,activation_plan_valid=True,backup_contract_valid=True,telemetry_contract_valid=True)
  self.assertFalse(r.production_ready);self.assertIn("TRANSPORT_HEALTH_UNKNOWN",r.blockers)
 def test_all_proven_gates_can_be_ready(self):
  r=build_readiness_report(acceptance=self.acceptance(True),health=self.health(),compatibility_valid=True,configuration_valid=True,activation_plan_valid=True,backup_contract_valid=True,telemetry_contract_valid=True)
  self.assertTrue(r.offline_ready);self.assertTrue(r.production_ready);self.assertEqual((),r.blockers)
 def test_contract_failure_blocks_offline_readiness(self):
  r=build_readiness_report(acceptance=self.acceptance(True),health=self.health(),compatibility_valid=False,configuration_valid=True,activation_plan_valid=True,backup_contract_valid=True,telemetry_contract_valid=True)
  self.assertFalse(r.offline_ready);self.assertIn("COMPATIBILITY_POLICY_INVALID",r.blockers)
