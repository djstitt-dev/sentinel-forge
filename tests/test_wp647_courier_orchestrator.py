import hashlib,tempfile,unittest
from pathlib import Path
from sentinel_forge.courier_orchestrator import prepare_delivery,mark_effect_started,mark_effect_uncertain
from sentinel_forge.courier_queue import CourierQueue
from sentinel_forge.credential_reference import build_credential_reference
from sentinel_forge.credential_registry import CredentialReferenceRegistry
from sentinel_forge.credential_session import bind_session_credential
from sentinel_forge.enrollment import EnrollmentError,build_bundle
from sentinel_forge.send_sequence import SendSequenceRegistry
from sentinel_forge.session import derive_session
from sentinel_forge.trust_domain import derive_trust_domain

class OrchestratorTests(unittest.TestCase):
 def setUp(self):
  self.td=tempfile.TemporaryDirectory();root=Path(self.td.name);self.payload=b"artifact";self.a="sha256:"+hashlib.sha256(self.payload).hexdigest()
  self.d=derive_trust_domain(build_bundle(forge_identity="forge",remote_identity="reaper",remote_role="reaper",permitted_actions=["receive"],permitted_target="reaper",policy_reference="p"))
  self.cr=CredentialReferenceRegistry(root/"c");self.c=build_credential_reference(self.d,generation=1,key_reference="cred:r:1");self.cr.register_initial(self.d,self.c)
  self.s=derive_session(self.d,generation=1,challenge=b"R"*32);self.cb=bind_session_credential(self.s,self.d,self.c)
  self.q=CourierQueue(root/"q");self.seq=SendSequenceRegistry(root/"s")
 def tearDown(self):self.td.cleanup()
 def prep(self):return prepare_delivery(payload=self.payload,artifact_identity=self.a,operation="deliver",domain=self.d,session=self.s,binding=self.cb,credential=self.c,credential_registry=self.cr,queue=self.q,send_sequences=self.seq)
 def test_prepare_binds_queue_sequence_and_context(self):
  p=self.prep();r=self.q.get(p.item_id);self.assertEqual("PREPARED",r["state"]);self.assertEqual(p.sequence,r["sequence"]);self.assertEqual(p.relationship_id,p.context.relationship_id)
 def test_effect_lifecycle(self):
  p=self.prep();mark_effect_started(p,self.q);self.assertEqual("IN_FLIGHT",self.q.get(p.item_id)["state"]);mark_effect_uncertain(p,self.q);self.assertEqual("OUTCOME_UNKNOWN",self.q.get(p.item_id)["state"])
 def test_wrong_payload_identity_fails_before_queue(self):
  with self.assertRaisesRegex(EnrollmentError,"artifact identity"):prepare_delivery(payload=b"evil",artifact_identity=self.a,operation="deliver",domain=self.d,session=self.s,binding=self.cb,credential=self.c,credential_registry=self.cr,queue=self.q,send_sequences=self.seq)
  self.assertEqual([],self.q.pending(self.d.relationship_id))
 def test_stale_credential_fails(self):
  c2=build_credential_reference(self.d,generation=2,key_reference="cred:r:2");self.cr.rotate(self.d,c2)
  with self.assertRaisesRegex(EnrollmentError,"stale"):self.prep()
 def test_duplicate_preparation_refused(self):
  self.prep()
  with self.assertRaisesRegex(EnrollmentError,"not eligible"):self.prep()
