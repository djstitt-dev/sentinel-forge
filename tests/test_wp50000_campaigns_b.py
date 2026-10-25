import dataclasses,hashlib,random,struct,tempfile,unittest
from pathlib import Path
from sentinel_forge.courier_ack import build_ack,verify_ack
from sentinel_forge.courier_reconcile import assess_delivery
from sentinel_forge.courier_queue_v2 import IntentCourierQueue
from sentinel_forge.credential_reference import build_credential_reference
from sentinel_forge.credential_registry import CredentialReferenceRegistry
from sentinel_forge.credential_session import bind_session_credential
from sentinel_forge.delivery_intent import build_delivery_intent
from sentinel_forge.enrollment import EnrollmentError,build_bundle
from sentinel_forge.framing import frame,unframe,HEADER
from sentinel_forge.protected_wire import encode,decode
from sentinel_forge.protection_provider import protect,unprotect,ProtectedPayload
from sentinel_forge.send_sequence import SendSequenceRegistry
from sentinel_forge.session import derive_session,ReplayRegistry
from sentinel_forge.transport_contract import build_transport_context
from sentinel_forge.trust_domain import derive_trust_domain

class P:
 provider_id="TEST-P"
 def protect(self,p,*,associated_data,key_reference):
  k=(sum(associated_data)+sum(key_reference.encode()))%251+1
  return bytes(x^k for x in p)
 def unprotect(self,p,*,associated_data,key_reference):return self.protect(p,associated_data=associated_data,key_reference=key_reference)

class FakeQueue:
 def __init__(self,state,seed):
  self.r={"state":state,"relationship_id":"r","artifact_identity":f"a{seed}","operation":"d","sequence":seed+1}
 def get(self,_):return dict(self.r)

class Campaigns30to40K(unittest.TestCase):
 def done(self,n):self.assertEqual(1000,n)
 def setup_transport(self,root):
  b=build_bundle(forge_identity="forge",remote_identity="reaper",remote_role="node",permitted_actions=["receive"],permitted_target="reaper",policy_reference="p");d=derive_trust_domain(b);cr=CredentialReferenceRegistry(root/"c");c=build_credential_reference(d,generation=1,key_reference="k1");cr.register_initial(d,c);s=derive_session(d,generation=1,challenge=b"x"*16);bind=bind_session_credential(s,d,c);h,x=build_transport_context(d,s,bind,c,cr,operation="deliver",artifact_identity="sha256:a",sequence=1);return d,cr,c,s,bind,h,x

 def test_wp50000_campaign_11(self):
  n=0
  with tempfile.TemporaryDirectory() as td:
   d=derive_trust_domain(build_bundle(forge_identity="f",remote_identity="r",remote_role="n",permitted_actions=["x"],permitted_target="r",policy_reference="p"));s=derive_session(d,generation=1,challenge=b"x"*16);rr=ReplayRegistry(Path(td)/"r")
   for seed in range(1000):rr.accept(s,d,sequence=seed+1);self.assertEqual(seed+1,rr.state(d.relationship_id)["highest"]);n+=1
  self.done(n)

 def test_wp50000_campaign_12(self):
  n=0
  with tempfile.TemporaryDirectory() as td:
   d=derive_trust_domain(build_bundle(forge_identity="f",remote_identity="r",remote_role="n",permitted_actions=["x"],permitted_target="r",policy_reference="p"));s=derive_session(d,generation=1,challenge=b"x"*16);sr=SendSequenceRegistry(Path(td)/"s")
   for seed in range(1000):self.assertEqual(seed+1,sr.reserve(s,d));self.assertEqual(seed+1,sr.state(d.relationship_id)["highest"]);n+=1
  self.done(n)

 def test_wp50000_campaign_13(self):
  n=0;seen=set()
  for seed in range(1000):
   a="sha256:"+hashlib.sha256(f"a{seed}".encode()).hexdigest();i=build_delivery_intent(correlation_id=f"c{seed}",relationship_id=f"r{seed%31}",artifact_identity=a,operation=f"op{seed%7}",authorization_reference=f"auth{seed}")
   self.assertNotIn(i.delivery_id,seen);seen.add(i.delivery_id);n+=1
  self.done(n)

 def test_wp50000_campaign_14(self):
  legal={("QUEUED","PREPARED"),("PREPARED","IN_FLIGHT"),("IN_FLIGHT","ACKNOWLEDGED"),("IN_FLIGHT","REJECTED"),("IN_FLIGHT","OUTCOME_UNKNOWN"),("OUTCOME_UNKNOWN","ACKNOWLEDGED"),("OUTCOME_UNKNOWN","REJECTED"),("QUEUED","CANCELLED")}
  states=("QUEUED","PREPARED","IN_FLIGHT","OUTCOME_UNKNOWN","ACKNOWLEDGED","REJECTED","CANCELLED");n=0
  with tempfile.TemporaryDirectory() as td:
   q=IntentCourierQueue(Path(td)/"q");a="sha256:a";i=build_delivery_intent(correlation_id="c",relationship_id="r",artifact_identity=a,operation="d",authorization_reference="a");item=q.enqueue(intent=i,payload_identity=a)
   for seed in range(1000):
    astate=states[seed%len(states)];bstate=states[(seed*5+3)%len(states)]
    if (astate,bstate) in legal:bstate=astate
    before=q.get(item)
    with self.assertRaises(EnrollmentError):q.transition(item,expected=astate,new=bstate,sequence=1,acknowledgement="ack")
    self.assertEqual(before,q.get(item));n+=1
  self.done(n)

 def test_wp50000_campaign_15(self):
  n=0
  with tempfile.TemporaryDirectory() as td:
   d,cr,c,s,b,h,x=self.setup_transport(Path(td));ack=build_ack(x,sequence=1,operation="deliver",artifact_identity="sha256:a",disposition="ACCEPTED",reason="ok");fields=tuple(ack.__dataclass_fields__)
   for seed in range(1000):
    f=fields[seed%len(fields)];v=getattr(ack,f)
    if isinstance(v,int):bad=v+seed+1
    else:bad=str(v)+f"-{seed}"
    with self.assertRaises(EnrollmentError):verify_ack(dataclasses.replace(ack,**{f:bad}),x,sequence=1,operation="deliver",artifact_identity="sha256:a")
    n+=1
  self.done(n)

 def test_wp50000_campaign_16(self):
  states=("OUTCOME_UNKNOWN","ACKNOWLEDGED","REJECTED","IN_FLIGHT","QUEUED","PREPARED","CANCELLED");expected={"OUTCOME_UNKNOWN":"RECONCILIATION_REQUIRED","ACKNOWLEDGED":"COMPLETED","REJECTED":"REJECTED","IN_FLIGHT":"RECONCILIATION_REQUIRED","QUEUED":"NOT_FINAL","PREPARED":"NOT_FINAL","CANCELLED":"NOT_FINAL"};n=0
  for seed in range(1000):
   st=states[seed%len(states)];a=assess_delivery(FakeQueue(st,seed),f"i{seed}");self.assertEqual(expected[st],a.conclusion);n+=1
  self.done(n)

 def test_wp50000_campaign_17(self):
  n=0;good=frame(bytes(range(251))*4)
  for seed in range(1000):
   m=bytearray(good);idx=seed%len(m);m[idx]^=(seed%255)+1
   try:r=unframe(bytes(m))
   except EnrollmentError:pass
   else:self.assertNotEqual(r.protected_payload,good[HEADER.size:])
   n+=1
  self.done(n)

 def test_wp50000_campaign_18(self):
  n=0;good=bytearray(frame(b"x"*64));rng=random.Random(50018)
  for seed in range(1000):
   m=bytearray(good);decl=rng.randrange(0,2**32);m[6:10]=struct.pack(">I",decl)
   if decl==64:m[6:10]=struct.pack(">I",65)
   with self.assertRaises(EnrollmentError):unframe(bytes(m))
   n+=1
  self.done(n)

 def test_wp50000_campaign_19(self):
  n=0;p=P();pt=b"secret"
  for seed in range(1000):
   ad=f"ad-{seed}".encode();key=f"k-{seed}";x=protect(p,pt,associated_data=ad,key_reference=key);self.assertNotEqual(pt,x.protected_bytes);self.assertEqual(pt,unprotect(p,x,associated_data=ad,key_reference=key))
   with self.assertRaises(EnrollmentError):unprotect(p,x,associated_data=ad,key_reference=key+"x")
   n+=1
  self.done(n)

 def test_wp50000_campaign_20(self):
  n=0
  with tempfile.TemporaryDirectory() as td:
   d,cr,c,s,b,h,x=self.setup_transport(Path(td));p=P();w=encode(plaintext=b"payload",header=h,context=x,domain=d,session=s,binding=b,credential=c,credential_registry=cr,provider=p);fields=tuple(x.__dataclass_fields__)
   for seed in range(1000):
    f=fields[seed%len(fields)];v=getattr(x,f);bad=(v+seed+1 if isinstance(v,int) else str(v)+f"-{seed}")
    with self.assertRaises(EnrollmentError):decode(wire=w,header=h,context=dataclasses.replace(x,**{f:bad}),domain=d,session=s,binding=b,credential=c,credential_registry=cr,provider=p)
    n+=1
  self.done(n)
