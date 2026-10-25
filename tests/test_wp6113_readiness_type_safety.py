import unittest
from sentinel_forge.enrollment import EnrollmentError
from sentinel_forge.transport_readiness import assess_transport_readiness
class ReadinessTypeSafety(unittest.TestCase):
 def args(self):return dict(enrollment_state="ACTIVE",revoked=False,current_credential=True,current_session=True,unresolved_effect=False,unresolved_recovery=False,audit_available=True,assistant_independence_verified=True,protection_provider_approved=True,network_provider_approved=True)
 def bad(self,k,v):
  x=self.args();x[k]=v
  with self.assertRaises(EnrollmentError):assess_transport_readiness(**x)
 def test_revoked_string_rejected(self):self.bad("revoked","false")
 def test_current_credential_integer_rejected(self):self.bad("current_credential",1)
 def test_current_session_none_rejected(self):self.bad("current_session",None)
 def test_unresolved_effect_integer_rejected(self):self.bad("unresolved_effect",0)
 def test_unresolved_recovery_string_rejected(self):self.bad("unresolved_recovery","false")
 def test_audit_string_rejected(self):self.bad("audit_available","true")
 def test_independence_integer_rejected(self):self.bad("assistant_independence_verified",1)
 def test_protection_string_rejected(self):self.bad("protection_provider_approved","yes")
 def test_network_integer_rejected(self):self.bad("network_provider_approved",1)
 def test_blank_enrollment_state_rejected(self):self.bad("enrollment_state","")
