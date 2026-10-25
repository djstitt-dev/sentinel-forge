import itertools,unittest
from sentinel_forge.enrollment import EnrollmentError
from sentinel_forge.transport_readiness import assess_transport_readiness,require_transport_ready
NAMES=("revoked","current_credential","current_session","unresolved_effect","unresolved_recovery","audit_available","assistant_independence_verified","protection_provider_approved","network_provider_approved")
GOOD=dict(revoked=False,current_credential=True,current_session=True,unresolved_effect=False,unresolved_recovery=False,audit_available=True,assistant_independence_verified=True,protection_provider_approved=True,network_provider_approved=True)
class ReadinessExhaustion(unittest.TestCase):
 def test_all_512_boolean_combinations_exact_ready_semantics(self):
  for bits in itertools.product((False,True),repeat=9):
   kw=dict(zip(NAMES,bits));r=assess_transport_readiness(enrollment_state="ACTIVE",**kw)
   expected=all(kw[k]==GOOD[k] for k in NAMES)
   with self.subTest(bits=bits):self.assertEqual(expected,r.ready);self.assertEqual(expected,not r.blockers)
 def test_each_nonactive_state_blocks(self):
  for s in ("STAGED","REMOTE_AUTHENTICATED","VERIFIED","REVOKED","UNKNOWN","active"," ACTIVE "):
   with self.subTest(s=s):
    r=assess_transport_readiness(enrollment_state=s,**GOOD);self.assertFalse(r.ready);self.assertIn("ENROLLMENT_NOT_ACTIVE",r.blockers)
 def test_all_good_is_ready(self):
  r=assess_transport_readiness(enrollment_state="ACTIVE",**GOOD);self.assertTrue(r.ready);require_transport_ready(r)
 def test_every_single_bad_fact_has_expected_blocker(self):
  expected={"revoked":"RELATIONSHIP_REVOKED","current_credential":"CREDENTIAL_NOT_CURRENT","current_session":"SESSION_NOT_CURRENT","unresolved_effect":"UNRESOLVED_EFFECT","unresolved_recovery":"UNRESOLVED_RECOVERY","audit_available":"AUDIT_UNAVAILABLE","assistant_independence_verified":"ASSISTANT_INDEPENDENCE_UNVERIFIED","protection_provider_approved":"PROTECTION_PROVIDER_UNAPPROVED","network_provider_approved":"NETWORK_PROVIDER_UNAPPROVED"}
  for n in NAMES:
   kw=dict(GOOD);kw[n]=not GOOD[n];r=assess_transport_readiness(enrollment_state="ACTIVE",**kw)
   with self.subTest(n=n):self.assertEqual((expected[n],),r.blockers);self.assertFalse(r.ready)
 def test_type_confusion_matrix(self):
  for n in NAMES:
   for bad in (0,1,None,"true",[],{}):
    kw=dict(GOOD);kw[n]=bad
    with self.subTest(n=n,bad=bad):
     with self.assertRaises(EnrollmentError):assess_transport_readiness(enrollment_state="ACTIVE",**kw)
