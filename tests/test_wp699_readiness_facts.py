import unittest
from sentinel_forge.enrollment import EnrollmentError
from sentinel_forge.readiness_facts import REQUIRED,derive_contract_facts,fact
class ReadinessFactsTests(unittest.TestCase):
 def facts(self):return [fact(name=x,satisfied=True,source="offline-test",observed=True) for x in REQUIRED]
 def test_complete_observed_set_derives(self):self.assertTrue(all(derive_contract_facts(self.facts()).values()))
 def test_unobserved_fact_rejected(self):
  fs=self.facts();fs[0]=fact(name=fs[0].name,satisfied=True,source="claim",observed=False)
  with self.assertRaisesRegex(EnrollmentError,"unobserved"):derive_contract_facts(fs)
 def test_missing_fact_rejected(self):
  with self.assertRaises(EnrollmentError):derive_contract_facts(self.facts()[:-1])
 def test_extra_fact_rejected(self):
  with self.assertRaises(EnrollmentError):derive_contract_facts(self.facts()+[fact(name="extra",satisfied=True,source="x",observed=True)])
 def test_duplicate_fact_rejected(self):
  fs=self.facts();fs.append(fs[0])
  with self.assertRaises(EnrollmentError):derive_contract_facts(fs)
 def test_failed_observed_fact_stays_false(self):
  fs=self.facts();fs[0]=fact(name=fs[0].name,satisfied=False,source="offline-test",observed=True);self.assertFalse(derive_contract_facts(fs)[fs[0].name])
 def test_fact_requires_real_booleans(self):
  with self.assertRaises(EnrollmentError):fact(name="x",satisfied=1,source="x",observed=True)
 def test_fact_requires_source(self):
  with self.assertRaises(EnrollmentError):fact(name="x",satisfied=True,source="",observed=True)
