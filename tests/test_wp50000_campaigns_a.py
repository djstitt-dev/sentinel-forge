import dataclasses,hashlib,json,tempfile,unittest
from pathlib import Path
from sentinel_forge.campaign_50k import CAMPAIGNS
from sentinel_forge.credential_reference import build_credential_reference,verify_credential_reference,require_rotation
from sentinel_forge.credential_registry import CredentialReferenceRegistry
from sentinel_forge.enrollment import EnrollmentError,EnrollmentRegistry,build_bundle
from sentinel_forge.enrollment_proof import issue_challenge
from sentinel_forge.enrollment_session import ChallengeRegistry
from sentinel_forge.recovery import RecoveryObservation,classify,SAFE_AUTOMATIC_REPAIR,OPERATOR_REQUIRED
from sentinel_forge.recovery_intent import RecoveryIntentLedger
from sentinel_forge.revocation import make_revocation,verify_revocation
from sentinel_forge.session import derive_session
from sentinel_forge.transition_intent import TransitionIntentLedger
from sentinel_forge.trust_domain import derive_trust_domain

class Campaigns20to30K(unittest.TestCase):
 def done(self,n):self.assertEqual(1000,n)
 def bundle(self,peer="reaper"):return build_bundle(forge_identity="forge",remote_identity=peer,remote_role="node",permitted_actions=["receive"],permitted_target=peer,policy_reference="p")

 def test_wp50000_campaign_01(self):
  n=0
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"e";b=self.bundle();r=EnrollmentRegistry(p);r.stage(b);base=json.loads(p.read_text());eid=b.enrollment_id
   bad_states=("MAGIC","",None,1,True,[],{},"ACTIVE ","active")
   for seed in range(1000):
    d=json.loads(json.dumps(base));rec=d[eid];kind=seed%6
    if kind==0:rec["state"]=bad_states[seed%len(bad_states)]
    elif kind==1:rec["remote_identity"]=""
    elif kind==2:rec["bundle_digest"]=[]
    elif kind==3:rec[f"extra{seed}"]=seed
    elif kind==4:rec.pop("remote_identity",None)
    else:d[""]=d.pop(eid)
    p.write_text(json.dumps(d))
    with self.assertRaises(EnrollmentError):EnrollmentRegistry(p)
    n+=1
  self.done(n)

 def test_wp50000_campaign_02(self):
  n=0;seen=set()
  for seed in range(1000):
   b=self.bundle(f"peer-{seed}");self.assertNotIn(b.enrollment_id,seen);seen.add(b.enrollment_id);self.assertEqual(f"peer-{seed}",b.remote_identity);n+=1
  self.done(n)

 def test_wp50000_campaign_03(self):
  n=0
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"c";b=self.bundle();ch=issue_challenge(b,nonce=b"x"*16);r=ChallengeRegistry(p);r.issue(b,ch);base=json.loads(p.read_text());eid=b.enrollment_id
   for seed in range(1000):
    d=json.loads(json.dumps(base));rec=d[eid];kind=seed%5
    if kind==0:rec["state"]=("BAD",None,1,True,[])[seed%5]
    elif kind==1:rec["challenge_id"]=""
    elif kind==2:rec["remote_identity"]=[]
    elif kind==3:rec[f"x{seed}"]=1
    else:rec.pop("challenge_id",None)
    p.write_text(json.dumps(d))
    with self.assertRaises(EnrollmentError):ChallengeRegistry(p)
    n+=1
  self.done(n)

 def test_wp50000_campaign_04(self):
  n=0;r=make_revocation(enrollment_id="e",remote_identity="r",operator_authorization_reference="a",reason="stop",prior_state="ACTIVE")
  fields=("enrollment_id","remote_identity","operator_authorization_reference","reason","prior_state","terminal_state","record_digest")
  for seed in range(1000):
   f=fields[seed%len(fields)];v=getattr(r,f);bad=(v+"x") if isinstance(v,str) else v
   self.assertFalse(verify_revocation(dataclasses.replace(r,**{f:bad})));n+=1
  self.done(n)

 def test_wp50000_campaign_05(self):
  n=0
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"i";x=TransitionIntentLedger(p);iid=x.prepare(enrollment_id="e",remote_identity="r",from_state="STAGED",to_state="VERIFIED",authorization_reference="a",reason="x");base=json.loads(p.read_text())
   for seed in range(1000):
    d=json.loads(json.dumps(base));rec=d["e"];kind=seed%5
    if kind==0:rec["status"]=("MAGIC","",None,1,[])[seed%5]
    elif kind==1:rec["reason"]+=str(seed)
    elif kind==2:rec["intent_id"]="intent:bad"+str(seed)
    elif kind==3:rec[f"extra{seed}"]=1
    else:rec["remote_identity"]=""
    p.write_text(json.dumps(d))
    with self.assertRaises(EnrollmentError):TransitionIntentLedger(p)
    n+=1
  self.done(n)

 def test_wp50000_campaign_06(self):
  safe=("missing_derived_cache","missing_local_index","stale_derived_cache","stale_local_index");n=0
  for seed in range(1000):
   if seed%5<4:o=RecoveryObservation(safe[seed%4],"t","i",f"d{seed}");self.assertEqual(SAFE_AUTOMATIC_REPAIR,classify(o))
   else:o=RecoveryObservation(f"unknown-{seed}","t","i","d");self.assertEqual(OPERATOR_REQUIRED,classify(o))
   n+=1
  self.done(n)

 def test_wp50000_campaign_07(self):
  n=0
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"r";x=RecoveryIntentLedger(p);iid=x.prepare(plan_digest="p",target="t",observation_digest="o");base=json.loads(p.read_text())
   for seed in range(1000):
    d=json.loads(json.dumps(base));rec=d["p"];kind=seed%5
    if kind==0:rec["status"]=("MAGIC","",None,1,[])[seed%5]
    elif kind==1:rec["target"]+=str(seed)
    elif kind==2:rec["intent_id"]="recovery-intent:bad"+str(seed)
    elif kind==3:rec[f"extra{seed}"]=1
    else:rec["observation_digest"]=""
    p.write_text(json.dumps(d))
    with self.assertRaises(EnrollmentError):RecoveryIntentLedger(p)
    n+=1
  self.done(n)

 def test_wp50000_campaign_08(self):
  n=0;d=derive_trust_domain(self.bundle())
  for seed in range(1000):
   g=seed+1;r=build_credential_reference(d,generation=g,key_reference=f"k{g}");self.assertTrue(verify_credential_reference(r,d))
   if g>1:
    prev=build_credential_reference(d,generation=g-1,key_reference=f"k{g-1}");require_rotation(prev,r,d)
   n+=1
  self.done(n)

 def test_wp50000_campaign_09(self):
  n=0
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"c";d=derive_trust_domain(self.bundle());r=CredentialReferenceRegistry(p);ref=build_credential_reference(d,generation=1,key_reference="k1");r.register_initial(d,ref);base=json.loads(p.read_text());rid=d.relationship_id
   for seed in range(1000):
    x=json.loads(json.dumps(base));rec=x["relationships"][rid];kind=seed%5
    if kind==0:rec["generation"]=True
    elif kind==1:rec["key_reference"]=""
    elif kind==2:rec["relationship_id"]="other"
    elif kind==3:rec[f"extra{seed}"]=1
    else:x["format"]="bad"
    p.write_text(json.dumps(x))
    with self.assertRaises(EnrollmentError):CredentialReferenceRegistry(p)
    n+=1
  self.done(n)

 def test_wp50000_campaign_10(self):
  n=0;d=derive_trust_domain(self.bundle());seen=set()
  for seed in range(1000):
   ch=hashlib.sha256(f"challenge-{seed}".encode()).digest();s=derive_session(d,generation=seed+1,challenge=ch);self.assertNotIn(s.session_id,seen);seen.add(s.session_id);self.assertEqual(seed+1,s.generation);n+=1
  self.done(n)

 def test_metadata_first_ten(self):
  self.assertEqual(1000,sum(1 for _ in range(CAMPAIGNS[0].start,CAMPAIGNS[0].end+1)))
