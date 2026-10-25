import hashlib,tempfile,unittest
from pathlib import Path
from sentinel_forge.courier_orchestrator import prepare_intent_delivery
from sentinel_forge.courier_queue_v2 import IntentCourierQueue
from sentinel_forge.credential_reference import build_credential_reference
from sentinel_forge.credential_registry import CredentialReferenceRegistry
from sentinel_forge.credential_session import bind_session_credential
from sentinel_forge.delivery_intent import build_delivery_intent
from sentinel_forge.enrollment import EnrollmentError,build_bundle
from sentinel_forge.send_sequence import SendSequenceRegistry
from sentinel_forge.session import derive_session
from sentinel_forge.trust_domain import derive_trust_domain

class IntentOrchestrationTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();r=Path(self.t.name);self.q=IntentCourierQueue(r/"q");self.seq=SendSequenceRegistry(r/"seq");self.cr=CredentialReferenceRegistry(r/"cred")
  self.d=derive_trust_domain(build_bundle(forge_identity="forge",remote_identity="reaper",remote_role="reaper",
   permitted_actions=["receive"],permitted_target="reaper",policy_reference="p"))
  self.c=build_credential_reference(self.d,generation=1,key_reference="key:reaper:1");self.cr.register_initial(self.d,self.c)
  self.s=derive_session(self.d,generation=1,challenge=b"x"*16);self.b=bind_session_credential(self.s,self.d,self.c)
  self.payload=b"payload";self.a="sha256:"+hashlib.sha256(self.payload).hexdigest()
 def tearDown(self):self.t.cleanup()
 def intent(self,c="c1",rel=None,artifact=None,op="deliver",auth="auth"):
  return build_delivery_intent(correlation_id=c,relationship_id=rel or self.d.relationship_id,artifact_identity=artifact or self.a,operation=op,authorization_reference=auth)
 def args(self,i):return dict(intent=i,payload=self.payload,domain=self.d,session=self.s,binding=self.b,credential=self.c,credential_registry=self.cr,queue=self.q,send_sequences=self.seq)
 def test_prepare_binds_intent_to_sequence_and_context(self):
  p=prepare_intent_delivery(**self.args(self.intent()));self.assertEqual(1,p.sequence);self.assertEqual("PREPARED",self.q.get(p.item_id)["state"])
 def test_wrong_relationship_rejected_before_queue(self):
  with self.assertRaises(EnrollmentError):prepare_intent_delivery(**self.args(self.intent(rel="other")))
  self.assertEqual([],self.q.pending(self.d.relationship_id))
 def test_wrong_artifact_rejected_before_queue(self):
  with self.assertRaises(EnrollmentError):prepare_intent_delivery(**self.args(self.intent(artifact="sha256:wrong")))
  self.assertEqual([],self.q.pending(self.d.relationship_id))
 def test_exact_prepare_replay_does_not_allocate_second_sequence(self):
  p=prepare_intent_delivery(**self.args(self.intent()))
  with self.assertRaisesRegex(EnrollmentError,"not eligible"):prepare_intent_delivery(**self.args(self.intent()))
  self.assertEqual(1,self.seq.state(self.d.relationship_id)["highest"]);self.assertEqual("PREPARED",self.q.get(p.item_id)["state"])
 def test_new_delivery_same_bytes_gets_new_queue_identity_and_sequence(self):
  p1=prepare_intent_delivery(**self.args(self.intent("c1")));self.q.transition(p1.item_id,expected="PREPARED",new="IN_FLIGHT",sequence=1);self.q.transition(p1.item_id,expected="IN_FLIGHT",new="REJECTED",sequence=1)
  p2=prepare_intent_delivery(**self.args(self.intent("c2")));self.assertNotEqual(p1.item_id,p2.item_id);self.assertEqual(2,p2.sequence)
 def test_new_authorization_same_correlation_is_conflict(self):
  prepare_intent_delivery(**self.args(self.intent("c1",auth="a1")))
  # Existing PREPARED also blocks new preparation; correlation conflict is independently enforced by queue-v2.
  with self.assertRaises(EnrollmentError):self.q.enqueue(intent=self.intent("c1",auth="a2"),payload_identity=self.a)
 def test_operation_is_intent_bound(self):
  p=prepare_intent_delivery(**self.args(self.intent(op="release-evidence")));self.assertEqual("release-evidence",p.operation);self.assertEqual("release-evidence",self.q.get(p.item_id)["operation"])
