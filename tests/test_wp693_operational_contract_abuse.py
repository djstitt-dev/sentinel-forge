import unittest
from sentinel_forge.activation_plan import ACTIVATION_ACTIONS,require_activation_order
from sentinel_forge.backup_contract import build_backup_manifest
from sentinel_forge.enrollment import EnrollmentError
from sentinel_forge.production_config import build_production_config
from sentinel_forge.watchtower_telemetry import build_telemetry
class OperationalContractAbuseTests(unittest.TestCase):
 def test_each_adjacent_activation_swap_fails(self):
  for i in range(len(ACTIVATION_ACTIONS)-1):
   with self.subTest(i=i):
    x=list(ACTIVATION_ACTIONS);x[i],x[i+1]=x[i+1],x[i]
    with self.assertRaises(EnrollmentError):require_activation_order(x)
 def test_activation_missing_step_fails(self):
  with self.assertRaises(EnrollmentError):require_activation_order(ACTIVATION_ACTIONS[:-1])
 def test_activation_duplicate_step_fails(self):
  with self.assertRaises(EnrollmentError):require_activation_order(ACTIVATION_ACTIONS+(ACTIVATION_ACTIONS[-1],))
 def test_each_forbidden_config_secret_field_fails(self):
  base=dict(peer_identity="r",peer_role="reaper",endpoint_reference="e",credential_reference="c",protection_provider_reference="p",network_provider_reference="n",policy_reference="x")
  for f in ("secret","password","token","private_key","key_material","credential_material"):
   with self.subTest(f=f):
    with self.assertRaises(EnrollmentError):build_production_config(**base,**{f:"x"})
 def test_each_forbidden_telemetry_field_fails(self):
  base=dict(relationship_id="r",peer_identity="p",event_type="e",outcome="o",reason="x",correlation_id="c")
  for f in ("payload","secret","password","token","private_key","key_material","ciphertext"):
   with self.subTest(f=f):
    with self.assertRaises(EnrollmentError):build_telemetry(**base,**{f:"x"})
 def test_backup_secret_flag_fails(self):
  with self.assertRaises(EnrollmentError):build_backup_manifest(relationship_id="r",queue_digest="q",delivery_journal_digest="j",evidence_digest="e",credential_reference_digest="c",includes_secret_material=True)
