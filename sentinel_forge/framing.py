"""Offline canonical framing contract for already-protected Courier bytes.

This module performs no networking and has no knowledge of plaintext semantics.
"""
from __future__ import annotations
import hashlib,struct
from dataclasses import dataclass
from .enrollment import EnrollmentError

MAGIC=b"SFC1"
VERSION=1
TYPE_PROTECTED=1
HEADER=struct.Struct(">4sBBI32s")
MAX_PROTECTED_BYTES=17*1024*1024
MAX_FRAME_BYTES=HEADER.size+MAX_PROTECTED_BYTES

@dataclass(frozen=True)
class ProtectedFrame:
 version:int
 frame_type:int
 protected_payload:bytes
 payload_digest:str

def frame(protected_payload:bytes,*,version:int=VERSION,frame_type:int=TYPE_PROTECTED)->bytes:
 _validate_meta(version,frame_type)
 if not isinstance(protected_payload,bytes):raise EnrollmentError("protected frame payload must be bytes")
 n=len(protected_payload)
 if n<1 or n>MAX_PROTECTED_BYTES:raise EnrollmentError("protected frame payload size invalid")
 digest=hashlib.sha256(protected_payload).digest()
 return HEADER.pack(MAGIC,version,frame_type,n,digest)+protected_payload

def unframe(raw:bytes)->ProtectedFrame:
 if not isinstance(raw,bytes):raise EnrollmentError("Courier frame must be bytes")
 if len(raw)<HEADER.size:raise EnrollmentError("Courier frame truncated")
 if len(raw)>MAX_FRAME_BYTES:raise EnrollmentError("Courier frame exceeds bound")
 try:magic,version,frame_type,n,digest=HEADER.unpack(raw[:HEADER.size])
 except struct.error as exc:raise EnrollmentError("Courier frame header malformed") from exc
 if magic!=MAGIC:raise EnrollmentError("Courier frame magic invalid")
 _validate_meta(version,frame_type)
 if n<1 or n>MAX_PROTECTED_BYTES:raise EnrollmentError("Courier frame payload size invalid")
 if len(raw)!=HEADER.size+n:raise EnrollmentError("Courier frame length mismatch")
 payload=raw[HEADER.size:]
 actual=hashlib.sha256(payload).digest()
 if actual!=digest:raise EnrollmentError("Courier frame payload digest mismatch")
 return ProtectedFrame(version,frame_type,payload,"sha256:"+actual.hex())

def _validate_meta(version,frame_type):
 if not isinstance(version,int) or isinstance(version,bool) or version!=VERSION:raise EnrollmentError("Courier frame version unsupported")
 if not isinstance(frame_type,int) or isinstance(frame_type,bool) or frame_type!=TYPE_PROTECTED:raise EnrollmentError("Courier frame type unsupported")
