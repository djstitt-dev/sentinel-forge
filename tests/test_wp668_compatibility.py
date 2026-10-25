import unittest
from sentinel_forge.capability import NegotiatedCapabilities
from sentinel_forge.compatibility import CompatibilityRule,require_compatible,rule_for
from sentinel_forge.enrollment import EnrollmentError
class CompatibilityTests(unittest.TestCase):
 def test_all_known_roles_have_rules(self):
  for r in ("reaper","scribe","watchtower"):self.assertEqual(r,rule_for(r).peer_role)
 def test_unknown_role_fails(self):
  with self.assertRaises(EnrollmentError):rule_for("evil")
 def test_supported_context(self):
  require_compatible("reaper",NegotiatedCapabilities("reaper",1,1,("ack","anti-replay")))
 def test_future_version_not_silently_accepted(self):
  with self.assertRaisesRegex(EnrollmentError,"protocol"):require_compatible("reaper",NegotiatedCapabilities("reaper",2,1,("ack","anti-replay")))
 def test_missing_security_feature_fails(self):
  with self.assertRaisesRegex(EnrollmentError,"features"):require_compatible("scribe",NegotiatedCapabilities("scribe",1,1,("ack",)))
 def test_duplicate_role_policy_fails(self):
  rules=(CompatibilityRule("reaper",1,1,1,1,()),CompatibilityRule("reaper",1,2,1,1,()))
  with self.assertRaisesRegex(EnrollmentError,"unique"):rule_for("reaper",rules)
