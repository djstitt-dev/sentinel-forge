import dataclasses,hashlib,itertools,json,tempfile,unittest
from pathlib import Path
from sentinel_forge.assistant_independence import *
from sentinel_forge.authenticity import *
from sentinel_forge.consistency_audit import audit_relationship
from sentinel_forge.courier_queue_v2 import IntentCourierQueue
from sentinel_forge.credential_reference import build_credential_reference
from sentinel_forge.credential_registry import CredentialReferenceRegistry
from sentinel_forge.credential_session import bind_session_credential
from sentinel_forge.delivery_intent import build_delivery_intent
from sentinel_forge.enrollment import EnrollmentError,EnrollmentRegistry,build_bundle
from sentinel_forge.evidence import EvidenceJournal,EvidenceError
from sentinel_forge.evidence_anchor import build_evidence_head,verify_against_head
from sentinel_forge.framing import frame,unframe
from sentinel_forge.protected_receive import accept_protected_inbound
from sentinel_forge.protected_wire import encode
from sentinel_forge.release_evidence import build_release_evidence,verify_release_evidence
from sentinel_forge.revocation import RevocationRegistry
from sentinel_forge.send_sequence import SendSequenceRegistry
from sentinel_forge.session import ReplayRegistry,derive_session
from sentinel_forge.state_backup import *
from sentinel_forge.transport_contract import build_transport_context
from sentinel_forge.transport_readiness import assess_transport_readiness
from sentinel_forge.trust_domain import derive_trust_domain
from sentinel_forge.recovery import RecoveryObservation,classify,OPERATOR_REQUIRED

HEAD="d5b8f07542bde35c78795c126ad5c89698f3cb08"
class P:
 provider_id="TEST-P"
 def protect(self,p,*,associated_data,key_reference):
  k=(sum(associated_data)+sum(key_reference.encode()))%251+1;return bytes(x^k for x in p)
 def unprotect(self,p,*,associated_data,key_reference):return self.protect(p,associated_data=associated_data,key_reference=key_reference)

class Campaigns40to50K(unittest.TestCase):
 def done(self,n):self.assertEqual(1000,n)
 def transport(self,root):
  b=build_bundle(forge_identity="forge",remote_identity="reaper",remote_role="node",permitted_actions=["receive"],permitted_target="reaper",policy_reference="p");d=derive_trust_domain(b);cr=CredentialReferenceRegistry(root/"cred");c=build_credential_reference(d,generation=1,key_reference="k1");cr.register_initial(d,c);s=derive_session(d,generation=1,challenge=b"x"*16);bind=bind_session_credential(s,d,c);payload=b"payload";a="sha256:"+hashlib.sha256(payload).hexdigest();h,x=build_transport_context(d,s,bind,c,cr,operation="deliver",artifact_identity=a,sequence=1);p=P();w=encode(plaintext=payload,header=h,context=x,domain=d,session=s,binding=bind,credential=c,credential_registry=cr,provider=p);return b,d,cr,c,s,bind,payload,a,h,x,p,w

 def test_wp50000_campaign_21(self):
  n=0
  with tempfile.TemporaryDirectory() as td:
   r=Path(td);b,d,cr,c,s,bind,payload,a,h,x,p,w=self.transport(r);rr=ReplayRegistry(r/"replay")
   base=w.frame_bytes
   for seed in range(1000):
    m=bytearray(base);idx=seed%len(m);m[idx]^=(seed%255)+1;bad=dataclasses.replace(w,frame_bytes=bytes(m))
    with self.assertRaises(EnrollmentError):accept_protected_inbound(wire=bad,header=h,context=x,domain=d,session=s,binding=bind,credential=c,credential_registry=cr,replay_registry=rr,provider=p,expected_operation="deliver",expected_artifact_identity=a,expected_sequence=1)
    self.assertIsNone(rr.state(d.relationship_id));n+=1
  self.done(n)

 def test_wp50000_campaign_22(self):
  n=0;s=TestOnlyHMACSigner("forge","k",b"k"*32);v=TestOnlyHMACVerifier({("forge","k"):b"k"*32});e=create_envelope(b"subject",s)
  for seed in range(1000):
   if seed%2:self.assertFalse(verify_envelope(b"subject",e,v,expected_signer_identity=f"forge-{seed}",expected_key_reference="k"))
   else:self.assertFalse(verify_envelope(b"subject",e,v,expected_signer_identity="forge",expected_key_reference=f"k-{seed}"))
   n+=1
  self.done(n)

 def test_wp50000_campaign_23(self):
  n=0
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"e";j=EvidenceJournal(p)
   for i in range(25):j.append(correlation_id=f"c{i}",reason=f"r{i}")
   base=p.read_text().splitlines()
   for seed in range(1000):
    rows=list(base);idx=seed%len(rows);d=json.loads(rows[idx]);d["reason"]=str(d["reason"])+f"-m{seed}";rows[idx]=json.dumps(d);p.write_text("\n".join(rows)+"\n")
    with self.assertRaises(EvidenceError):j.verify()
    n+=1
   p.write_text("\n".join(base)+"\n")
  self.done(n)

 def test_wp50000_campaign_24(self):
  n=0
  with tempfile.TemporaryDirectory() as td:
   e=EvidenceJournal(Path(td)/"e");e.append(correlation_id="c");h=build_evidence_head(e,journal_identity="forge")
   for seed in range(1000):
    bad=dataclasses.replace(h,checkpoint_digest="bad-"+str(seed))
    with self.assertRaises(EvidenceError):verify_against_head(e,bad)
    n+=1
  self.done(n)

 def test_wp50000_campaign_25(self):
  n=0
  with tempfile.TemporaryDirectory() as td:
   r=Path(td);files={}
   for name in ALLOWED:p=r/name;p.write_bytes(name.encode());files[name]=p
   m=build_state_backup_manifest(relationship_id="rel",files=files)
   for seed in range(1000):
    if seed%3==0:bad=dataclasses.replace(m,manifest_digest="sha256:"+hashlib.sha256(str(seed).encode()).hexdigest())
    elif seed%3==1:
     rows=list(m.files);name,dig,size=rows[seed%len(rows)];rows[seed%len(rows)]=(name,dig,size+seed+1);bad=dataclasses.replace(m,files=tuple(rows))
    else:bad=dataclasses.replace(m,relationship_id=f"rel-{seed}")
    with self.assertRaises(EnrollmentError):verify_restored_state(bad,expected_relationship_id="rel",files=files)
    n+=1
  self.done(n)

 def test_wp50000_campaign_26(self):
  n=0;e=build_release_evidence(repository_head=HEAD,test_count=1184,checkpoint_end=20000,offline_invariants_passed=True,production_ready=False,blockers=("NETWORK_UNAPPROVED","INDEPENDENCE_UNVERIFIED"))
  for seed in range(1000):
   if seed%4==0:bad=dataclasses.replace(e,test_count=e.test_count+seed+1)
   elif seed%4==1:bad=dataclasses.replace(e,checkpoint_end=e.checkpoint_end+seed+1)
   elif seed%4==2:bad=dataclasses.replace(e,repository_head=("0"*39)+hex(seed%16)[2:])
   else:bad=dataclasses.replace(e,evidence_digest="sha256:"+hashlib.sha256(str(seed).encode()).hexdigest())
   with self.assertRaises(EnrollmentError):verify_release_evidence(bad)
   n+=1
  self.done(n)

 def test_wp50000_campaign_27(self):
  names=("revoked","current_credential","current_session","unresolved_effect","unresolved_recovery","audit_available","assistant_independence_verified","protection_provider_approved","network_provider_approved");good=(False,True,True,False,False,True,True,True,True);patterns=list(itertools.product((False,True),repeat=9));n=0
  for seed in range(1000):
   bits=patterns[seed%512];kw=dict(zip(names,bits));state="ACTIVE" if seed<512 else ("STAGED","VERIFIED","REVOKED","UNKNOWN")[seed%4];r=assess_transport_readiness(enrollment_state=state,**kw);self.assertEqual(state=="ACTIVE" and bits==good,r.ready);n+=1
  self.done(n)

 def test_wp50000_campaign_28(self):
  cats=sorted(REQUIRED_CATEGORIES);n=0
  for seed in range(1000):
   mask=seed%(1<<len(cats));observed=[c for i,c in enumerate(cats) if mask&(1<<i)];inv=build_inventory(forge_identity="forge",collector_method="test",categories_observed=observed,findings=[]);a=assess_independence(inv);self.assertEqual(len(observed)==len(cats),a.passed);n+=1
  self.done(n)

 def test_wp50000_campaign_29(self):
  n=0;seen=set()
  for seed in range(1000):
   peer=f"peer-{seed}";b=build_bundle(forge_identity="forge",remote_identity=peer,remote_role="node",permitted_actions=["receive"],permitted_target=peer,policy_reference="p");d=derive_trust_domain(b);self.assertNotIn(d.relationship_id,seen);seen.add(d.relationship_id);n+=1
  self.done(n)

 def test_wp50000_campaign_30(self):
  n=0
  for seed in range(1000):
   payload=f"payload-{seed}".encode();a="sha256:"+hashlib.sha256(payload).hexdigest();i=build_delivery_intent(correlation_id=f"c{seed}",relationship_id=f"rel-{seed%41}",artifact_identity=a,operation="deliver",authorization_reference=f"auth-{seed}");self.assertEqual(a,i.artifact_identity);self.assertEqual(payload,unframe(frame(payload)).protected_payload)
   o=RecoveryObservation(f"unknown-{seed}","target",a,"integrated");self.assertEqual(OPERATOR_REQUIRED,classify(o))
   ready=(seed%37==0);r=assess_transport_readiness(enrollment_state="ACTIVE",revoked=False,current_credential=True,current_session=True,unresolved_effect=False,unresolved_recovery=False,audit_available=True,assistant_independence_verified=ready,protection_provider_approved=ready,network_provider_approved=ready);self.assertEqual(ready,r.ready);n+=1
  self.done(n)
