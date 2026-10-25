import hashlib,tempfile,threading,unittest
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

class AuthorityRaceTests(unittest.TestCase):
 def setUp(self):
  self.td=tempfile.TemporaryDirectory();r=Path(self.td.name);self.payload=b"x";self.a="sha256:"+hashlib.sha256(self.payload).hexdigest()
  self.d=derive_trust_domain(build_bundle(forge_identity="forge",remote_identity="reaper",remote_role="reaper",permitted_actions=["receive"],permitted_target="reaper",policy_reference="p"))
  self.cr=CredentialReferenceRegistry(r/"c");self.c=build_credential_reference(self.d,generation=1,key_reference="k1");self.cr.register_initial(self.d,self.c)
  self.s=derive_session(self.d,generation=1,challenge=b"R"*32);self.b=bind_session_credential(self.s,self.d,self.c);self.q=CourierQueue(r/"q");self.seq=SendSequenceRegistry(r/"s")
 def tearDown(self):self.td.cleanup()
 def prep(self):return prepare_delivery(payload=self.payload,artifact_identity=self.a,operation="deliver",domain=self.d,session=self.s,binding=self.b,credential=self.c,credential_registry=self.cr,queue=self.q,send_sequences=self.seq)
 def auth(self,p):
  return authorize_effect(prepared=p,queue=self.q,domain=self.d,session=self.s,binding=self.b,credential=self.c,credential_registry=self.cr,enrollment_state="ACTIVE",revoked=False,unresolved_effect=False,unresolved_recovery=False,audit_available=True,assistant_independence_verified=True,protection_provider_approved=True,network_provider_approved=True,expected_target="reaper",actual_target="reaper",expected_classification="CONTROLLED",actual_classification="CONTROLLED")
 def test_concurrent_prepare_same_artifact_has_one_queue_item_unique_sequences_not_reused(self):
  out=[];lock=threading.Lock()
  def f():
   try:v=("ok",self.prep())
   except Exception as e:v=("err",type(e).__name__)
   with lock:out.append(v)
  ts=[threading.Thread(target=f) for _ in range(8)];[t.start() for t in ts];[t.join() for t in ts]
  oks=[v for k,v in out if k=="ok"];self.assertEqual(1,len(oks));self.assertEqual(1,oks[0].sequence)
 def test_rotation_after_prepare_blocks_old_authority(self):
  p=self.prep();self.cr.rotate(self.d,build_credential_reference(self.d,generation=2,key_reference="k2"))
  with self.assertRaises(EnrollmentError):self.auth(p)
