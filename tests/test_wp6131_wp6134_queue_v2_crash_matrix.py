import hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from sentinel_forge.courier_orchestrator import prepare_intent_delivery,reconcile_prepared_sequence
from sentinel_forge.courier_queue_v2 import IntentCourierQueue
from sentinel_forge.credential_reference import build_credential_reference
from sentinel_forge.credential_registry import CredentialReferenceRegistry
from sentinel_forge.credential_session import bind_session_credential
from sentinel_forge.delivery_intent import build_delivery_intent
from sentinel_forge.enrollment import EnrollmentError,build_bundle
from sentinel_forge.send_sequence import SendSequenceRegistry
from sentinel_forge.session import derive_session
from sentinel_forge.trust_domain import derive_trust_domain

class CrashMatrix(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();r=Path(self.t.name);self.qp=r/"q";self.sp=r/"s";self.cp=r/"c"
  self.q=IntentCourierQueue(self.qp);self.seq=SendSequenceRegistry(self.sp);self.cr=CredentialReferenceRegistry(self.cp)
  b=build_bundle(forge_identity="forge",remote_identity="reaper",remote_role="reaper",permitted_actions=["receive"],permitted_target="reaper",policy_reference="p")
  self.d=derive_trust_domain(b);self.c=build_credential_reference(self.d,generation=1,key_reference="k1");self.cr.register_initial(self.d,self.c)
  self.s=derive_session(self.d,generation=1,challenge=b"x"*16);self.bind=bind_session_credential(self.s,self.d,self.c)
  self.payload=b"payload";self.a="sha256:"+hashlib.sha256(self.payload).hexdigest()
 def tearDown(self):self.t.cleanup()
 def intent(self,c="c1"):return build_delivery_intent(correlation_id=c,relationship_id=self.d.relationship_id,artifact_identity=self.a,operation="deliver",authorization_reference="auth")
 def args(self):return dict(intent=self.intent(),payload=self.payload,domain=self.d,session=self.s,binding=self.bind,credential=self.c,credential_registry=self.cr,queue=self.q,send_sequences=self.seq)
 def test_crash_after_reserve_before_queue_prepare_reuses_same_sequence(self):
  original=self.q.transition
  with patch.object(self.q,"transition",side_effect=OSError("crash")):
   with self.assertRaises(OSError):prepare_intent_delivery(**self.args())
  st=self.seq.state(self.d.relationship_id);self.assertEqual(1,st["pending_sequence"]);self.assertEqual("QUEUED",self.q.get(st["pending_item_id"])["state"])
  self.q=IntentCourierQueue(self.qp);self.seq=SendSequenceRegistry(self.sp);p=prepare_intent_delivery(**self.args());self.assertEqual(1,p.sequence);self.assertNotIn("pending_item_id",self.seq.state(self.d.relationship_id))
 def test_crash_after_queue_prepare_before_commit_reconciles_without_new_sequence(self):
  with patch.object(self.seq,"commit_item",side_effect=OSError("crash")):
   with self.assertRaises(OSError):prepare_intent_delivery(**self.args())
  st=self.seq.state(self.d.relationship_id);item=st["pending_item_id"];self.assertEqual("PREPARED",self.q.get(item)["state"])
  self.q=IntentCourierQueue(self.qp);self.seq=SendSequenceRegistry(self.sp)
  self.assertEqual(1,reconcile_prepared_sequence(item_id=item,domain=self.d,session=self.s,queue=self.q,send_sequences=self.seq))
  self.assertEqual(1,self.seq.state(self.d.relationship_id)["highest"])
 def test_different_intent_cannot_jump_pending_reservation(self):
  with patch.object(self.q,"transition",side_effect=OSError("crash")):
   with self.assertRaises(OSError):prepare_intent_delivery(**self.args())
  args=self.args();args["intent"]=self.intent("c2")
  with self.assertRaisesRegex(EnrollmentError,"unresolved"):prepare_intent_delivery(**args)
  self.assertEqual(1,self.seq.state(self.d.relationship_id)["highest"])
 def test_restart_does_not_clear_pending(self):
  item=self.q.enqueue(intent=self.intent(),payload_identity=self.a);self.seq.reserve_for_item(self.s,self.d,item)
  for _ in range(10):
   st=SendSequenceRegistry(self.sp).state(self.d.relationship_id);self.assertEqual(item,st["pending_item_id"]);self.assertEqual(1,st["highest"])
 def test_pending_record_field_mutation_matrix(self):
  item=self.q.enqueue(intent=self.intent(),payload_identity=self.a);self.seq.reserve_for_item(self.s,self.d,item);raw=json.loads(self.sp.read_text());rid=self.d.relationship_id
  mutations={"generation":True,"session_id":"","highest":0,"pending_item_id":"","pending_sequence":2}
  for field,bad in mutations.items():
   with self.subTest(field=field):
    d=json.loads(json.dumps(raw));d[rid][field]=bad;self.sp.write_text(json.dumps(d))
    with self.assertRaises(EnrollmentError):SendSequenceRegistry(self.sp)
    self.sp.write_text(json.dumps(raw))
 def test_exact_pending_reservation_is_idempotent(self):
  item=self.q.enqueue(intent=self.intent(),payload_identity=self.a);a=self.seq.reserve_for_item(self.s,self.d,item)
  for _ in range(50):self.assertEqual(a,self.seq.reserve_for_item(self.s,self.d,item))
  self.assertEqual(1,self.seq.state(self.d.relationship_id)["highest"])
