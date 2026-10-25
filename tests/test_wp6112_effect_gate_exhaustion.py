import dataclasses
import hashlib,tempfile,unittest
from pathlib import Path
from sentinel_forge.courier_orchestrator import prepare_delivery
from sentinel_forge.courier_queue import CourierQueue
from sentinel_forge.credential_reference import build_credential_reference
from sentinel_forge.credential_registry import CredentialReferenceRegistry
from sentinel_forge.credential_session import bind_session_credential
from sentinel_forge.enrollment import build_bundle
from sentinel_forge.pre_effect_gate import authorize_effect
from sentinel_forge.send_sequence import SendSequenceRegistry
from sentinel_forge.session import derive_session
from sentinel_forge.trust_domain import derive_trust_domain
from sentinel_forge.enrollment import EnrollmentError
class EffectGateExhaustion(unittest.TestCase):
 def setUp(self):
  self.td=tempfile.TemporaryDirectory();r=Path(self.td.name);payload=b"a";self.a="sha256:"+hashlib.sha256(payload).hexdigest()
  self.d=derive_trust_domain(build_bundle(forge_identity="forge",remote_identity="reaper",remote_role="reaper",permitted_actions=["receive"],permitted_target="reaper",policy_reference="p"))
  self.cr=CredentialReferenceRegistry(r/"c");self.c=build_credential_reference(self.d,generation=1,key_reference="k1");self.cr.register_initial(self.d,self.c)
  self.s=derive_session(self.d,generation=1,challenge=b"R"*32);self.b=bind_session_credential(self.s,self.d,self.c);self.q=CourierQueue(r/"q");self.seq=SendSequenceRegistry(r/"s")
  self.p=prepare_delivery(payload=payload,artifact_identity=self.a,operation="deliver",domain=self.d,session=self.s,binding=self.b,credential=self.c,credential_registry=self.cr,queue=self.q,send_sequences=self.seq)
 def tearDown(self):self.td.cleanup()
 def auth(self,**kw):
  x=dict(prepared=self.p,queue=self.q,domain=self.d,session=self.s,binding=self.b,credential=self.c,credential_registry=self.cr,enrollment_state="ACTIVE",revoked=False,unresolved_effect=False,unresolved_recovery=False,audit_available=True,assistant_independence_verified=True,protection_provider_approved=True,network_provider_approved=True,expected_target="reaper",actual_target="reaper",expected_classification="CONTROLLED",actual_classification="CONTROLLED");x.update(kw);return authorize_effect(**x)

 def test_inactive_enrollment_blocks(self):
  with self.assertRaises(EnrollmentError):self.auth(enrollment_state="STAGED")
 def test_unknown_enrollment_blocks(self):
  with self.assertRaises(EnrollmentError):self.auth(enrollment_state="UNKNOWN")
 def test_unresolved_recovery_blocks(self):
  with self.assertRaises(EnrollmentError):self.auth(unresolved_recovery=True)
 def test_assistant_independence_unverified_blocks(self):
  with self.assertRaises(EnrollmentError):self.auth(assistant_independence_verified=False)
 def test_protection_unapproved_blocks(self):
  with self.assertRaises(EnrollmentError):self.auth(protection_provider_approved=False)
 def test_network_unapproved_blocks(self):
  with self.assertRaises(EnrollmentError):self.auth(network_provider_approved=False)
 def test_expected_target_mutation_blocks(self):
  with self.assertRaises(EnrollmentError):self.auth(expected_target="scribe")
 def test_expected_classification_mutation_blocks(self):
  with self.assertRaises(EnrollmentError):self.auth(expected_classification="SECRET")
 def test_queue_not_prepared_blocks(self):
  self.q.transition(self.p.item_id,expected="PREPARED",new="IN_FLIGHT",sequence=self.p.sequence)
  with self.assertRaises(EnrollmentError):self.auth()
 def test_prepared_relationship_mutation_blocks(self):
  with self.assertRaises(EnrollmentError):self.auth(prepared=dataclasses.replace(self.p,relationship_id="evil"))
 def test_prepared_sequence_mutation_blocks(self):
  with self.assertRaises(EnrollmentError):self.auth(prepared=dataclasses.replace(self.p,sequence=self.p.sequence+1))
 def test_prepared_artifact_mutation_blocks(self):
  with self.assertRaises(EnrollmentError):self.auth(prepared=dataclasses.replace(self.p,artifact_identity="evil"))
 def test_prepared_operation_mutation_blocks(self):
  with self.assertRaises(EnrollmentError):self.auth(prepared=dataclasses.replace(self.p,operation="evil"))
 def test_wrong_credential_binding_blocks(self):
  with self.assertRaises(EnrollmentError):self.auth(binding=dataclasses.replace(self.b,key_reference="evil"))
 def test_wrong_session_blocks(self):
  with self.assertRaises(EnrollmentError):self.auth(session=dataclasses.replace(self.s,session_id=self.s.session_id+"x"))
