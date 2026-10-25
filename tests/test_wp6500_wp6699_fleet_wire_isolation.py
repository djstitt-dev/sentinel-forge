import tempfile,unittest
from pathlib import Path
from sentinel_forge.credential_reference import build_credential_reference
from sentinel_forge.credential_registry import CredentialReferenceRegistry
from sentinel_forge.credential_session import bind_session_credential
from sentinel_forge.enrollment import EnrollmentError,build_bundle
from sentinel_forge.protected_wire import encode,decode
from sentinel_forge.session import derive_session
from sentinel_forge.transport_contract import build_transport_context
from sentinel_forge.trust_domain import derive_trust_domain
class P:
 provider_id="TEST-P"
 def protect(self,p,*,associated_data,key_reference):
  k=(sum(associated_data)+sum(key_reference.encode()))%251+1;return bytes(x^k for x in p)
 def unprotect(self,p,*,associated_data,key_reference):return self.protect(p,associated_data=associated_data,key_reference=key_reference)
class FleetWire(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.root=Path(self.t.name);self.p=P();self.nodes={}
  for peer,role in (("reaper","reaper"),("scribe","scribe"),("watchtower","watchtower")):
   d=derive_trust_domain(build_bundle(forge_identity="forge",remote_identity=peer,remote_role=role,permitted_actions=["receive"],permitted_target=peer,policy_reference="p"))
   r=CredentialReferenceRegistry(self.root/(peer+"-c"));c=build_credential_reference(d,generation=1,key_reference="key:"+peer);r.register_initial(d,c)
   s=derive_session(d,generation=1,challenge=(peer.encode()*16)[:32]);b=bind_session_credential(s,d,c);h,x=build_transport_context(d,s,b,c,r,operation="deliver",artifact_identity="sha256:"+peer,sequence=1)
   self.nodes[peer]=(d,r,c,s,b,h,x)
 def tearDown(self):self.t.cleanup()
 def args(self,n):
  d,r,c,s,b,h,x=self.nodes[n];return dict(header=h,context=x,domain=d,session=s,binding=b,credential=c,credential_registry=r,provider=self.p)
 def test_each_peer_roundtrip(self):
  for n in self.nodes:
   with self.subTest(n=n):w=encode(plaintext=n.encode(),**self.args(n));self.assertEqual(n.encode(),decode(wire=w,**self.args(n)))
 def test_every_cross_peer_decode_rejected(self):
  for src in self.nodes:
   w=encode(plaintext=src.encode(),**self.args(src))
   for dst in self.nodes:
    if src==dst:continue
    with self.subTest(src=src,dst=dst):
     with self.assertRaises(EnrollmentError):decode(wire=w,**self.args(dst))
 def test_every_cross_peer_context_encode_rejected(self):
  for a in self.nodes:
   for b in self.nodes:
    if a==b:continue
    args=self.args(a);args["context"]=self.nodes[b][-1]
    with self.subTest(a=a,b=b):
     with self.assertRaises(EnrollmentError):encode(plaintext=b"x",**args)
 def test_key_refs_unique(self):
  self.assertEqual(3,len({self.nodes[n][2].key_reference for n in self.nodes}))
 def test_relationships_unique(self):
  self.assertEqual(3,len({self.nodes[n][0].relationship_id for n in self.nodes}))
 def test_sessions_unique(self):
  self.assertEqual(3,len({self.nodes[n][3].session_id for n in self.nodes}))
