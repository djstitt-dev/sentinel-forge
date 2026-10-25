import hashlib,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from sentinel_forge.courier_orchestrator import prepare_delivery
from sentinel_forge.courier_queue import CourierQueue
from sentinel_forge.credential_reference import build_credential_reference
from sentinel_forge.credential_registry import CredentialReferenceRegistry
from sentinel_forge.credential_session import bind_session_credential
from sentinel_forge.enrollment import EnrollmentError,build_bundle
from sentinel_forge.send_sequence import SendSequenceRegistry
from sentinel_forge.session import derive_session
from sentinel_forge.trust_domain import derive_trust_domain

class SequenceReservationRecoveryTests(unittest.TestCase):
 def setUp(self):
  self.td=tempfile.TemporaryDirectory();r=Path(self.td.name);self.payload=b"x";self.a="sha256:"+hashlib.sha256(self.payload).hexdigest()
  self.d=derive_trust_domain(build_bundle(forge_identity="forge",remote_identity="reaper",remote_role="reaper",permitted_actions=["receive"],permitted_target="reaper",policy_reference="p"))
  self.cr=CredentialReferenceRegistry(r/"c");self.c=build_credential_reference(self.d,generation=1,key_reference="k");self.cr.register_initial(self.d,self.c)
  self.s=derive_session(self.d,generation=1,challenge=b"R"*32);self.b=bind_session_credential(self.s,self.d,self.c);self.q=CourierQueue(r/"q");self.seq=SendSequenceRegistry(r/"s")
 def tearDown(self):self.td.cleanup()
 def args(self):return dict(payload=self.payload,artifact_identity=self.a,operation="deliver",domain=self.d,session=self.s,binding=self.b,credential=self.c,credential_registry=self.cr,queue=self.q,send_sequences=self.seq)
 def test_context_failure_reuses_same_sequence_after_restart(self):
  import sentinel_forge.courier_orchestrator as o
  real=o.build_transport_context
  with patch.object(o,"build_transport_context",side_effect=RuntimeError("crash")):
   with self.assertRaises(RuntimeError):prepare_delivery(**self.args())
  st=SendSequenceRegistry(self.seq.path).state(self.d.relationship_id);self.assertEqual((1,1),(st["highest"],st["pending_sequence"]))
  p=prepare_delivery(**self.args());self.assertEqual(1,p.sequence);self.assertNotIn("pending_item_id",self.seq.state(self.d.relationship_id))
 def test_queue_transition_failure_reuses_same_sequence(self):
  real=self.q.transition
  with patch.object(self.q,"transition",side_effect=OSError("disk")):
   with self.assertRaises(OSError):prepare_delivery(**self.args())
  p=prepare_delivery(**self.args());self.assertEqual(1,p.sequence)
 def test_different_item_blocked_while_reservation_unresolved(self):
  item=self.q.enqueue(relationship_id=self.d.relationship_id,artifact_identity=self.a,operation="deliver",payload_identity=self.a)
  self.seq.reserve_for_item(self.s,self.d,item)
  with self.assertRaisesRegex(EnrollmentError,"unresolved"):self.seq.reserve_for_item(self.s,self.d,"different")

class PreparedCommitRecoveryTests(SequenceReservationRecoveryTests):
 def test_prepared_queue_pending_reservation_can_close_without_new_sequence(self):
  from sentinel_forge.courier_orchestrator import reconcile_prepared_sequence
  item=self.q.enqueue(relationship_id=self.d.relationship_id,artifact_identity=self.a,operation="deliver",payload_identity=self.a)
  seq=self.seq.reserve_for_item(self.s,self.d,item);self.q.transition(item,expected="QUEUED",new="PREPARED",sequence=seq)
  self.assertEqual(1,reconcile_prepared_sequence(item_id=item,domain=self.d,session=self.s,queue=self.q,send_sequences=self.seq))
  self.assertNotIn("pending_item_id",self.seq.state(self.d.relationship_id))
 def test_reconcile_refuses_queued_state(self):
  from sentinel_forge.courier_orchestrator import reconcile_prepared_sequence
  item=self.q.enqueue(relationship_id=self.d.relationship_id,artifact_identity=self.a,operation="deliver",payload_identity=self.a);self.seq.reserve_for_item(self.s,self.d,item)
  with self.assertRaises(EnrollmentError):reconcile_prepared_sequence(item_id=item,domain=self.d,session=self.s,queue=self.q,send_sequences=self.seq)
