import hashlib, io, tarfile, tempfile, unittest
from pathlib import Path
from sentinel_forge.enrollment import EnrollmentError, build_bundle
from sentinel_forge.enrollment_artifact import export_artifact, validate_artifact

class EnrollmentArtifactTests(unittest.TestCase):
    def setUp(self):
        self.td=tempfile.TemporaryDirectory(); self.root=Path(self.td.name)
        self.bundle=build_bundle(forge_identity="sentinel-forge",remote_identity="sentinel-reaper",
          remote_role="reaper",permitted_actions=["courier-receive"],permitted_target="sentinel-reaper",
          policy_reference="policy-r1")
    def tearDown(self): self.td.cleanup()
    def artifact(self,name="a.tar"):
        p=self.root/name; export_artifact(self.bundle,p); return p

    def test_export_validates_for_exact_remote(self):
        self.assertTrue(validate_artifact(self.artifact(),expected_remote_identity="sentinel-reaper")["validated"])
    def test_wrong_remote_rejected(self):
        with self.assertRaises(EnrollmentError):
            validate_artifact(self.artifact(),expected_remote_identity="sentinel-watchtower")
    def test_artifact_is_byte_deterministic(self):
        a=self.artifact("a.tar"); b=self.artifact("b.tar")
        self.assertEqual(hashlib.sha256(a.read_bytes()).digest(),hashlib.sha256(b.read_bytes()).digest())
    def test_member_set_is_minimal(self):
        with tarfile.open(self.artifact(),"r") as tf:
            self.assertEqual(["MANIFEST.json","bundle.json","install.py","README.txt"],tf.getnames())
    def test_no_actual_private_key_or_credentials(self):
        with tarfile.open(self.artifact(),"r") as tf:
            blob=b"\n".join(tf.extractfile(m).read() for m in tf.getmembers()).lower()
        for forbidden in (b"-----begin private key-----",b"bearer ",b"password=",b"api_key"):
            self.assertNotIn(forbidden,blob)
    def _rewrite(self,mutator,name):
        src=self.artifact(); dst=self.root/name
        with tarfile.open(src,"r") as tin, tarfile.open(dst,"w") as tout:
            for m in tin.getmembers():
                data=tin.extractfile(m).read(); m,data=mutator(m,data); tout.addfile(m,io.BytesIO(data))
        return dst
    def test_tampered_file_is_rejected(self):
        def mutate(m,data):
            if m.name=="README.txt": data+=b"tamper"; m.size=len(data)
            return m,data
        with self.assertRaises(EnrollmentError): validate_artifact(self._rewrite(mutate,"tampered.tar"))
    def test_extra_member_is_rejected(self):
        src=self.artifact(); dst=self.root/"extra.tar"
        with tarfile.open(src,"r") as tin, tarfile.open(dst,"w") as tout:
            for m in tin.getmembers(): tout.addfile(m,io.BytesIO(tin.extractfile(m).read()))
            info=tarfile.TarInfo("evil"); info.size=1; tout.addfile(info,io.BytesIO(b"x"))
        with self.assertRaises(EnrollmentError): validate_artifact(dst)
    def test_path_traversal_member_is_rejected(self):
        src=self.artifact(); dst=self.root/"escape.tar"
        with tarfile.open(src,"r") as tin, tarfile.open(dst,"w") as tout:
            for m in tin.getmembers(): tout.addfile(m,io.BytesIO(tin.extractfile(m).read()))
            info=tarfile.TarInfo("../escape"); info.size=1; tout.addfile(info,io.BytesIO(b"x"))
        with self.assertRaises(EnrollmentError): validate_artifact(dst)
    def test_link_member_is_rejected(self):
        src=self.artifact(); dst=self.root/"link.tar"
        with tarfile.open(src,"r") as tin, tarfile.open(dst,"w") as tout:
            for m in tin.getmembers():
                if m.name=="README.txt":
                    m.type=tarfile.SYMTYPE; m.linkname="/etc/passwd"; m.size=0; tout.addfile(m)
                else: tout.addfile(m,io.BytesIO(tin.extractfile(m).read()))
        with self.assertRaises(EnrollmentError): validate_artifact(dst)
    def test_installer_is_non_effecting_stub(self):
        with tarfile.open(self.artifact(),"r") as tf: text=tf.extractfile("install.py").read().decode()
        self.assertIn("No installation or network activation performed.",text)
        for forbidden in ("subprocess","socket","systemctl","ssh "): self.assertNotIn(forbidden,text.lower())

if __name__=="__main__": unittest.main()
