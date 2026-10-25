import tempfile,unittest
from pathlib import Path
from sentinel_forge.courier_ack import build_ack,verify_ack
from sentinel_forge.credential_reference import build_credential_reference
from sentinel_forge.credential_registry import CredentialReferenceRegistry
from sentinel_forge.credential_session import bind_session_credential
from sentinel_forge.delivery_intent import build_delivery_intent,verify_delivery_intent
from sentinel_forge.enrollment import EnrollmentError,build_bundle
from sentinel_forge.session import derive_session
from sentinel_forge.transport_contract import build_transport_context,validate_transport_context
from sentinel_forge.trust_domain import derive_trust_domain
PEERS=("reaper","scribe","watchtower")
class FleetIsolationMatrix(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.cr=CredentialReferenceRegistry(Path(self.t.name)/"c");self.x={}
  for n in PEERS:
   d=derive_trust_domain(build_bundle(forge_identity="forge",remote_identity=n,remote_role=n,permitted_actions=["receive"],permitted_target=n,policy_reference="p"));c=build_credential_reference(d,generation=1,key_reference="key:"+n);self.cr.register_initial(d,c);s=derive_session(d,generation=1,challenge=(n.encode()*32)[:32]);b=bind_session_credential(s,d,c);h,ctx=build_transport_context(d,s,b,c,self.cr,operation="deliver",artifact_identity="a",sequence=1);self.x[n]=(d,c,s,b,h,ctx)
 def tearDown(self):self.t.cleanup()
 def test_every_cross_peer_context_rejected(self):
  for source in PEERS:
   for target in PEERS:
    if source==target:continue
    with self.subTest(source=source,target=target):
     _,_,_,_,h,ctx=self.x[source];d,c,s,b,_,_=self.x[target]
     with self.assertRaises(EnrollmentError):validate_transport_context(h,ctx,d,s,b,c,self.cr,expected_operation="deliver",expected_artifact_identity="a",expected_sequence=1)
 def test_every_cross_peer_ack_rejected(self):
  for source in PEERS:
   for target in PEERS:
    if source==target:continue
    with self.subTest(source=source,target=target):
     *_,ctxs=self.x[source];*_,ctxt=self.x[target];ack=build_ack(ctxs,sequence=1,operation="deliver",artifact_identity="a",disposition="ACCEPTED",reason="ok")
     with self.assertRaises(EnrollmentError):verify_ack(ack,ctxt,sequence=1,operation="deliver",artifact_identity="a")
 def test_every_cross_peer_credential_rejected(self):
  for source in PEERS:
   for target in PEERS:
    if source==target:continue
    with self.subTest(source=source,target=target):
     ds,cs,*_=self.x[source];dt,_,st,_,_,_=self.x[target]
     with self.assertRaises(EnrollmentError):bind_session_credential(st,dt,cs)
 def test_delivery_intent_relationship_swap_rejected(self):
  for source in PEERS:
   d,*_=self.x[source];i=build_delivery_intent(correlation_id="c",relationship_id=d.relationship_id,artifact_identity="a",operation="deliver",authorization_reference="auth")
   for target in PEERS:
    if target==source:continue
    with self.subTest(source=source,target=target):
     td,*_=self.x[target]
     with self.assertRaises(EnrollmentError):verify_delivery_intent(i,relationship_id=td.relationship_id)

def _context_case(source,target):
 def test(self):
  _,_,_,_,h,ctx=self.x[source];d,c,s,b,_,_=self.x[target]
  with self.assertRaises(EnrollmentError):validate_transport_context(h,ctx,d,s,b,c,self.cr,expected_operation="deliver",expected_artifact_identity="a",expected_sequence=1)
 return test
def _ack_case(source,target):
 def test(self):
  *_,a=self.x[source];*_,b=self.x[target];ack=build_ack(a,sequence=1,operation="deliver",artifact_identity="a",disposition="ACCEPTED",reason="ok")
  with self.assertRaises(EnrollmentError):verify_ack(ack,b,sequence=1,operation="deliver",artifact_identity="a")
 return test
def _credential_case(source,target):
 def test(self):
  _,c,*_=self.x[source];d,_,s,_,_,_=self.x[target]
  with self.assertRaises(EnrollmentError):bind_session_credential(s,d,c)
 return test
for _s in PEERS:
 for _t in PEERS:
  if _s==_t:continue
  setattr(FleetIsolationMatrix,f"test_context_{_s}_cannot_be_{_t}",_context_case(_s,_t))
  setattr(FleetIsolationMatrix,f"test_ack_{_s}_cannot_close_{_t}",_ack_case(_s,_t))
  setattr(FleetIsolationMatrix,f"test_credential_{_s}_cannot_bind_{_t}",_credential_case(_s,_t))
