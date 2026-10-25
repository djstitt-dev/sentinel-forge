import unittest
from sentinel_forge.courier_completion import *
from sentinel_forge.enrollment import EnrollmentError
class CourierCompletionTests(unittest.TestCase):
 def facts(self,n,v=True):return {x:v for x in n}
 def test_forge_implementation_can_be_complete_while_activation_blocked(self):
  i=self.facts(IMPLEMENTATION_GATES);a=self.facts(ACTIVATION_GATES);o=self.facts(OPERATIONAL_GATES)
  for k in a:a[k]=False
  for k in o:o[k]=False
  r=assess_completion(implementation_facts=i,activation_facts=a,operational_facts=o)
  self.assertTrue(r.implementation_complete);self.assertFalse(r.activation_ready);self.assertFalse(r.operational)
 def test_activation_requires_implementation(self):
  i=self.facts(IMPLEMENTATION_GATES);i["FRAMING_IMPLEMENTED"]=False
  r=assess_completion(implementation_facts=i,activation_facts=self.facts(ACTIVATION_GATES),operational_facts=self.facts(OPERATIONAL_GATES))
  self.assertFalse(r.activation_ready);self.assertIn("IMPLEMENTATION_INCOMPLETE",r.activation_blockers)
 def test_operational_requires_activation(self):
  a=self.facts(ACTIVATION_GATES);a["PRODUCTION_NETWORK_APPROVED"]=False
  r=assess_completion(implementation_facts=self.facts(IMPLEMENTATION_GATES),activation_facts=a,operational_facts=self.facts(OPERATIONAL_GATES))
  self.assertFalse(r.operational);self.assertIn("ACTIVATION_NOT_READY",r.operational_blockers)
 def test_all_true_is_operational(self):
  r=assess_completion(implementation_facts=self.facts(IMPLEMENTATION_GATES),activation_facts=self.facts(ACTIVATION_GATES),operational_facts=self.facts(OPERATIONAL_GATES))
  self.assertTrue(r.implementation_complete);self.assertTrue(r.activation_ready);self.assertTrue(r.operational)
 def test_missing_extra_nonbool_fail_closed(self):
  i=self.facts(IMPLEMENTATION_GATES);a=self.facts(ACTIVATION_GATES);o=self.facts(OPERATIONAL_GATES)
  for bad in ({},i|{"X":True},i|{"FRAMING_IMPLEMENTED":"true"}):
   with self.assertRaises(EnrollmentError):assess_completion(implementation_facts=bad,activation_facts=a,operational_facts=o)
class CompletionRunnerTests(unittest.TestCase):
 def test_runner_derives_all_module_and_invariant_gates(self):
  from sentinel_forge.courier_completion_runner import derive_implementation_facts
  f=derive_implementation_facts(full_regression_passed=True)
  self.assertEqual(set(IMPLEMENTATION_GATES),set(f));self.assertTrue(all(f.values()))
 def test_runner_does_not_invent_regression_success(self):
  from sentinel_forge.courier_completion_runner import current_report
  r=current_report(full_regression_passed=False)
  self.assertFalse(r.implementation_complete);self.assertIn("FULL_REGRESSION_PASS",r.implementation_blockers)
