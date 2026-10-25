import unittest
from sentinel_forge.campaign_50k import CAMPAIGNS,report
class CampaignLedger50K(unittest.TestCase):
 def test_exact_30000_checkpoints(self):self.assertEqual(30000,report()["checkpoint_count"])
 def test_exact_range(self):self.assertEqual([20001,50000],report()["range"])
 def test_exact_30_campaigns(self):self.assertEqual(30,len(CAMPAIGNS))
 def test_each_campaign_exactly_1000(self):
  for c in CAMPAIGNS:
   with self.subTest(c=c.name):self.assertEqual(1000,c.count)
 def test_contiguous(self):
  n=20001
  for c in CAMPAIGNS:self.assertEqual(n,c.start);n=c.end+1
  self.assertEqual(50001,n)
 def test_each_has_evidence_name(self):
  for c in CAMPAIGNS:
   with self.subTest(c=c.name):self.assertTrue(c.evidence.startswith("test_wp50000_campaign_"))
 def test_never_claims_production(self):self.assertFalse(report()["production_ready"])
 def test_campaign_digest_present(self):self.assertTrue(report()["campaign_digest"].startswith("sha256:"))
