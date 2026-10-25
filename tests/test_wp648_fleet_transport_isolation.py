import hashlib,tempfile,unittest
from pathlib import Path
from sentinel_forge.courier_ack import build_ack
from sentinel_forge.courier_orchestrator import prepare_delivery,mark_effect_started
from sentinel_forge.courier_queue import CourierQueue
from sentinel_forge.courier_reconcile import reconcile_with_ack
from sentinel_forge.credential_reference import build_credential_reference
from sentinel_forge.credential_registry import CredentialReferenceRegistry
from sentinel_forge.credential_session import bind_session_credential
from sentinel_forge.enrollment import EnrollmentError,build_bundle
from sentinel_forge.send_sequence import SendSequenceRegistry
from sentinel_forge.session import derive_session
from sentinel_forge.trust_domain import derive_trust_domain

class FleetIsolationTests(unittest.TestCase):
 def setUp(self):
  self.td=tempfile.TemporaryDirectory();self.root=Path(self.td.name);self.q=CourierQueue(self.root/"q");self.seq=SendSequenceRegistry(self.root/"s");self.cr=CredentialReferenceRegistry(self.root/"c")
 def tearDown(self):self.td.cleanup()
 def peer(self,name):
  d=derive_trust_domain(build_bundle(forge_identity="forge",remote_identity=name,remote_role=name.split("-")[-1],permitted_actions=["receive"],permitted_target=name,policy_reference="p"))
  c=build_credential_reference(d,generation=1,key_reference=f"cred:{name}:1");self.cr.register_initial(d,c)
  s=derive_session(d,generation=1,challenge=(name.encode()*16)[:32]);b=bind_session_credential(s,d,c);return d,c,s,b
 def test_three_peers_have_independent_sequence_one(self):
  for name in ("sentinel-reaper","sentinel-scribe","sentinel-watchtower"):
   d,c,s,b=self.peer(name);payload=name.encode();a="sha256:"+hashlib.sha256(payload).hexdigest()
   p=prepare_delivery(payload=payload,artifact_identity=a,operation="deliver",domain=d,session=s,binding=b,credential=c,credential_registry=self.cr,queue=self.q,send_sequences=self.seq)
   self.assertEqual(1,p.sequence)
 def test_cross_peer_ack_cannot_close_delivery(self):
  dr,cr,sr,br=self.peer("sentinel-reaper");ds,cs,ss,bs=self.peer("sentinel-scribe")
  payload=b"reaper";a="sha256:"+hashlib.sha256(payload).hexdigest()
  pr=prepare_delivery(payload=payload,artifact_identity=a,operation="deliver",domain=dr,session=sr,binding=br,credential=cr,credential_registry=self.cr,queue=self.q,send_sequences=self.seq);mark_effect_started(pr,self.q)
  other_payload=b"scribe";oa="sha256:"+hashlib.sha256(other_payload).hexdigest()
  ps=prepare_delivery(payload=other_payload,artifact_identity=oa,operation="deliver",domain=ds,session=ss,binding=bs,credential=cs,credential_registry=self.cr,queue=self.q,send_sequences=self.seq)
  wrong=build_ack(ps.context,sequence=ps.sequence,operation="deliver",artifact_identity=oa,disposition="ACCEPTED",reason="stored")
  with self.assertRaises(EnrollmentError):reconcile_with_ack(self.q,pr.item_id,wrong,pr.context,operation="deliver",artifact_identity=a,sequence=pr.sequence)
  self.assertEqual("IN_FLIGHT",self.q.get(pr.item_id)["state"])
