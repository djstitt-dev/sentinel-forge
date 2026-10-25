"""Algorithm-neutral protection-provider boundary.

No production algorithm or key material is implemented here. Providers receive an
opaque key reference and exact associated data; plaintext fallback is prohibited.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol
from .enrollment import EnrollmentError

@dataclass(frozen=True)
class ProtectedPayload:
 provider_id:str
 key_reference:str
 protected_bytes:bytes

class ProtectionProvider(Protocol):
 provider_id:str
 def protect(self,plaintext:bytes,*,associated_data:bytes,key_reference:str)->bytes:...
 def unprotect(self,protected:bytes,*,associated_data:bytes,key_reference:str)->bytes:...

def protect(provider:ProtectionProvider,plaintext:bytes,*,associated_data:bytes,key_reference:str)->ProtectedPayload:
 _inputs(plaintext,associated_data,key_reference)
 pid=_provider_id(provider)
 try:out=provider.protect(plaintext,associated_data=associated_data,key_reference=key_reference)
 except Exception as exc:raise EnrollmentError("protection provider failed closed") from exc
 if not isinstance(out,bytes) or not out:raise EnrollmentError("protection provider returned invalid protected payload")
 if out==plaintext:raise EnrollmentError("protection provider plaintext fallback prohibited")
 return ProtectedPayload(pid,key_reference,out)

def unprotect(provider:ProtectionProvider,payload:ProtectedPayload,*,associated_data:bytes,key_reference:str)->bytes:
 if not isinstance(payload,ProtectedPayload):raise EnrollmentError("protected payload contract required")
 _inputs(payload.protected_bytes,associated_data,key_reference)
 pid=_provider_id(provider)
 if payload.provider_id!=pid or payload.key_reference!=key_reference:raise EnrollmentError("protection provider binding mismatch")
 try:out=provider.unprotect(payload.protected_bytes,associated_data=associated_data,key_reference=key_reference)
 except Exception as exc:raise EnrollmentError("protection provider failed closed") from exc
 if not isinstance(out,bytes) or not out:raise EnrollmentError("protection provider returned invalid plaintext")
 return out

def _inputs(data,ad,key):
 if not isinstance(data,bytes) or not data:raise EnrollmentError("protection bytes required")
 if not isinstance(ad,bytes) or not ad:raise EnrollmentError("protection associated data required")
 if not isinstance(key,str) or not key.strip():raise EnrollmentError("protection key reference required")
def _provider_id(p):
 v=getattr(p,"provider_id",None)
 if not isinstance(v,str) or not v.strip():raise EnrollmentError("protection provider identity required")
 return v
