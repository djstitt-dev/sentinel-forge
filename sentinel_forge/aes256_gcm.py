"""AES-256-GCM Courier protection provider. Key storage/provisioning is external."""
from __future__ import annotations
from dataclasses import dataclass
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag
from .enrollment import EnrollmentError

ALGORITHM="AES-256-GCM"
NONCE_BYTES=12
KEY_BYTES=32

@dataclass(frozen=True)
class Aes256GcmPacket:
 nonce:bytes
 ciphertext:bytes
 def wire(self)->bytes:return self.nonce+self.ciphertext

class Aes256GcmProvider:
 provider_id="sentinel-aes256-gcm-v1"
 def __init__(self,key_resolver):
  if not callable(key_resolver):raise EnrollmentError("key resolver required")
  self._resolve=key_resolver
 def _key(self,ref):
  if not isinstance(ref,str) or not ref.strip():raise EnrollmentError("key reference required")
  k=self._resolve(ref)
  if not isinstance(k,bytes) or len(k)!=KEY_BYTES:raise EnrollmentError("AES-256 key must be exactly 32 bytes")
  return k
 def protect(self,plaintext:bytes,associated_data:bytes,key_reference:str)->bytes:
  if not isinstance(plaintext,bytes) or not plaintext:raise EnrollmentError("plaintext bytes required")
  if not isinstance(associated_data,bytes) or not associated_data:raise EnrollmentError("associated data required")
  nonce=os.urandom(NONCE_BYTES)
  return nonce+AESGCM(self._key(key_reference)).encrypt(nonce,plaintext,associated_data)
 def unprotect(self,protected:bytes,associated_data:bytes,key_reference:str)->bytes:
  if not isinstance(protected,bytes) or len(protected)<=NONCE_BYTES+16:raise EnrollmentError("protected AES-GCM packet invalid")
  if not isinstance(associated_data,bytes) or not associated_data:raise EnrollmentError("associated data required")
  nonce,ct=protected[:NONCE_BYTES],protected[NONCE_BYTES:]
  try:return AESGCM(self._key(key_reference)).decrypt(nonce,ct,associated_data)
  except InvalidTag as e:raise EnrollmentError("AES-256-GCM authentication failed") from e
