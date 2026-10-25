import hashlib,tempfile,unittest
from pathlib import Path
from sentinel_forge.courier_orchestrator import prepare_delivery
from sentinel_forge.courier_queue import CourierQueue
from sentinel_forge.credential_reference import build_credential_reference
from sentinel_forge.credential_registry import CredentialReferenceRegistry
from sentinel_forge.credential_session import bind_session_credential
from sentinel_forge.enrollment import EnrollmentError,build_bundle
from sentinel_forge.pre_effect_gate import authorize_effect
from sentinel_forge.send_sequence import SendSequenceRegistry
from sentinel_forge.session import derive_session
from sentinel_forge.trust_domain import derive_trust_domain

class PreEffectGateTests(unittest.TestCase):
 def setUp(self):
  self.td=tempfile.TemporaryDirectory();r=Path(self.td.name);self.payload=b"a";self.a="sha256:"+hashlib.sha256(self.payload).hexdigest()
  self.d=derive_trust_domain(build_bundle(forge_identity="forge",remote_identity="reaper",remote_role="reaper",permitted_actions=["receive"],permitted_target="reaper",policy_reference="p"))
  self.cr=CredentialReferenceRegistry(r/"c");self.c=build_credential_reference(self.d,generation=1,key_reference="k1");self.cr.register_initial(self.d,self.c)
  self.s=derive_session(self.d,generation=1,challenge=b"R"*32);self.b=bind_session_credential(self.s,self.d,self.c);self.q=CourierQueue(r/"q");self.seq=SendSequenceRegistry(r/"s")
  self.p=prepare_delivery(payload=self.payload,artifact_identity=self.a,operation="deliver",domain=self.d,session=self.s,binding=self.b,credential=self.c,credential_registry=self.cr,queue=self.q,send_sequences=self.seq)
 def tearDown(self):self.td.cleanup()
 def auth(self,**kw):
  x=dict(prepared=self.p,queue=self.q,domain=self.d,session=self.s,binding=self.b,credential=self.c,credential_registry=self.cr,
   enrollment_state="ACTIVE",revoked=False,unresolved_effect=False,unresolved_recovery=False,audit_available=True,
   assistant_independence_verified=True,protection_provider_approved=True,network_provider_approved=True,
   expected_target="reaper",actual_target="reaper",expected_classification="CONTROLLED",actual_classification="CONTROLLED");x.update(kw);return authorize_effect(**x)
 def test_valid_current_state_authorizes(self):self.assertEqual(self.p.item_id,self.auth().item_id)
 def test_revocation_kills_prepared_delivery(self):
  with self.assertRaisesRegex(EnrollmentError,"RELATIONSHIP_REVOKED"):self.auth(revoked=True)
 def test_credential_rotation_kills_old_prepared_delivery(self):
  c2=build_credential_reference(self.d,generation=2,key_reference="k2");self.cr.rotate(self.d,c2)
  with self.assertRaisesRegex(EnrollmentError,"stale"):self.auth()
 def test_target_change_fails(self):
  with self.assertRaisesRegex(EnrollmentError,"target binding"):self.auth(actual_target="scribe")
 def test_classification_change_fails(self):
  with self.assertRaisesRegex(EnrollmentError,"classification"):self.auth(actual_classification="PUBLIC")
 def test_audit_loss_blocks(self):
  with self.assertRaisesRegex(EnrollmentError,"AUDIT_UNAVAILABLE"):self.auth(audit_available=False)
 def test_unresolved_effect_blocks(self):
  with self.assertRaisesRegex(EnrollmentError,"UNRESOLVED_EFFECT"):self.auth(unresolved_effect=True)
