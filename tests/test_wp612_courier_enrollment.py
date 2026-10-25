import dataclasses, json, multiprocessing
from pathlib import Path
import tempfile, unittest
from sentinel_forge.enrollment import (EnrollmentError,EnrollmentRegistry,build_bundle,
    install_bundle,verify_bundle,verify_proof)



def _stage_worker(path,bundle,queue):
    try:
        EnrollmentRegistry(Path(path)).stage(bundle)
        queue.put(("STAGED",bundle.enrollment_id))
    except Exception as exc:
        queue.put((type(exc).__name__,str(exc)))

class CourierEnrollmentTests(unittest.TestCase):
    def setUp(self):
        self.td=tempfile.TemporaryDirectory(); self.root=Path(self.td.name); (self.root/"remote").mkdir()
        self.bundle=build_bundle(forge_identity="sentinel-forge",remote_identity="sentinel-reaper",
          remote_role="reaper",permitted_actions=["courier-receive"],
          permitted_target="sentinel-reaper",policy_reference="policy-reaper-1")
        self.registry=EnrollmentRegistry(self.root/"forge-registry.json")
    def tearDown(self): self.td.cleanup()

    def test_bundle_is_deterministic_and_integrity_verifiable(self):
        b2=build_bundle(forge_identity="sentinel-forge",remote_identity="sentinel-reaper",
          remote_role="reaper",permitted_actions=["courier-receive"],
          permitted_target="sentinel-reaper",policy_reference="policy-reaper-1")
        self.assertEqual(self.bundle,b2); self.assertTrue(verify_bundle(self.bundle))

    def test_bundle_is_host_bound(self):
        with self.assertRaises(EnrollmentError):
            install_bundle(self.bundle,expected_remote_identity="sentinel-scribe",root=self.root/"remote")

    def test_tampered_bundle_is_rejected(self):
        bad=dataclasses.replace(self.bundle,remote_identity="evil-host")
        self.assertFalse(verify_bundle(bad))
        with self.assertRaises(EnrollmentError):
            install_bundle(bad,expected_remote_identity="evil-host",root=self.root/"remote")

    def test_install_emits_verifiable_proof(self):
        proof=install_bundle(self.bundle,expected_remote_identity="sentinel-reaper",root=self.root/"remote")
        self.assertTrue(verify_proof(self.bundle,proof)); self.assertEqual("INSTALLED",proof.installer_outcome)

    def test_bundle_is_one_time_at_remote(self):
        install_bundle(self.bundle,expected_remote_identity="sentinel-reaper",root=self.root/"remote")
        with self.assertRaises(EnrollmentError):
            install_bundle(self.bundle,expected_remote_identity="sentinel-reaper",root=self.root/"remote")

    def test_incomplete_staging_requires_reconciliation_not_blind_retry(self):
        remote=self.root/"remote"
        parent=remote/"var"/"lib"/"sentinel-courier"/"enrollments"
        parent.mkdir(parents=True)
        import hashlib
        name=hashlib.sha256(self.bundle.enrollment_id.encode()).hexdigest()
        (parent/(name+".staging")).mkdir()
        with self.assertRaises(EnrollmentError):
            install_bundle(self.bundle,expected_remote_identity="sentinel-reaper",root=remote)

    def test_proof_tampering_is_rejected(self):
        proof=install_bundle(self.bundle,expected_remote_identity="sentinel-reaper",root=self.root/"remote")
        bad=dataclasses.replace(proof,remote_identity="other")
        self.assertFalse(verify_proof(self.bundle,bad))

    def test_raw_registry_cannot_bypass_remote_authentication(self):
        self.registry.stage(self.bundle); self.assertEqual("STAGED",self.registry.state(self.bundle.enrollment_id))
        proof=install_bundle(self.bundle,expected_remote_identity="sentinel-reaper",root=self.root/"remote")
        with self.assertRaisesRegex(EnrollmentError,"authenticated remote"):
            self.registry.accept_proof(self.bundle,proof)
        self.assertEqual("STAGED",self.registry.state(self.bundle.enrollment_id))
        self.assertFalse(hasattr(self.registry,"activate"))


    def test_unstaged_proof_is_rejected(self):
        proof=install_bundle(self.bundle,expected_remote_identity="sentinel-reaper",root=self.root/"remote")
        with self.assertRaises(EnrollmentError): self.registry.accept_proof(self.bundle,proof)

    def test_bundle_for_reaper_cannot_enroll_watchtower(self):
        with self.assertRaises(EnrollmentError):
            install_bundle(self.bundle,expected_remote_identity="sentinel-watchtower",root=self.root/"remote")

    def test_installation_has_no_service_or_network_effect(self):
        install_bundle(self.bundle,expected_remote_identity="sentinel-reaper",root=self.root/"remote")
        files={p.name for p in (self.root/"remote").rglob("*") if p.is_file()}
        self.assertEqual({"policy.json","consumed.json"},files)

    def test_registry_malformed_state_fails_closed(self):
        p=self.root/"bad.json"; p.write_text("{bad")
        with self.assertRaises(EnrollmentError): EnrollmentRegistry(p).state("x")

if __name__=="__main__": unittest.main()


class EnrollmentRegistryConcurrencyTests(unittest.TestCase):
    def test_multiprocess_stage_has_exactly_one_winner(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"registry.json"
            bundle=build_bundle(forge_identity="sentinel-forge",remote_identity="sentinel-reaper",
              remote_role="reaper",permitted_actions=["courier-receive"],permitted_target="sentinel-reaper",
              policy_reference="p1")
            q=multiprocessing.Queue()
            ps=[multiprocessing.Process(target=_stage_worker,args=(str(path),bundle,q)) for _ in range(8)]
            for proc in ps:proc.start()
            for proc in ps:proc.join(5)
            self.assertTrue(all(not proc.is_alive() and proc.exitcode==0 for proc in ps),
                            [(proc.pid,proc.exitcode) for proc in ps])
            results=[q.get(timeout=2) for _ in ps]
            self.assertEqual(1,sum(1 for x in results if x[0]=="STAGED"),results)
            self.assertEqual(7,sum(1 for x in results if x[0]=="EnrollmentError"),results)
            self.assertEqual("STAGED",EnrollmentRegistry(path).state(bundle.enrollment_id))
