"""Fail-closed inbound Courier acceptance pipeline, without network I/O."""
from __future__ import annotations
import hashlib
from dataclasses import dataclass
from .courier_ack import CourierAcknowledgement,build_ack
from .enrollment import EnrollmentError
from .transport_contract import accept_transport_message

@dataclass(frozen=True)
class ReceiveResult:
 acknowledgement:CourierAcknowledgement
 payload_identity:str

def payload_identity(payload:bytes)->str:
 if not isinstance(payload,bytes) or not payload:raise EnrollmentError("Courier inbound payload required")
 return "sha256:"+hashlib.sha256(payload).hexdigest()

def accept_inbound(*,payload:bytes,header,context,domain,session,binding,credential,
                   credential_registry,replay_registry,expected_operation:str,
                   expected_artifact_identity:str,expected_sequence:int)->ReceiveResult:
 # Validate content identity before anti-replay state is consumed.
 actual=payload_identity(payload)
 if actual!=expected_artifact_identity:raise EnrollmentError("Courier inbound artifact identity mismatch")
 # All relationship/session/current-credential/context validation occurs before
 # ReplayRegistry.accept inside accept_transport_message.
 accept_transport_message(header,context,domain,session,binding,credential,credential_registry,
  replay_registry,expected_operation=expected_operation,
  expected_artifact_identity=expected_artifact_identity,expected_sequence=expected_sequence)
 ack=build_ack(context,sequence=expected_sequence,operation=expected_operation,
               artifact_identity=expected_artifact_identity,disposition="ACCEPTED",reason="validated")
 return ReceiveResult(ack,actual)
