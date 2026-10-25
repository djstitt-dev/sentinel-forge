import itertools,unittest
from sentinel_forge.assistant_independence import *
from sentinel_forge.enrollment import EnrollmentError
C=sorted(REQUIRED_CATEGORIES);P=sorted(PROHIBITED_FINDING_CLASSES)
class IndependenceExhaustion(unittest.TestCase):
 def inv(self,cats=None,findings=()):return build_inventory(forge_identity="forge",collector_method="offline-test",categories_observed=list(C if cats is None else cats),findings=list(findings))
 def test_all_category_presence_masks_only_complete_can_pass(self):
  for bits in itertools.product((False,True),repeat=len(C)):
   cats=[c for c,b in zip(C,bits) if b];a=assess_independence(self.inv(cats))
   with self.subTest(bits=bits):self.assertEqual(all(bits),a.passed)
 def test_every_prohibited_finding_individually_blocks(self):
  for i,p in enumerate(P):
   f=InventoryFinding(C[i%len(C)],p,"id",True,"observed")
   with self.subTest(p=p):self.assertFalse(assess_independence(self.inv(findings=(f,))).passed)
 def test_absent_prohibited_findings_do_not_block(self):
  fs=[InventoryFinding(C[i%len(C)],p,"id"+str(i),False,"not present") for i,p in enumerate(P)]
  self.assertTrue(assess_independence(self.inv(findings=fs)).passed)
 def test_unknown_present_finding_blocks_review(self):
  a=assess_independence(self.inv(findings=(InventoryFinding(C[0],"new-class","id",True,"observed"),)));self.assertFalse(a.passed);self.assertIn("unclassified",a.reasons[0])
 def test_attestation_boolean_matrix_only_both_true_can_produce(self):
  inv=self.inv()
  for host,removed in itertools.product((False,True),repeat=2):
   att=build_attestation(inv,verifier_identity="operator",verification_scope="host",host_observed=host,development_access_removed=removed)
   if host and removed:require_production_independence(inv,att)
   else:
    with self.assertRaises(EnrollmentError):require_production_independence(inv,att)
