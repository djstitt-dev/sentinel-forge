import unittest
from sentinel_forge.activation_plan import ACTIVATION_ACTIONS,activation_plan,shutdown_plan,require_activation_order
from sentinel_forge.backup_contract import build_backup_manifest,require_restore_identity
from sentinel_forge.enrollment import EnrollmentError
from sentinel_forge.production_config import build_production_config
from sentinel_forge.watchtower_telemetry import build_telemetry

class ProductionContractTests(unittest.TestCase):
 def test_config_is_born_disabled(self):
  c=build_production_config(peer_identity="reaper",peer_role="reaper",endpoint_reference="endpoint:r",credential_reference="cred:r",protection_provider_reference="protect:approved",network_provider_reference="network:approved",policy_reference="policy:1")
  self.assertFalse(c.enabled)
 def test_config_rejects_secret_and_enabled(self):
  base=dict(peer_identity="r",peer_role="reaper",endpoint_reference="e",credential_reference="c",protection_provider_reference="p",network_provider_reference="n",policy_reference="x")
  with self.assertRaises(EnrollmentError):build_production_config(**base,secret="x")
  with self.assertRaises(EnrollmentError):build_production_config(**base,enabled=True)
 def test_activation_exact_order_and_operator_gate(self):
  p=activation_plan();self.assertEqual(ACTIVATION_ACTIONS,tuple(x.action for x in p));self.assertTrue(next(x for x in p if x.action=="OPERATOR_APPROVAL").requires_operator_approval);require_activation_order(ACTIVATION_ACTIONS)
 def test_activation_reordering_fails(self):
  with self.assertRaises(EnrollmentError):require_activation_order(reversed(ACTIVATION_ACTIONS))
 def test_shutdown_preserves_inflight_before_disable(self):
  a=[x.action for x in shutdown_plan()];self.assertLess(a.index("PRESERVE_IN_FLIGHT_STATE"),a.index("DISABLE_TRANSPORT"))
 def test_backup_excludes_secrets_and_binds_relationship(self):
  m=build_backup_manifest(relationship_id="rel",queue_digest="q",delivery_journal_digest="j",evidence_digest="e",credential_reference_digest="c")
  require_restore_identity(m,expected_relationship_id="rel")
  with self.assertRaises(EnrollmentError):require_restore_identity(m,expected_relationship_id="other")
  with self.assertRaises(EnrollmentError):build_backup_manifest(relationship_id="rel",queue_digest="q",delivery_journal_digest="j",evidence_digest="e",credential_reference_digest="c",includes_secret_material=True)
 def test_watchtower_telemetry_excludes_payloads(self):
  t=build_telemetry(relationship_id="rel",peer_identity="reaper",event_type="DELIVERY",outcome="BLOCKED",reason="revoked",sequence=1,correlation_id="c");self.assertEqual("reaper",t.peer_identity)
  with self.assertRaisesRegex(EnrollmentError,"forbidden"):build_telemetry(relationship_id="rel",peer_identity="reaper",event_type="x",outcome="x",reason="x",sequence=1,correlation_id="c",payload="secret")
