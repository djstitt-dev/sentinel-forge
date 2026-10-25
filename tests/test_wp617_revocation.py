import dataclasses,multiprocessing,tempfile,unittest
from pathlib import Path
from sentinel_forge.enrollment import EnrollmentError
from sentinel_forge.revocation import RevocationRegistry,make_revocation,verify_revocation



def _revoke_worker(path,record,queue):
    try:
        RevocationRegistry(Path(path)).revoke(record)
        queue.put(("REVOKED",record.record_digest))
    except Exception as exc:
        queue.put((type(exc).__name__,str(exc)))

class RevocationTests(unittest.TestCase):
    def setUp(self):
        self.td=tempfile.TemporaryDirectory();self.reg=RevocationRegistry(Path(self.td.name)/"r.json")
        self.r=make_revocation(enrollment_id="enroll:abc",remote_identity="sentinel-reaper",
          operator_authorization_reference="operator-approval-7",reason="endpoint retirement",prior_state="ACTIVE")
    def tearDown(self):self.td.cleanup()
    def test_valid_record_verifies(self):self.assertTrue(verify_revocation(self.r))
    def test_tamper_fails(self):self.assertFalse(verify_revocation(dataclasses.replace(self.r,reason="changed")))
    def test_revoke_is_terminal(self):
        self.reg.revoke(self.r);self.assertTrue(self.reg.is_revoked("enroll:abc"))
        with self.assertRaises(EnrollmentError):self.reg.require_not_revoked("enroll:abc")
    def test_exact_replay_is_idempotent(self):
        self.reg.revoke(self.r);self.reg.revoke(self.r);self.assertTrue(self.reg.is_revoked("enroll:abc"))
    def test_conflicting_revocation_rejected(self):
        self.reg.revoke(self.r)
        other=make_revocation(enrollment_id="enroll:abc",remote_identity="sentinel-reaper",
          operator_authorization_reference="operator-approval-8",reason="different",prior_state="ACTIVE")
        with self.assertRaises(EnrollmentError):self.reg.revoke(other)
    def test_revocation_requires_reason(self):
        with self.assertRaises(EnrollmentError):
            make_revocation(enrollment_id="x",remote_identity="r",operator_authorization_reference="a",
              reason="",prior_state="ACTIVE")
    def test_revocation_requires_operator_authorization_reference(self):
        with self.assertRaises(EnrollmentError):
            make_revocation(enrollment_id="x",remote_identity="r",operator_authorization_reference="",
              reason="retire",prior_state="ACTIVE")
    def test_cannot_revoke_from_revoked(self):
        with self.assertRaises(EnrollmentError):
            make_revocation(enrollment_id="x",remote_identity="r",operator_authorization_reference="a",
              reason="again",prior_state="REVOKED")

if __name__=="__main__":unittest.main()


class RevocationConcurrencyTests(unittest.TestCase):
    def test_multiprocess_conflicting_revocations_have_one_semantic_winner(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"r.json"
            a=make_revocation(enrollment_id="enroll:abc",remote_identity="sentinel-reaper",
              operator_authorization_reference="operator-a",reason="retire-a",prior_state="ACTIVE")
            b=make_revocation(enrollment_id="enroll:abc",remote_identity="sentinel-reaper",
              operator_authorization_reference="operator-b",reason="retire-b",prior_state="ACTIVE")
            q=multiprocessing.Queue()
            ps=[multiprocessing.Process(target=_revoke_worker,args=(str(path),r,q))
                for r in (a,b)]
            for proc in ps:proc.start()
            for proc in ps:proc.join(5)
            self.assertTrue(all(not proc.is_alive() and proc.exitcode==0 for proc in ps),
                            [(proc.pid,proc.exitcode) for proc in ps])
            results=[q.get(timeout=2) for _ in ps]
            self.assertEqual(1,sum(1 for x in results if x[0]=="REVOKED"),results)
            self.assertEqual(1,sum(1 for x in results if x[0]=="EnrollmentError"),results)
            stored=RevocationRegistry(path).get("enroll:abc")
            self.assertIn(stored["record_digest"],{a.record_digest,b.record_digest})

    def test_multiprocess_exact_replay_remains_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"r.json"
            record=make_revocation(enrollment_id="enroll:abc",remote_identity="sentinel-reaper",
              operator_authorization_reference="operator-a",reason="retire",prior_state="ACTIVE")
            q=multiprocessing.Queue()
            ps=[multiprocessing.Process(target=_revoke_worker,args=(str(path),record,q)) for _ in range(8)]
            for proc in ps:proc.start()
            for proc in ps:proc.join(5)
            results=[q.get(timeout=2) for _ in ps]
            self.assertEqual(8,sum(1 for x in results if x[0]=="REVOKED"),results)
            self.assertEqual(record.record_digest,
                             RevocationRegistry(path).get("enroll:abc")["record_digest"])
