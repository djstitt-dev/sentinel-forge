import multiprocessing,tempfile,unittest
from pathlib import Path
from dataclasses import replace
from sentinel_forge.enrollment import EnrollmentError,build_bundle
from sentinel_forge.trust_domain import derive_trust_domain
from sentinel_forge.session import derive_session,require_session,ReplayRegistry

def domain(peer,role):
 return derive_trust_domain(build_bundle(forge_identity="sentinel-forge",remote_identity=peer,remote_role=role,
  permitted_actions=["receive"],permitted_target=peer,policy_reference="policy:v1"))



def _replay_accept_worker(path,peer,role,generation,challenge,sequence,queue):
 try:
  d=domain(peer,role);sess=derive_session(d,generation=generation,challenge=challenge)
  ReplayRegistry(Path(path)).accept(sess,d,sequence=sequence)
  queue.put(("ACCEPTED",sequence))
 except Exception as exc:
  queue.put((type(exc).__name__,str(exc)))

class SessionAntiReplayTests(unittest.TestCase):
 def setUp(self):
  self.r=domain("sentinel-reaper","reaper");self.s=domain("sentinel-scribe","scribe")
  self.rs=derive_session(self.r,generation=1,challenge=b"R"*32)
 def test_session_is_deterministic_for_same_inputs(self):
  self.assertEqual(self.rs,derive_session(self.r,generation=1,challenge=b"R"*32))
 def test_challenge_changes_session(self):
  self.assertNotEqual(self.rs.session_id,derive_session(self.r,generation=1,challenge=b"Q"*32).session_id)
 def test_relationship_changes_session(self):
  self.assertNotEqual(self.rs.session_id,derive_session(self.s,generation=1,challenge=b"R"*32).session_id)
 def test_short_challenge_rejected(self):
  with self.assertRaises(EnrollmentError):derive_session(self.r,generation=1,challenge=b"x")
 def test_cross_relationship_session_rejected(self):
  with self.assertRaises(EnrollmentError):require_session(self.rs,self.s)
 def test_tampered_session_rejected(self):
  with self.assertRaises(EnrollmentError):require_session(replace(self.rs,peer_identity="sentinel-scribe"),self.r)
 def test_contiguous_messages_accepted(self):
  with tempfile.TemporaryDirectory() as td:
   rr=ReplayRegistry(Path(td)/"r.json")
   for n in (1,2,3):rr.accept(self.rs,self.r,sequence=n)
   self.assertEqual(3,rr.state(self.r.relationship_id)["highest"])
 def test_duplicate_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   rr=ReplayRegistry(Path(td)/"r.json");rr.accept(self.rs,self.r,sequence=1)
   with self.assertRaisesRegex(EnrollmentError,"replayed"):rr.accept(self.rs,self.r,sequence=1)
 def test_out_of_order_rejected_without_advancing(self):
  with tempfile.TemporaryDirectory() as td:
   rr=ReplayRegistry(Path(td)/"r.json");rr.accept(self.rs,self.r,sequence=1)
   with self.assertRaisesRegex(EnrollmentError,"out-of-order"):rr.accept(self.rs,self.r,sequence=3)
   self.assertEqual(1,rr.state(self.r.relationship_id)["highest"])
 def test_new_generation_must_start_at_one(self):
  with tempfile.TemporaryDirectory() as td:
   rr=ReplayRegistry(Path(td)/"r.json");rr.accept(self.rs,self.r,sequence=1)
   s2=derive_session(self.r,generation=2,challenge=b"2"*32)
   with self.assertRaises(EnrollmentError):rr.accept(s2,self.r,sequence=2)
 def test_new_generation_invalidates_old_session(self):
  with tempfile.TemporaryDirectory() as td:
   rr=ReplayRegistry(Path(td)/"r.json");rr.accept(self.rs,self.r,sequence=1)
   s2=derive_session(self.r,generation=2,challenge=b"2"*32);rr.accept(s2,self.r,sequence=1)
   with self.assertRaisesRegex(EnrollmentError,"stale session"):rr.accept(self.rs,self.r,sequence=2)
 def test_generation_jump_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   rr=ReplayRegistry(Path(td)/"r.json")
   s2=derive_session(self.r,generation=2,challenge=b"2"*32)
   with self.assertRaisesRegex(EnrollmentError,"generation jump"):rr.accept(s2,self.r,sequence=1)
 def test_conflicting_session_same_generation_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   rr=ReplayRegistry(Path(td)/"r.json");rr.accept(self.rs,self.r,sequence=1)
   evil=derive_session(self.r,generation=1,challenge=b"E"*32)
   with self.assertRaisesRegex(EnrollmentError,"conflicting session"):rr.accept(evil,self.r,sequence=2)
 def test_relationships_have_independent_replay_windows(self):
  with tempfile.TemporaryDirectory() as td:
   rr=ReplayRegistry(Path(td)/"r.json");ss=derive_session(self.s,generation=1,challenge=b"S"*32)
   rr.accept(self.rs,self.r,sequence=1);rr.accept(ss,self.s,sequence=1)
   self.assertEqual(1,rr.state(self.r.relationship_id)["highest"]);self.assertEqual(1,rr.state(self.s.relationship_id)["highest"])
 def test_restart_preserves_replay_state(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"r.json";ReplayRegistry(p).accept(self.rs,self.r,sequence=1)
   with self.assertRaisesRegex(EnrollmentError,"replayed"):ReplayRegistry(p).accept(self.rs,self.r,sequence=1)
 def test_malformed_registry_fails_closed(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"r.json";p.write_text('{"bad":{"generation":"x"}}')
   with self.assertRaises(EnrollmentError):ReplayRegistry(p).state("bad")
if __name__=="__main__":unittest.main()

class SessionBoundHeaderTests(unittest.TestCase):
 def test_header_binds_session_identity_and_generation(self):
  from sentinel_forge.protected_message import build_header,validate_header
  r=domain("sentinel-reaper","reaper");s1=derive_session(r,generation=1,challenge=b"1"*32)
  h=build_header(r,s1,operation="deliver",artifact_identity="sha256:a",sequence=1)
  validate_header(h,r,s1,expected_operation="deliver",expected_artifact_identity="sha256:a",expected_sequence=1)
  wrong=derive_session(r,generation=1,challenge=b"W"*32)
  with self.assertRaises(EnrollmentError):
   validate_header(h,r,wrong,expected_operation="deliver",expected_artifact_identity="sha256:a",expected_sequence=1)
 def test_same_message_in_new_session_has_different_associated_data(self):
  from sentinel_forge.protected_message import build_header,associated_data_digest
  r=domain("sentinel-reaper","reaper")
  a=derive_session(r,generation=1,challenge=b"1"*32);b=derive_session(r,generation=2,challenge=b"2"*32)
  ha=build_header(r,a,operation="deliver",artifact_identity="sha256:a",sequence=1)
  hb=build_header(r,b,operation="deliver",artifact_identity="sha256:a",sequence=1)
  self.assertNotEqual(associated_data_digest(ha),associated_data_digest(hb))


class ReplayRegistryConcurrencyTests(unittest.TestCase):
 def test_multiprocess_same_sequence_has_exactly_one_winner(self):
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/"replay.json";q=multiprocessing.Queue()
   ps=[multiprocessing.Process(target=_replay_accept_worker,
    args=(str(path),"sentinel-reaper","reaper",1,b"R"*32,1,q)) for _ in range(8)]
   for p in ps:p.start()
   for p in ps:p.join(5)
   self.assertTrue(all(not p.is_alive() and p.exitcode==0 for p in ps),[(p.pid,p.exitcode) for p in ps])
   results=[q.get(timeout=2) for _ in ps]
   self.assertEqual(1,sum(1 for x in results if x[0]=="ACCEPTED"),results)
   self.assertEqual(7,sum(1 for x in results if x[0]=="EnrollmentError"),results)
   r=domain("sentinel-reaper","reaper")
   self.assertEqual(1,ReplayRegistry(path).state(r.relationship_id)["highest"])
 def test_multiprocess_next_sequence_has_exactly_one_winner(self):
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/"replay.json";r=domain("sentinel-reaper","reaper")
   sess=derive_session(r,generation=1,challenge=b"R"*32);ReplayRegistry(path).accept(sess,r,sequence=1)
   q=multiprocessing.Queue();ps=[multiprocessing.Process(target=_replay_accept_worker,
    args=(str(path),"sentinel-reaper","reaper",1,b"R"*32,2,q)) for _ in range(8)]
   for p in ps:p.start()
   for p in ps:p.join(5)
   results=[q.get(timeout=2) for _ in ps]
   self.assertEqual(1,sum(1 for x in results if x[0]=="ACCEPTED"),results)
   self.assertEqual(7,sum(1 for x in results if x[0]=="EnrollmentError"),results)
   self.assertEqual(2,ReplayRegistry(path).state(r.relationship_id)["highest"])
