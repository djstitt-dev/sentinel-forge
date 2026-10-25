import unittest
import sentinel_forge.api as api
class SafeAPI(unittest.TestCase):
 def test_no_test_only_crypto_export(self):
  for n in ("TestOnlyHMACSigner","TestOnlyHMACVerifier","ProtectionProvider","IntentCourierQueue","ReplayRegistry","SendSequenceRegistry"):
   self.assertNotIn(n,api.__all__)
 def test_no_effect_or_network_named_export(self):
  for n in api.__all__:
   low=n.lower();self.assertNotIn("socket",low);self.assertNotIn("network",low);self.assertNotIn("effectcoordinator",low);self.assertNotIn("private",low)
 def test_exports_exist(self):
  for n in api.__all__:self.assertTrue(hasattr(api,n),n)
 def test_exports_unique(self):self.assertEqual(len(api.__all__),len(set(api.__all__)))
