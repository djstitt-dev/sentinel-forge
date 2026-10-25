import hashlib,tempfile,unittest
from pathlib import Path
from sentinel_forge.consistency_audit import audit_relationship
from sentinel_forge.courier_queue_v2 import IntentCourierQueue
from sentinel_forge.credential_reference import build_credential_reference
from sentinel_forge.credential_registry import CredentialReferenceRegistry
from sentinel_forge.credential_session import bind_session_credential
from sentinel_forge.delivery_intent import build_delivery_intent
from sentinel_forge.enrollment import EnrollmentRegistry,build_bundle
from sentinel_forge.revocation import RevocationRegistry,make_revocation
from sentinel_forge.send_sequence import SendSequenceRegistry
from sentinel_forge.session import ReplayRegistry,derive_session
from sentinel_forge.trust_domain import derive_trust_domain
class ConsistencyAuditTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();r=Path(self.t.name)
  self.er=EnrollmentRegistry(r/"e");self.rr=RevocationRegistry(r/"rev");self.sr=SendSequenceRegistry(r/"send");self.rp=ReplayRegistry(r/"recv");self.q=IntentCourierQueue(r/"q");self.cr=CredentialReferenceRegistry(r/"cred")
  self.bundle=build_bundle(forge_identity="forge",remote_identity="reaper",remote_role="reaper",permitted_actions=["receive"],permitted_target="reaper",policy_reference="p");self.er.stage(self.bundle);self.d=derive_trust_domain(self.bundle);self.c=build_credential_reference(self.d,generation=1,key_reference="k1");self.cr.register_initial(self.d,self.c);self.s=derive_session(self.d,generation=1,challenge=b"x"*16);self.b=bind_session_credential(self.s,self.d,self.c)
 def tearDown(self):self.t.cleanup()
 def args(self):return dict(bundle=self.bundle,domain=self.d,session=self.s,binding=self.b,credential=self.c,credential_registry=self.cr,enrollment_registry=self.er,revocation_registry=self.rr,send_registry=self.sr,replay_registry=self.rp,queue=self.q)
 def test_clean_staged_relationship_consistent(self):self.assertTrue(audit_relationship(**self.args()).consistent)
 def test_pending_queue_counted(self):
  a="sha256:"+hashlib.sha256(b"x").hexdigest();i=build_delivery_intent(correlation_id="c",relationship_id=self.d.relationship_id,artifact_identity=a,operation="d",authorization_reference="a");self.q.enqueue(intent=i,payload_identity=a);self.assertEqual(1,audit_relationship(**self.args()).pending_queue_items)
 def test_revocation_blocks_consistency(self):
  self.rr.revoke(make_revocation(enrollment_id=self.bundle.enrollment_id,remote_identity=self.bundle.remote_identity,operator_authorization_reference="op",reason="stop",prior_state="STAGED"));x=audit_relationship(**self.args());self.assertFalse(x.consistent);self.assertIn("RELATIONSHIP_REVOKED",x.blockers)
