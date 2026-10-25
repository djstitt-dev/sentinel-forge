import unittest
from sentinel_forge.capability import NegotiatedCapabilities
from sentinel_forge.compatibility import CompatibilityRule,require_compatible,rule_for
from sentinel_forge.enrollment import EnrollmentError
class CompatibilityAssaultTests(unittest.TestCase):
 def n(self,**kw):
  x=dict(peer_identity="p",protocol_version=1,schema_version=1,features=("ack","anti-replay"));x.update(kw);return NegotiatedCapabilities(**x)
 def test_bool_protocol_rejected(self):
  with self.assertRaises(EnrollmentError):require_compatible("reaper",self.n(protocol_version=True))
 def test_bool_schema_rejected(self):
  with self.assertRaises(EnrollmentError):require_compatible("reaper",self.n(schema_version=True))
 def test_zero_protocol_rejected(self):
  with self.assertRaises(EnrollmentError):require_compatible("reaper",self.n(protocol_version=0))
 def test_blank_peer_rejected(self):
  with self.assertRaises(EnrollmentError):require_compatible("reaper",self.n(peer_identity=""))
 def test_blank_feature_rejected(self):
  with self.assertRaises(EnrollmentError):require_compatible("reaper",self.n(features=("ack","")))
 def test_future_protocol_unapproved(self):
  with self.assertRaises(EnrollmentError):require_compatible("reaper",self.n(protocol_version=2))
 def test_future_schema_unapproved(self):
  with self.assertRaises(EnrollmentError):require_compatible("reaper",self.n(schema_version=2))
 def test_missing_ack_rejected(self):
  with self.assertRaises(EnrollmentError):require_compatible("reaper",self.n(features=("anti-replay",)))
 def test_missing_antireplay_rejected(self):
  with self.assertRaises(EnrollmentError):require_compatible("reaper",self.n(features=("ack",)))
 def test_unknown_role_rejected(self):
  with self.assertRaises(EnrollmentError):require_compatible("unknown",self.n())
