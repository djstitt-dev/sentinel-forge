import unittest
from typing import Protocol,runtime_checkable
from sentinel_forge.enrollment import EnrollmentError

@runtime_checkable
class FrameProvider(Protocol):
 def frame(self,*,associated_data:bytes,protected_payload:bytes)->bytes:...
 def unframe(self,wire:bytes)->tuple[bytes,bytes]:...

@runtime_checkable
class ProtectionProvider(Protocol):
 def protect(self,*,plaintext:bytes,associated_data:bytes,key_reference:str)->bytes:...
 def unprotect(self,*,protected_payload:bytes,associated_data:bytes,key_reference:str)->bytes:...

def require_provider_shape(frame_provider,protection_provider):
 if not isinstance(frame_provider,FrameProvider):raise EnrollmentError("WP6.36 framing provider interface invalid")
 if not isinstance(protection_provider,ProtectionProvider):raise EnrollmentError("WP6.37 protection provider interface invalid")

class GoodFrame:
 def frame(self,*,associated_data,protected_payload):return associated_data+b"|"+protected_payload
 def unframe(self,wire):return tuple(wire.split(b"|",1))
class GoodProtect:
 def protect(self,*,plaintext,associated_data,key_reference):return b"P"+plaintext
 def unprotect(self,*,protected_payload,associated_data,key_reference):return protected_payload[1:]
class BadFrame:pass
class BadProtect:
 def protect(self,*,plaintext,associated_data,key_reference):return plaintext

class LandingZoneTests(unittest.TestCase):
 def test_expected_interfaces_are_narrow(self):require_provider_shape(GoodFrame(),GoodProtect())
 def test_missing_frame_surface_fails(self):
  with self.assertRaises(EnrollmentError):require_provider_shape(BadFrame(),GoodProtect())
 def test_missing_unprotect_surface_fails(self):
  with self.assertRaises(EnrollmentError):require_provider_shape(GoodFrame(),BadProtect())
 def test_protection_interface_requires_associated_data_and_key_reference(self):
  import inspect
  sig=inspect.signature(ProtectionProvider.protect);self.assertIn("associated_data",sig.parameters);self.assertIn("key_reference",sig.parameters)
 def test_framing_only_handles_already_protected_payload(self):
  import inspect
  sig=inspect.signature(FrameProvider.frame);self.assertIn("protected_payload",sig.parameters);self.assertNotIn("plaintext",sig.parameters)
