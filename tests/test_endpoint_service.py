import unittest
from sentinel_forge.endpoint_service import build_endpoint_service_artifacts
from sentinel_forge.endpoint_platform import PlatformFamily,build_platform_profile
from sentinel_forge.peer_configuration import PeerProfile,compile_peer_configuration
FP="SHA256:abcdefghijklmnopqrstuvwxyzABCDE1234567890"
PLAN=compile_peer_configuration(PeerProfile("new-peer","managed-peer","192.0.2.5","admin",22,FP,("courier.send","courier.receive")))
class EndpointServiceTests(unittest.TestCase):
 def test_linux_hardening(self):
  a=build_endpoint_service_artifacts(build_platform_profile(PlatformFamily.UBUNTU_SERVER),PLAN)
  for x in ("NoNewPrivileges=yes","ProtectSystem=strict","PrivateDevices=yes","MemoryDenyWriteExecute=yes"):
   self.assertIn(x,a.service_definition)
  self.assertNotIn("PRIVATE KEY",a.config_json)
 def test_windows_service_is_least_privilege_named_service(self):
  a=build_endpoint_service_artifacts(build_platform_profile(PlatformFamily.WINDOWS_11),PLAN)
  self.assertIn("NT SERVICE",a.service_definition);self.assertIn("Forge relationship only",a.service_definition)
 def test_config_is_staged_not_active(self):
  for f in PlatformFamily:
   a=build_endpoint_service_artifacts(build_platform_profile(f),PLAN)
   self.assertIn('"activation_state": "STAGED"',a.config_json)
   self.assertIn("AES-256-GCM",a.config_json)
