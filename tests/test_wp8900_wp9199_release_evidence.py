import dataclasses,unittest
from sentinel_forge.enrollment import EnrollmentError
from sentinel_forge.release_evidence import *
HEAD="d5b8f07542bde35c78795c126ad5c89698f3cb08"
class ReleaseEvidenceTests(unittest.TestCase):
 def good(self):return build_release_evidence(repository_head=HEAD,test_count=1200,checkpoint_end=5000,offline_invariants_passed=True,production_ready=False,blockers=("NETWORK_UNAPPROVED","INDEPENDENCE_UNVERIFIED"))
 def test_valid(self):self.assertTrue(verify_release_evidence(self.good()))
 def test_every_field_mutation_rejected(self):
  e=self.good()
  for f in e.__dataclass_fields__:
   v=getattr(e,f)
   if f=="evidence_digest":bad="sha256:bad"
   elif isinstance(v,bool):bad=not v
   elif isinstance(v,int):bad=v+1
   elif isinstance(v,tuple):bad=v+("x",)
   else:bad=v[:-1]+("0" if v[-1]!="0" else "1")
   with self.subTest(f=f):
    with self.assertRaises(EnrollmentError):verify_release_evidence(dataclasses.replace(e,**{f:bad}))
 def test_bad_head_matrix(self):
  for h in ("","abc","g"*40,"0"*39,"0"*41,None,1):
   with self.subTest(h=h):
    with self.assertRaises(EnrollmentError):build_release_evidence(repository_head=h,test_count=1,checkpoint_end=1,offline_invariants_passed=True,production_ready=False,blockers=("b",))
 def test_bool_numeric_confusion_rejected(self):
  for field in ("test_count","checkpoint_end"):
   kw=dict(repository_head=HEAD,test_count=1,checkpoint_end=1,offline_invariants_passed=True,production_ready=False,blockers=("b",));kw[field]=True
   with self.assertRaises(EnrollmentError):build_release_evidence(**kw)
 def test_production_ready_cannot_have_blocker(self):
  with self.assertRaises(EnrollmentError):build_release_evidence(repository_head=HEAD,test_count=1,checkpoint_end=1,offline_invariants_passed=True,production_ready=True,blockers=("b",))
 def test_production_ready_requires_offline(self):
  with self.assertRaises(EnrollmentError):build_release_evidence(repository_head=HEAD,test_count=1,checkpoint_end=1,offline_invariants_passed=False,production_ready=True,blockers=())
 def test_nonproduction_requires_reason(self):
  with self.assertRaises(EnrollmentError):build_release_evidence(repository_head=HEAD,test_count=1,checkpoint_end=1,offline_invariants_passed=True,production_ready=False,blockers=())
 def test_duplicate_blank_blockers_rejected(self):
  for b in (("x","x"),("",),(" ",),(1,)):
   with self.subTest(b=b):
    with self.assertRaises(EnrollmentError):build_release_evidence(repository_head=HEAD,test_count=1,checkpoint_end=1,offline_invariants_passed=True,production_ready=False,blockers=b)
