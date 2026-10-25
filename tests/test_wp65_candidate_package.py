import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from sentinel_forge.package import PackageError, build_manifest, verify_manifest

class CandidatePackageTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = Path(self.td.name)
        (self.root/"a.txt").write_bytes(b"alpha\n")
        (self.root/"sub").mkdir()
        (self.root/"sub"/"b.bin").write_bytes(bytes(range(32)))

    def tearDown(self):
        self.td.cleanup()

    def build(self, paths=("a.txt","sub/b.bin")):
        return build_manifest(self.root, paths, work_package_revision="rev-1",
                              artifact_type_class="candidate",
                              classification_handling="approved-class")

    def test_deterministic_identity_independent_of_input_order(self):
        self.assertEqual(self.build(), self.build(("sub/b.bin","a.txt")))

    def test_identity_changes_when_content_changes(self):
        before = self.build()
        (self.root/"a.txt").write_bytes(b"changed\n")
        after = self.build()
        self.assertNotEqual(before.artifact_id, after.artifact_id)
        self.assertNotEqual(before.integrity_reference, after.integrity_reference)

    def test_manifest_exposes_wp62_artifact_identity(self):
        ident = self.build().artifact_identity()
        self.assertEqual("rev-1", ident["source_work_package_revision"])
        self.assertEqual("COMPLETE", ident["completeness_state"])
        self.assertEqual(ident["artifact_id"], ident["integrity_reference"])

    def test_verify_detects_substitution(self):
        m = self.build()
        self.assertTrue(verify_manifest(self.root, m))
        (self.root/"a.txt").write_bytes(b"evil\n")
        self.assertFalse(verify_manifest(self.root, m))

    def test_path_escape_rejected(self):
        outside = self.root.parent/"outside-wp65"
        outside.write_text("x")
        try:
            with self.assertRaises(PackageError):
                self.build(("../outside-wp65",))
        finally:
            outside.unlink(missing_ok=True)

    def test_absolute_path_rejected(self):
        with self.assertRaises(PackageError):
            self.build(("/etc/passwd",))

    def test_symlink_rejected(self):
        (self.root/"link").symlink_to("a.txt")
        with self.assertRaises(PackageError):
            self.build(("link",))

    def test_hardlink_rejected(self):
        os.link(self.root/"a.txt", self.root/"hard")
        with self.assertRaises(PackageError):
            self.build(("a.txt",))

    def test_pathname_swap_during_open_fails_closed(self):
        import sentinel_forge.package as package_module
        real_open = package_module.os.open
        replacement = self.root/"replacement"
        replacement.write_bytes(b"replacement\n")
        def swapping_open(path, flags):
            if Path(path).name == "a.txt":
                (self.root/"a.txt").unlink()
                replacement.rename(self.root/"a.txt")
            return real_open(path, flags)
        with mock.patch.object(package_module.os, "open", side_effect=swapping_open):
            with self.assertRaises(PackageError):
                self.build(("a.txt",))

    def test_empty_package_rejected(self):
        with self.assertRaises(PackageError):
            self.build(())

    def test_missing_metadata_rejected(self):
        with self.assertRaises(PackageError):
            build_manifest(self.root, ["a.txt"], work_package_revision="",
                           artifact_type_class="candidate",
                           classification_handling="approved-class")

    def test_cli_build_and_verify(self):
        p = subprocess.run([sys.executable,"-m","sentinel_forge.package_cli","build",
            "--root",str(self.root),"--revision","rev-1","--artifact-type","candidate",
            "--classification","approved-class","a.txt","sub/b.bin"],
            text=True,capture_output=True,check=False)
        self.assertEqual(0,p.returncode,p.stderr)
        manifest=self.root/"manifest.json"; manifest.write_text(p.stdout)
        v=subprocess.run([sys.executable,"-m","sentinel_forge.package_cli","verify",
            "--root",str(self.root),str(manifest)],text=True,capture_output=True,check=False)
        self.assertEqual(0,v.returncode,v.stderr)
        self.assertTrue(json.loads(v.stdout)["verified"])

    def test_cli_verify_rejects_changed_file(self):
        m=self.build()
        path=self.root/"manifest.json"
        path.write_text(json.dumps(m.as_dict()))
        (self.root/"a.txt").write_bytes(b"changed\n")
        p=subprocess.run([sys.executable,"-m","sentinel_forge.package_cli","verify",
            "--root",str(self.root),str(path)],text=True,capture_output=True,check=False)
        self.assertEqual(1,p.returncode)
        self.assertFalse(json.loads(p.stdout)["verified"])

if __name__ == "__main__":
    unittest.main()
