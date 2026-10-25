import multiprocessing,tempfile,unittest
from pathlib import Path
from sentinel_forge.authenticity import TestOnlyHMACSigner,TestOnlyHMACVerifier
from sentinel_forge.enrollment import EnrollmentError,build_bundle,install_bundle
from sentinel_forge.enrollment_proof import issue_challenge,authenticate_proof
from sentinel_forge.enrollment_session import ChallengeRegistry



def _issue_worker(path,bundle,challenge,queue):
    try:
        ChallengeRegistry(Path(path)).issue(bundle,challenge)
        queue.put(("ISSUED",challenge.challenge_id))
    except Exception as exc:
        queue.put((type(exc).__name__,str(exc)))

def _consume_worker(path,bundle,proof,queue):
    verifier=TestOnlyHMACVerifier({("sentinel-reaper","rk"):b"remote-secret"})
    try:
        ChallengeRegistry(Path(path)).verify_and_consume(
            bundle,proof,verifier,expected_remote_key_reference="rk")
        queue.put(("CONSUMED",proof.challenge.challenge_id))
    except Exception as exc:
        queue.put((type(exc).__name__,str(exc)))

class ChallengeRegistryTests(unittest.TestCase):
    def setUp(self):
        self.td=tempfile.TemporaryDirectory();r=Path(self.td.name);(r/"remote").mkdir()
        self.b=build_bundle(forge_identity="sentinel-forge",remote_identity="sentinel-reaper",
          remote_role="reaper",permitted_actions=["courier-receive"],permitted_target="sentinel-reaper",
          policy_reference="p1")
        self.p=install_bundle(self.b,expected_remote_identity="sentinel-reaper",root=r/"remote")
        self.s=TestOnlyHMACSigner("sentinel-reaper","rk",b"remote-secret")
        self.v=TestOnlyHMACVerifier({("sentinel-reaper","rk"):b"remote-secret"})
        self.c=issue_challenge(self.b,nonce=b"0123456789abcdef")
        self.reg=ChallengeRegistry(r/"challenges.json")
    def tearDown(self):self.td.cleanup()
    def test_verified_challenge_is_consumed_once(self):
        self.reg.issue(self.b,self.c)
        a=authenticate_proof(self.b,self.c,self.p,self.s)
        self.assertTrue(self.reg.verify_and_consume(self.b,a,self.v,expected_remote_key_reference="rk"))
        self.assertEqual("CONSUMED",self.reg.state(self.b.enrollment_id))
        with self.assertRaises(EnrollmentError):
            self.reg.verify_and_consume(self.b,a,self.v,expected_remote_key_reference="rk")
    def test_second_outstanding_challenge_rejected(self):
        self.reg.issue(self.b,self.c)
        with self.assertRaises(EnrollmentError):self.reg.issue(self.b,self.c)
    def test_bad_proof_does_not_consume_challenge(self):
        self.reg.issue(self.b,self.c)
        a=authenticate_proof(self.b,self.c,self.p,self.s)
        with self.assertRaises(EnrollmentError):
            self.reg.verify_and_consume(self.b,a,self.v,expected_remote_key_reference="wrong")
        self.assertEqual("OUTSTANDING",self.reg.state(self.b.enrollment_id))
    def test_proof_without_outstanding_challenge_rejected(self):
        a=authenticate_proof(self.b,self.c,self.p,self.s)
        with self.assertRaises(EnrollmentError):
            self.reg.verify_and_consume(self.b,a,self.v,expected_remote_key_reference="rk")

if __name__=="__main__":unittest.main()


class ChallengeRegistryConcurrencyTests(unittest.TestCase):
    def _material(self,root):
        (root/"remote").mkdir()
        b=build_bundle(forge_identity="sentinel-forge",remote_identity="sentinel-reaper",
          remote_role="reaper",permitted_actions=["courier-receive"],permitted_target="sentinel-reaper",
          policy_reference="p1")
        p=install_bundle(b,expected_remote_identity="sentinel-reaper",root=root/"remote")
        signer=TestOnlyHMACSigner("sentinel-reaper","rk",b"remote-secret")
        c=issue_challenge(b,nonce=b"0123456789abcdef")
        a=authenticate_proof(b,c,p,signer)
        return b,c,a

    def test_multiprocess_issue_has_exactly_one_outstanding_winner(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);b,c,_=self._material(root);path=root/"challenges.json";q=multiprocessing.Queue()
            ps=[multiprocessing.Process(target=_issue_worker,args=(str(path),b,c,q)) for _ in range(8)]
            for proc in ps:proc.start()
            for proc in ps:proc.join(5)
            self.assertTrue(all(not proc.is_alive() and proc.exitcode==0 for proc in ps),
                            [(proc.pid,proc.exitcode) for proc in ps])
            results=[q.get(timeout=2) for _ in ps]
            self.assertEqual(1,sum(1 for x in results if x[0]=="ISSUED"),results)
            self.assertEqual(7,sum(1 for x in results if x[0]=="EnrollmentError"),results)
            self.assertEqual("OUTSTANDING",ChallengeRegistry(path).state(b.enrollment_id))

    def test_multiprocess_consume_has_exactly_one_winner(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);b,c,a=self._material(root);path=root/"challenges.json"
            ChallengeRegistry(path).issue(b,c);q=multiprocessing.Queue()
            ps=[multiprocessing.Process(target=_consume_worker,args=(str(path),b,a,q)) for _ in range(8)]
            for proc in ps:proc.start()
            for proc in ps:proc.join(5)
            self.assertTrue(all(not proc.is_alive() and proc.exitcode==0 for proc in ps),
                            [(proc.pid,proc.exitcode) for proc in ps])
            results=[q.get(timeout=2) for _ in ps]
            self.assertEqual(1,sum(1 for x in results if x[0]=="CONSUMED"),results)
            self.assertEqual(7,sum(1 for x in results if x[0]=="EnrollmentError"),results)
            self.assertEqual("CONSUMED",ChallengeRegistry(path).state(b.enrollment_id))
