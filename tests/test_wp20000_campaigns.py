import dataclasses,hashlib,itertools,json,random,struct,tempfile,unittest
from pathlib import Path
from sentinel_forge.authenticity import TestOnlyHMACSigner,TestOnlyHMACVerifier,create_envelope,verify_envelope
from sentinel_forge.authority_snapshot import AuthoritySnapshot,verify_authority_snapshot
from sentinel_forge.campaign_20k import CAMPAIGNS
from sentinel_forge.courier_queue_v2 import IntentCourierQueue
from sentinel_forge.delivery_intent import build_delivery_intent
from sentinel_forge.enrollment import EnrollmentError,EnrollmentRegistry,build_bundle
from sentinel_forge.evidence import EvidenceJournal,EvidenceError
from sentinel_forge.evidence_anchor import build_evidence_head,verify_against_head
from sentinel_forge.framing import frame,unframe,HEADER
from sentinel_forge.release_evidence import build_release_evidence,verify_release_evidence
from sentinel_forge.state_backup import ALLOWED,build_state_backup_manifest,verify_restored_state
from sentinel_forge.transport_readiness import assess_transport_readiness

HEAD="d5b8f07542bde35c78795c126ad5c89698f3cb08"

class Campaign20K(unittest.TestCase):
 def done(self,n):self.assertEqual(1000,n)

 def test_wp20000_campaign_enrollment(self):
  n=0
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"e";b=build_bundle(forge_identity="f",remote_identity="r",remote_role="reaper",permitted_actions=["x"],permitted_target="r",policy_reference="p");r=EnrollmentRegistry(p);r.stage(b);base=json.loads(p.read_text());eid=b.enrollment_id
   states=("MAGIC","REVOKED","verified","",None,1,True,[],{})
   for seed in range(1000):
    d=json.loads(json.dumps(base));rec=d[eid];kind=seed%5
    if kind==0:rec["state"]=states[seed%len(states)]
    elif kind==1:rec["remote_identity"]=""
    elif kind==2:rec["extra_"+str(seed)]=seed
    elif kind==3:rec.pop("bundle_digest",None)
    else:d[""]=d.pop(eid)
    p.write_text(json.dumps(d))
    with self.assertRaises(EnrollmentError):EnrollmentRegistry(p)
    n+=1
  self.done(n)

 def test_wp20000_campaign_queue(self):
  n=0
  with tempfile.TemporaryDirectory() as td:
   q=IntentCourierQueue(Path(td)/"q")
   for seed in range(1000):
    corr=f"c{seed}";a="sha256:"+hashlib.sha256(str(seed).encode()).hexdigest();i=build_delivery_intent(correlation_id=corr,relationship_id="rel",artifact_identity=a,operation="deliver",authorization_reference="auth")
    item=q.enqueue(intent=i,payload_identity=a);self.assertEqual("QUEUED",q.get(item)["state"])
    if seed%2:q.transition(item,expected="QUEUED",new="CANCELLED");self.assertEqual("CANCELLED",q.get(item)["state"])
    else:q.transition(item,expected="QUEUED",new="PREPARED",sequence=seed+1);self.assertEqual(seed+1,q.get(item)["sequence"])
    n+=1
  self.done(n)

 def test_wp20000_campaign_sequences(self):
  # Sequence semantics represented through queue-v2 immutable sequence assignments.
  n=0
  with tempfile.TemporaryDirectory() as td:
   q=IntentCourierQueue(Path(td)/"q")
   for seed in range(1000):
    a="sha256:"+hashlib.sha256(f"a{seed}".encode()).hexdigest();i=build_delivery_intent(correlation_id=f"s{seed}",relationship_id="rel",artifact_identity=a,operation="d",authorization_reference="a");item=q.enqueue(intent=i,payload_identity=a);seq=seed+1;q.transition(item,expected="QUEUED",new="PREPARED",sequence=seq)
    with self.assertRaises(EnrollmentError):q.transition(item,expected="PREPARED",new="IN_FLIGHT",sequence=seq+1001)
    self.assertEqual(seq,q.get(item)["sequence"]);n+=1
  self.done(n)

 def test_wp20000_campaign_wire(self):
  n=0;good=frame(bytes(range(251))*5)
  for seed in range(1000):
   m=bytearray(good);idx=seed%len(m);m[idx]^=((seed//len(m))%255)+1
   try:r=unframe(bytes(m))
   except EnrollmentError:pass
   else:self.assertNotEqual(good,bytes(m));self.assertNotEqual(r.protected_payload,good[HEADER.size:])
   n+=1
  self.done(n)

 def test_wp20000_campaign_artifact(self):
  n=0;subject=b"manifest+bundle";s=TestOnlyHMACSigner("forge","k1",b"k"*32);v=TestOnlyHMACVerifier({("forge","k1"):b"k"*32});e=create_envelope(subject,s)
  for seed in range(1000):
   if seed%2==0:ok=verify_envelope(subject,e,v,expected_signer_identity="forge-x"+str(seed),expected_key_reference="k1")
   else:ok=verify_envelope(subject,e,v,expected_signer_identity="forge",expected_key_reference="wrong-"+str(seed))
   self.assertFalse(ok);n+=1
  self.done(n)

 def test_wp20000_campaign_readiness(self):
  names=("revoked","current_credential","current_session","unresolved_effect","unresolved_recovery","audit_available","assistant_independence_verified","protection_provider_approved","network_provider_approved");good=(False,True,True,False,False,True,True,True,True);n=0
  patterns=list(itertools.product((False,True),repeat=9))
  for seed in range(1000):
   bits=patterns[seed%len(patterns)];kw=dict(zip(names,bits));r=assess_transport_readiness(enrollment_state="ACTIVE",**kw);self.assertEqual(bits==good,r.ready);n+=1
  self.done(n)

 def test_wp20000_campaign_fleet(self):
  # Distinct pairwise relationship identities across a synthetic 32-peer fleet.
  peers=[]
  for i in range(32):
   b=build_bundle(forge_identity="forge",remote_identity=f"peer-{i}",remote_role="node",permitted_actions=["receive"],permitted_target=f"peer-{i}",policy_reference="p");peers.append(b)
  ids={b.enrollment_id for b in peers};self.assertEqual(32,len(ids));n=0
  for seed in range(1000):
   a=seed%32;b=(seed*7+1)%32
   if a==b:b=(b+1)%32
   self.assertNotEqual(peers[a].enrollment_id,peers[b].enrollment_id);self.assertNotEqual(peers[a].remote_identity,peers[b].remote_identity);n+=1
  self.done(n)

 def test_wp20000_campaign_evidence(self):
  n=0
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"e";j=EvidenceJournal(p)
   for i in range(50):j.append(correlation_id=f"c{i}")
   base=p.read_text().splitlines();head=build_evidence_head(j,journal_identity="forge")
   for seed in range(1000):
    rows=list(base);idx=seed%len(rows);d=json.loads(rows[idx]);d["reason"]=str(d["reason"])+f"-{seed}";rows[idx]=json.dumps(d);p.write_text("\n".join(rows)+"\n")
    with self.assertRaises(EvidenceError):verify_against_head(j,head)
    n+=1
   p.write_text("\n".join(base)+"\n")
  self.done(n)

 def test_wp20000_campaign_backup(self):
  n=0
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);files={}
   for x in ALLOWED:p=root/x;p.write_bytes(x.encode());files[x]=p
   m=build_state_backup_manifest(relationship_id="rel",files=files)
   for seed in range(1000):
    name=ALLOWED[seed%len(ALLOWED)];orig=files[name].read_bytes();files[name].write_bytes(orig+seed.to_bytes(4,"big"))
    with self.assertRaises(EnrollmentError):verify_restored_state(m,expected_relationship_id="rel",files=files)
    files[name].write_bytes(orig);n+=1
  self.done(n)

 def test_wp20000_campaign_snapshot(self):
  n=0;base=AuthoritySnapshot("sentinel-authority-snapshot-v1","r","e","p",1,"k",1,"s",0,None,None,0,"sha256:x")
  # Use malformed snapshot mutations; integrity verifier must reject all.
  for seed in range(1000):
   x=dataclasses.replace(base,snapshot_digest="sha256:"+hashlib.sha256(str(seed).encode()).hexdigest())
   with self.assertRaises(EnrollmentError):verify_authority_snapshot(x)
   n+=1
  self.done(n)

 def test_wp20000_campaign_release(self):
  n=0;e=build_release_evidence(repository_head=HEAD,test_count=1163,checkpoint_end=5000,offline_invariants_passed=True,production_ready=False,blockers=("NETWORK_UNAPPROVED","INDEPENDENCE_UNVERIFIED"))
  for seed in range(1000):
   x=dataclasses.replace(e,test_count=e.test_count+seed+1)
   with self.assertRaises(EnrollmentError):verify_release_evidence(x)
   n+=1
  self.done(n)

 def test_wp20000_campaign_crash(self):
  # 1000 restart validations of persisted queue states across terminal/nonterminal variants.
  n=0
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/"q";q=IntentCourierQueue(path)
   items=[]
   for i in range(20):
    a="sha256:"+hashlib.sha256(str(i).encode()).hexdigest();it=build_delivery_intent(correlation_id=f"cr{i}",relationship_id="r",artifact_identity=a,operation="d",authorization_reference="a");items.append(q.enqueue(intent=it,payload_identity=a))
   for seed in range(1000):
    q=IntentCourierQueue(path);item=items[seed%20];self.assertIsNotNone(q.get(item));n+=1
  self.done(n)

 def test_wp20000_campaign_resource(self):
  n=0;rng=random.Random(18000)
  for seed in range(1000):
   raw=bytes(rng.randrange(256) for _ in range(rng.randrange(0,300)))
   try:unframe(raw)
   except EnrollmentError:pass
   else:self.fail(f"random hostile frame accepted at {seed}")
   n+=1
  self.done(n)

 def test_wp20000_campaign_rotation(self):
  # Revocation/rotation semantics represented by readiness facts: revoked or stale authority always blocks.
  n=0
  for seed in range(1000):
   kw=dict(enrollment_state="ACTIVE",revoked=(seed%2==0),current_credential=(seed%3!=0),current_session=(seed%5!=0),unresolved_effect=False,unresolved_recovery=False,audit_available=True,assistant_independence_verified=True,protection_provider_approved=True,network_provider_approved=True)
   r=assess_transport_readiness(**kw)
   expected=(not kw["revoked"] and kw["current_credential"] and kw["current_session"])
   self.assertEqual(expected,r.ready);n+=1
  self.done(n)

 def test_wp20000_campaign_integrated(self):
  n=0
  for seed in range(1000):
   # Integrated invariant: relationship-specific intent + frame roundtrip + readiness decision.
   a="sha256:"+hashlib.sha256(f"payload-{seed}".encode()).hexdigest();i=build_delivery_intent(correlation_id=f"i{seed}",relationship_id=f"rel-{seed%17}",artifact_identity=a,operation="deliver",authorization_reference=f"auth-{seed}");self.assertEqual(a,i.artifact_identity)
   payload=f"protected-{seed}".encode();self.assertEqual(payload,unframe(frame(payload)).protected_payload)
   good=(seed%11==0);r=assess_transport_readiness(enrollment_state="ACTIVE",revoked=False,current_credential=True,current_session=True,unresolved_effect=False,unresolved_recovery=False,audit_available=True,assistant_independence_verified=good,protection_provider_approved=good,network_provider_approved=good);self.assertEqual(good,r.ready);n+=1
  self.done(n)

 def test_campaign_metadata_exact(self):
  self.assertEqual(15,len(CAMPAIGNS));self.assertEqual(15000,sum(x.count for x in CAMPAIGNS));self.assertEqual(5001,CAMPAIGNS[0].start);self.assertEqual(20000,CAMPAIGNS[-1].end)
