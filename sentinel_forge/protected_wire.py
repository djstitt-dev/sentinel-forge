"""Offline composition: credential-authoritative context -> protection -> framing."""
from __future__ import annotations
from dataclasses import dataclass
from .enrollment import EnrollmentError
from .framing import frame,unframe
from .protection_provider import protect,unprotect,ProtectedPayload
from .transport_contract import associated_data,validate_transport_context

@dataclass(frozen=True)
class OfflineProtectedWire:
 provider_id:str
 key_reference:str
 frame_bytes:bytes

def encode(*,plaintext:bytes,header,context,domain,session,binding,credential,credential_registry,provider)->OfflineProtectedWire:
 validate_transport_context(header,context,domain,session,binding,credential,credential_registry,
  expected_operation=header.operation,expected_artifact_identity=header.artifact_identity,expected_sequence=header.sequence)
 if context.key_reference!=credential.key_reference:raise EnrollmentError("wire credential reference mismatch")
 p=protect(provider,plaintext,associated_data=associated_data(context),key_reference=context.key_reference)
 return OfflineProtectedWire(p.provider_id,p.key_reference,frame(p.protected_bytes))

def decode(*,wire:OfflineProtectedWire,header,context,domain,session,binding,credential,credential_registry,provider)->bytes:
 if not isinstance(wire,OfflineProtectedWire):raise EnrollmentError("protected wire contract required")
 validate_transport_context(header,context,domain,session,binding,credential,credential_registry,
  expected_operation=header.operation,expected_artifact_identity=header.artifact_identity,expected_sequence=header.sequence)
 if wire.key_reference!=context.key_reference:raise EnrollmentError("wire key reference mismatch")
 f=unframe(wire.frame_bytes)
 return unprotect(provider,ProtectedPayload(wire.provider_id,wire.key_reference,f.protected_payload),
  associated_data=associated_data(context),key_reference=context.key_reference)
