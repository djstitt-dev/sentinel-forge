import json,multiprocessing,tempfile,unittest
from pathlib import Path
from sentinel_forge.enrollment import EnrollmentError
from sentinel_forge.enrollment_state import EnrollmentStateJournal



def _state_append_worker(path,index,queue):
 try:
  rec=EnrollmentStateJournal(Path(path)).transition(
   enrollment_id=f"e{index}",remote_identity=f"peer{index}",new_state="STAGED",
   authorization_reference=f"op{index}",reason="concurrent stage")
  queue.put(("OK",rec["sequence"],rec["enrollment_id"]))
 except Exception as exc:
  queue.put((type(exc).__name__,str(exc)))

class EnrollmentStateJournalTests(unittest.TestCase):
 def setUp(self):
  self.td=tempfile.TemporaryDirectory();self.p=Path(self.td.name)/"state.jsonl";self.j=EnrollmentStateJournal(self.p)
 def tearDown(self):self.td.cleanup()
 def t(self,state,reason="test"):
  return self.j.transition(enrollment_id="e1",remote_identity="reaper",new_state=state,
   authorization_reference="op-1",reason=reason)
 def test_valid_monotonic_lifecycle(self):
  for s in ("STAGED","REMOTE_AUTHENTICATED","VERIFIED","ACTIVE","REVOKED"):self.t(s)
  self.assertEqual("REVOKED",self.j.state("e1"))
 def test_cannot_jump_staged_to_active(self):
  self.t("STAGED")
  with self.assertRaises(EnrollmentError):self.t("ACTIVE")
 def test_revoked_is_terminal(self):
  self.t("STAGED");self.t("REVOKED")
  with self.assertRaises(EnrollmentError):self.t("STAGED")
 def test_remote_identity_cannot_change(self):
  self.t("STAGED")
  with self.assertRaises(EnrollmentError):
   self.j.transition(enrollment_id="e1",remote_identity="watchtower",new_state="VERIFIED",
    authorization_reference="op",reason="bad")
 def test_truncation_fails_closed(self):
  self.t("STAGED");self.p.write_bytes(self.p.read_bytes()[:-1])
  with self.assertRaises(EnrollmentError):self.j.verify()
 def test_record_modification_detected(self):
  self.t("STAGED");raw=self.p.read_text().replace('"reason":"test"','"reason":"evil"');self.p.write_text(raw)
  with self.assertRaises(EnrollmentError):self.j.verify()
 def test_middle_record_deletion_detected(self):
  self.t("STAGED");self.t("REMOTE_AUTHENTICATED");self.t("VERIFIED");self.t("ACTIVE")
  lines=self.p.read_text().splitlines(True);self.p.write_text(lines[0]+lines[2])
  with self.assertRaises(EnrollmentError):self.j.verify()
 def test_forged_active_without_chain_rejected(self):
  self.t("STAGED");r=json.loads(self.p.read_text().splitlines()[0]);r["new_state"]="ACTIVE"
  self.p.write_text(json.dumps(r)+"\n")
  with self.assertRaises(EnrollmentError):self.j.verify()
 def test_restart_recovers_state(self):
  self.t("STAGED");self.t("REMOTE_AUTHENTICATED");self.t("VERIFIED")
  self.assertEqual("VERIFIED",EnrollmentStateJournal(self.p).state("e1"))
 def test_exact_state_replay_is_not_a_transition(self):
  self.t("STAGED")
  with self.assertRaises(EnrollmentError):self.t("STAGED")
 def test_multiple_enrollments_share_global_chain(self):
  self.t("STAGED")
  self.j.transition(enrollment_id="e2",remote_identity="watchtower",new_state="STAGED",
   authorization_reference="op-2",reason="stage")
  self.assertEqual("STAGED",self.j.state("e1"));self.assertEqual("STAGED",self.j.state("e2"))

if __name__=="__main__":unittest.main()


class EnrollmentStateJournalConcurrencyTests(unittest.TestCase):
 def test_multiprocess_append_preserves_one_global_chain(self):
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/"state.jsonl";EnrollmentStateJournal(path);q=multiprocessing.Queue()
   ps=[multiprocessing.Process(target=_state_append_worker,args=(str(path),i,q)) for i in range(8)]
   for proc in ps:proc.start()
   for proc in ps:proc.join(5)
   self.assertTrue(all(not proc.is_alive() and proc.exitcode==0 for proc in ps),
                   [(proc.pid,proc.exitcode) for proc in ps])
   results=[q.get(timeout=2) for _ in ps]
   self.assertTrue(all(x[0]=="OK" for x in results),results)
   self.assertEqual(list(range(1,9)),sorted(x[1] for x in results))
   records=EnrollmentStateJournal(path).verify()
   self.assertEqual(8,len(records));self.assertEqual(list(range(1,9)),[r["sequence"] for r in records])
