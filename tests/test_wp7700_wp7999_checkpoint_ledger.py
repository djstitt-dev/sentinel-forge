import unittest
from sentinel_forge.checkpoint_ledger import BANDS,report
class LedgerTests(unittest.TestCase):
 def test_exact_1000_checkpoints(self):self.assertEqual(1000,report()["checkpoint_count"])
 def test_exact_range(self):self.assertEqual([1001,2000],report()["range"])
 def test_bands_contiguous(self):
  expected=1001
  for b in BANDS:self.assertEqual(expected,b.start);self.assertGreaterEqual(b.end,b.start);expected=b.end+1
  self.assertEqual(2001,expected)
 def test_each_band_has_evidence(self):
  for b in BANDS:
   with self.subTest(b=b.name):self.assertTrue(b.evidence);self.assertEqual("PASS",b.status)
 def test_ledger_never_claims_production(self):self.assertFalse(report()["production_ready"])
 def test_note_distinguishes_checkpoint_from_test_method(self):self.assertIn("not unittest-method count",report()["note"])
