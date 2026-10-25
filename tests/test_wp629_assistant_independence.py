import dataclasses,unittest
from sentinel_forge.assistant_independence import *
from sentinel_forge.enrollment import EnrollmentError

ALL=list(REQUIRED_CATEGORIES)

def clean():
 return build_inventory(forge_identity="sentinel-forge",collector_method="offline-evidence",
  categories_observed=ALL,findings=[])

class AssistantIndependenceTests(unittest.TestCase):
 def test_complete_clean_inventory_passes(self):
  inv=clean();self.assertTrue(assess_independence(inv).passed);require_independent(inv)
 def test_missing_category_fails_closed(self):
  inv=build_inventory(forge_identity="sentinel-forge",collector_method="offline-evidence",
   categories_observed=[x for x in ALL if x!="remote_management"],findings=[])
  with self.assertRaisesRegex(EnrollmentError,"ASSISTANT_INDEPENDENCE_FAILED"):require_independent(inv)
 def test_each_prohibited_residual_class_fails(self):
  for fc in PROHIBITED_FINDING_CLASSES:
   with self.subTest(fc=fc):
    f=InventoryFinding("remote_management",fc,"development-tool",True,"test evidence")
    inv=build_inventory(forge_identity="sentinel-forge",collector_method="offline-evidence",
     categories_observed=ALL,findings=[f])
    self.assertFalse(assess_independence(inv).passed)
 def test_absent_prohibited_finding_does_not_fail(self):
  f=InventoryFinding("credentials","assistant_token","removed-token",False,"confirmed absent")
  inv=build_inventory(forge_identity="sentinel-forge",collector_method="offline-evidence",
   categories_observed=ALL,findings=[f]);self.assertTrue(assess_independence(inv).passed)
 def test_unknown_present_finding_requires_review(self):
  f=InventoryFinding("services","mystery_service","unknown-daemon",True,"ownership unknown")
  inv=build_inventory(forge_identity="sentinel-forge",collector_method="offline-evidence",
   categories_observed=ALL,findings=[f])
  self.assertFalse(assess_independence(inv).passed)
 def test_unknown_category_rejected(self):
  with self.assertRaises(EnrollmentError):
   build_inventory(forge_identity="sentinel-forge",collector_method="offline-evidence",
    categories_observed=ALL+["magic"],findings=[])
 def test_tampering_detected(self):
  inv=clean();bad=dataclasses.replace(inv,forge_identity="other")
  with self.assertRaisesRegex(EnrollmentError,"integrity mismatch"):assess_independence(bad)
 def test_inventory_is_deterministic(self):
  a=clean();b=build_inventory(forge_identity="sentinel-forge",collector_method="offline-evidence",
   categories_observed=list(reversed(ALL)),findings=[])
  self.assertEqual(a,b)
 def test_module_is_evidence_only_not_host_claim(self):
  inv=clean()
  self.assertEqual("offline-evidence",inv.collector_method)
  self.assertNotIn("host_verified",inv.as_dict())

if __name__=="__main__":unittest.main()

class ProductionIndependenceGateTests(unittest.TestCase):
 def test_offline_clean_inventory_alone_is_not_production_evidence(self):
  inv=clean()
  att=build_attestation(inv,verifier_identity="operator",verification_scope="offline-only",
   host_observed=False,development_access_removed=False)
  with self.assertRaisesRegex(EnrollmentError,"host verification evidence required"):
   require_production_independence(inv,att)
 def test_host_observed_but_access_not_removed_is_blocked(self):
  inv=clean()
  att=build_attestation(inv,verifier_identity="operator",verification_scope="host-audit",
   host_observed=True,development_access_removed=False)
  with self.assertRaisesRegex(EnrollmentError,"development access removal not verified"):
   require_production_independence(inv,att)
 def test_production_gate_requires_both_explicit_claims(self):
  inv=clean()
  att=build_attestation(inv,verifier_identity="operator",verification_scope="host-audit",
   host_observed=True,development_access_removed=True)
  require_production_independence(inv,att)
 def test_attestation_is_inventory_bound(self):
  inv=clean()
  att=build_attestation(inv,verifier_identity="operator",verification_scope="host-audit",
   host_observed=True,development_access_removed=True)
  changed=build_inventory(forge_identity="sentinel-forge",collector_method="other-evidence",
   categories_observed=ALL,findings=[])
  with self.assertRaises(EnrollmentError):require_production_independence(changed,att)
