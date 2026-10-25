import hashlib,tempfile,unittest
from pathlib import Path
from sentinel_forge.courier_ack import build_ack
from sentinel_forge.courier_orchestrator import prepare_delivery,mark_effect_started,mark_effect_uncertain
from sentinel_forge.courier_queue import CourierQueue
from sentinel_forge.courier_reconcile import reconcile_with_ack
from sentinel_forge.credential_reference import build_credential_reference
from sentinel_forge.credential_registry import CredentialReferenceRegistry
from sentinel_forge.credential_session import bind_session_credential
from sentinel_forge.enrollment import EnrollmentError,build_bundle
from sentinel_forge.pre_effect_gate import authorize_effect
from sentinel_forge.send_sequence import SendSequenceRegistry
from sentinel_forge.session import derive_session
from sentinel_forge.trust_domain import derive_trust_domain

class CourierAcceptanceTests(unittest.TestCase):
 def setUp(self):
  self.td=tempfile.TemporaryDirectory();r=Path(self.td.name);self.payload=b"controlled-artifact";self.a="sha256:"+hashlib.sha256(self.payload).hexdigest()
  self.d=derive_trust_domain(build_bundle(forge_identity="forge",remote_identity="reaper",remote_role="reaper",permitted_actions=["receive"],permitted_target="reaper",policy_reference="p"))
  self.cr=CredentialReferenceRegistry(r/"c");self.c=build_credential_reference(self.d,generation=1,key_reference="k1");self.cr.register_initial(self.d,self.c)
  self.s=derive_session(self.d,generation=1,challenge=b"R"*32);self.b=bind_session_credential(self.s,self.d,self.c);self.q=CourierQueue(r/"q");self.seq=SendSequenceRegistry(r/"s")
 def tearDown(self):self.td.cleanup()
 def prep(self):return prepare_delivery(payload=self.payload,artifact_identity=self.a,operation="deliver",domain=self.d,session=self.s,binding=self.b,credential=self.c,credential_registry=self.cr,queue=self.q,send_sequences=self.seq)
 def authorize(self,p,**kw):
  x=dict(prepared=p,queue=self.q,domain=self.d,session=self.s,binding=self.b,credential=self.c,credential_registry=self.cr,enrollment_state="ACTIVE",revoked=False,unresolved_effect=False,unresolved_recovery=False,audit_available=True,assistant_independence_verified=True,protection_provider_approved=True,network_provider_approved=True,expected_target="reaper",actual_target="reaper",expected_classification="CONTROLLED",actual_classification="CONTROLLED");x.update(kw);return authorize_effect(**x)
 def test_happy_path_through_ack_closure(self):
  p=self.prep();self.authorize(p);mark_effect_started(p,self.q)
  ack=build_ack(p.context,sequence=p.sequence,operation=p.operation,artifact_identity=p.artifact_identity,disposition="ACCEPTED",reason="validated")
  self.assertEqual("ACKNOWLEDGED",reconcile_with_ack(self.q,p.item_id,ack,p.context,operation=p.operation,artifact_identity=p.artifact_identity,sequence=p.sequence))
 def test_timeout_becomes_unknown_not_retry(self):
  p=self.prep();self.authorize(p);mark_effect_started(p,self.q);mark_effect_uncertain(p,self.q)
  with self.assertRaises(EnrollmentError):mark_effect_started(p,self.q)
 def test_revocation_between_prepare_and_effect_blocks(self):
  p=self.prep()
  with self.assertRaisesRegex(EnrollmentError,"RELATIONSHIP_REVOKED"):self.authorize(p,revoked=True)
  self.assertEqual("PREPARED",self.q.get(p.item_id)["state"])
 def test_rotation_between_prepare_and_effect_blocks(self):
  p=self.prep();self.cr.rotate(self.d,build_credential_reference(self.d,generation=2,key_reference="k2"))
  with self.assertRaisesRegex(EnrollmentError,"stale"):self.authorize(p)
 def test_wrong_peer_ack_does_not_close(self):
  p=self.prep();self.authorize(p);mark_effect_started(p,self.q)
  bad=build_ack(p.context,sequence=p.sequence+1,operation=p.operation,artifact_identity=p.artifact_identity,disposition="ACCEPTED",reason="validated")
  with self.assertRaises(EnrollmentError):reconcile_with_ack(self.q,p.item_id,bad,p.context,operation=p.operation,artifact_identity=p.artifact_identity,sequence=p.sequence)
  self.assertEqual("IN_FLIGHT",self.q.get(p.item_id)["state"])
