import random,tempfile,unittest
from pathlib import Path
from sentinel_forge.capability import NegotiatedCapabilities,require_no_downgrade
from sentinel_forge.courier_queue import CourierQueue,FINAL
from sentinel_forge.enrollment import EnrollmentError,build_bundle
from sentinel_forge.recovery_intent import RecoveryIntentLedger
from sentinel_forge.session import ReplayRegistry,derive_session
from sentinel_forge.transition_intent import TransitionIntentLedger
from sentinel_forge.trust_domain import derive_trust_domain
LEGAL={("QUEUED","PREPARED"),("PREPARED","IN_FLIGHT"),("IN_FLIGHT","ACKNOWLEDGED"),("IN_FLIGHT","REJECTED"),("IN_FLIGHT","OUTCOME_UNKNOWN"),("OUTCOME_UNKNOWN","ACKNOWLEDGED"),("OUTCOME_UNKNOWN","REJECTED"),("QUEUED","CANCELLED")}
STATES=("QUEUED","PREPARED","IN_FLIGHT","OUTCOME_UNKNOWN","ACKNOWLEDGED","REJECTED","CANCELLED")
class StatefulProperties(unittest.TestCase):
 def queue_property(self,seed):
  rng=random.Random(seed)
  with tempfile.TemporaryDirectory() as td:
   q=CourierQueue(Path(td)/"q");i=q.enqueue(relationship_id="r",artifact_identity="a",operation="d",payload_identity="p");model="QUEUED";seq=None
   for _ in range(100):
    new=rng.choice(STATES);before=q.get(i)
    try:q.transition(i,expected=model,new=new,sequence=1,acknowledgement="ack" if new=="ACKNOWLEDGED" else None)
    except EnrollmentError:self.assertEqual(before,q.get(i))
    else:
     self.assertIn((model,new),LEGAL);model=new;seq=q.get(i)["sequence"]
     if model in FINAL:
      for target in STATES:
       with self.assertRaises(EnrollmentError):q.transition(i,expected=model,new=target,sequence=1,acknowledgement="ack")
      break
   if seq is not None:self.assertEqual(1,seq)
 def replay_property(self,seed):
  rng=random.Random(seed)
  with tempfile.TemporaryDirectory() as td:
   d=derive_trust_domain(build_bundle(forge_identity="f",remote_identity="r",remote_role="reaper",permitted_actions=["x"],permitted_target="r",policy_reference="p"));s=derive_session(d,generation=1,challenge=b"R"*32);rr=ReplayRegistry(Path(td)/"r");highest=0
   for _ in range(100):
    n=rng.randint(1,highest+3)
    try:rr.accept(s,d,sequence=n)
    except EnrollmentError:self.assertNotEqual(n,highest+1)
    else:self.assertEqual(n,highest+1);highest=n
    st=rr.state(d.relationship_id)
    if st:self.assertEqual(highest,st["highest"])
 def transition_property(self,seed):
  rng=random.Random(seed)
  with tempfile.TemporaryDirectory() as td:
   x=TransitionIntentLedger(Path(td)/"i");i=x.prepare(enrollment_id="e",remote_identity="r",from_state="S",to_state="V",authorization_reference="a",reason="x");state="PREPARED"
   for _ in range(20):
    action=rng.choice(("mutate","commit","abort"))
    try:
     if action=="mutate":x.mark_mutated("e",i);new="MUTATED"
     elif action=="commit":x.commit("e",i);new="COMMITTED"
     else:x.abort("e",i,authorization_reference="op");new="ABORTED"
    except EnrollmentError:continue
    self.assertIn((state,new),{("PREPARED","MUTATED"),("MUTATED","COMMITTED"),("PREPARED","ABORTED")});state=new
    if state in {"COMMITTED","ABORTED"}:break
 def recovery_property(self,seed):
  rng=random.Random(seed)
  with tempfile.TemporaryDirectory() as td:
   x=RecoveryIntentLedger(Path(td)/"r");i=x.prepare(plan_digest="p",target="t",observation_digest="o");state="PREPARED"
   for _ in range(20):
    action=rng.choice(("apply","commit","abort"))
    try:
     if action=="apply":x.mark_applied("p",i);new="APPLIED"
     elif action=="commit":x.commit("p",i);new="COMMITTED"
     else:x.abort("p",i);new="ABORTED"
    except EnrollmentError:continue
    self.assertIn((state,new),{("PREPARED","APPLIED"),("APPLIED","COMMITTED"),("PREPARED","ABORTED")});state=new
    if state in {"COMMITTED","ABORTED"}:break
 def downgrade_property(self,seed):
  rng=random.Random(seed);p=1;s=1;features={"ack","anti-replay"}
  for _ in range(100):
   np=rng.randint(1,3);ns=rng.randint(1,3);nf=set(rng.sample(("ack","anti-replay","x"),rng.randint(0,3)))
   prev=NegotiatedCapabilities("peer",p,s,tuple(sorted(features)));cur=NegotiatedCapabilities("peer",np,ns,tuple(sorted(nf)))
   should=np>=p and ns>=s and features<=nf
   try:require_no_downgrade(prev,cur)
   except EnrollmentError:self.assertFalse(should)
   else:self.assertTrue(should);p, s, features=np,ns,nf
def _mk(name,seed):
 def t(self):getattr(self,name)(seed)
 return t
for _seed in range(5):
 for _name in ("queue_property","replay_property","transition_property","recovery_property","downgrade_property"):
  setattr(StatefulProperties,f"test_{_name}_{_seed}",_mk(_name,_seed))
