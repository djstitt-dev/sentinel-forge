import json,unittest
from sentinel_forge.endpoint_platform import PlatformFamily,build_platform_profile
from sentinel_forge.endpoint_package import generate_endpoint_package
from sentinel_forge.peer_configuration import PeerProfile
FP="SHA256:abcdefghijklmnopqrstuvwxyzABCDE1234567890"
def peer():
 return PeerProfile("new-peer","managed-peer","192.0.2.50","sentineladmin",22,FP,("courier.send","courier.receive","health.report"))
class EndpointPackageTests(unittest.TestCase):
 def test_all_supported_families_generate_inert_packages(self):
  for family in PlatformFamily:
   with self.subTest(family=family):
    p=generate_endpoint_package(peer(),family=family)
    m=json.loads(p.manifest_json)
    self.assertFalse(m["operational_effects_enabled"]);self.assertFalse(m["contains_secret_material"])
    self.assertIn("BLOCKED",p.preflight_script);self.assertIn("operator approval",p.install_script.lower())
 def test_windows_profiles(self):
  for f in (PlatformFamily.WINDOWS_10,PlatformFamily.WINDOWS_11):
   p=build_platform_profile(f);self.assertEqual("PowerShell",p.shell);self.assertIn("Service Control",p.service_manager)
 def test_linux_profiles(self):
  for f in (PlatformFamily.UBUNTU_DESKTOP,PlatformFamily.UBUNTU_SERVER,PlatformFamily.DEBIAN_WORKSTATION,PlatformFamily.DEBIAN_SERVER):
   p=build_platform_profile(f);self.assertEqual("systemd",p.service_manager);self.assertEqual("apt/dpkg",p.package_manager)
 def test_platform_packages_are_distinct(self):
  a=generate_endpoint_package(peer(),family=PlatformFamily.WINDOWS_10)
  b=generate_endpoint_package(peer(),family=PlatformFamily.UBUNTU_SERVER)
  self.assertNotEqual(a.package_digest,b.package_digest)
 def test_version_is_not_falsely_hardcoded(self):
  p=generate_endpoint_package(peer(),family=PlatformFamily.UBUNTU_SERVER,version="auto")
  self.assertEqual("auto",p.platform.version);self.assertIn("/etc/os-release",p.preflight_script)

class EndpointMaterializationTests(unittest.TestCase):
 def test_materializes_private_files_without_overwrite(self):
  import tempfile
  from pathlib import Path
  from sentinel_forge.endpoint_package import materialize_endpoint_package
  with tempfile.TemporaryDirectory() as td:
   root=Path(td)/"pkg"
   pkg=generate_endpoint_package(peer(),family=PlatformFamily.DEBIAN_SERVER)
   files=materialize_endpoint_package(pkg,root)
   self.assertEqual(4,len(files))
   self.assertEqual(0o600,(root/"manifest.json").stat().st_mode & 0o777)
   with self.assertRaises(FileExistsError):materialize_endpoint_package(pkg,root)

class OperationalInstallerRenderTests(unittest.TestCase):
 def test_linux_installer_stages_without_starting(self):
  from sentinel_forge.endpoint_package import render_operational_linux_installer
  p=generate_endpoint_package(peer(),family=PlatformFamily.DEBIAN_SERVER)
  s=render_operational_linux_installer(p)
  self.assertIn("systemctl enable",s);self.assertNotIn("systemctl start",s)
  self.assertIn("dedicated sentinel-courier service account",s)
 def test_windows_installer_stages_without_starting(self):
  from sentinel_forge.endpoint_package import render_operational_windows_installer
  p=generate_endpoint_package(peer(),family=PlatformFamily.WINDOWS_11)
  s=render_operational_windows_installer(p)
  self.assertIn("New-Service",s);self.assertNotIn("Start-Service",s)
  self.assertIn("reconcile explicitly",s)
 def test_rollbacks_preserve_state_evidence(self):
  from sentinel_forge.endpoint_package import render_operational_linux_rollback,render_operational_windows_rollback
  l=generate_endpoint_package(peer(),family=PlatformFamily.UBUNTU_SERVER)
  w=generate_endpoint_package(peer(),family=PlatformFamily.WINDOWS_10)
  self.assertIn("retained for evidence",render_operational_linux_rollback(l))
  self.assertIn("retained for evidence",render_operational_windows_rollback(w))

class OperationalMaterializationTests(unittest.TestCase):
 def test_all_platforms_materialize_operational_package(self):
  import tempfile
  from pathlib import Path
  from sentinel_forge.endpoint_package import materialize_operational_endpoint_package
  for family in PlatformFamily:
   with self.subTest(family=family),tempfile.TemporaryDirectory() as td:
    pkg=generate_endpoint_package(peer(),family=family)
    root=Path(td)/"pkg";files=materialize_operational_endpoint_package(pkg,root)
    self.assertGreaterEqual(len(files),8)
    self.assertTrue((root/"endpoint.json").exists())
    for f in files:self.assertEqual(0o600,f.stat().st_mode & 0o777)
 def test_activation_requires_verified_receipt(self):
  from sentinel_forge.endpoint_package import render_activation_script
  for family in (PlatformFamily.WINDOWS_11,PlatformFamily.DEBIAN_SERVER):
   s=render_activation_script(generate_endpoint_package(peer(),family=family))
   self.assertIn("activation receipt",s)
   self.assertIn("plan",s.lower())
   self.assertIn("peer",s.lower())
 def test_install_and_activation_are_separate(self):
  from sentinel_forge.endpoint_package import render_operational_linux_installer,render_activation_script
  p=generate_endpoint_package(peer(),family=PlatformFamily.UBUNTU_SERVER)
  self.assertNotIn("systemctl start",render_operational_linux_installer(p))
  self.assertIn("systemctl start",render_activation_script(p))
