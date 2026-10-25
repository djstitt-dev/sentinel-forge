"""Offline protected-wire inbound acceptance; anti-replay is consumed last."""
from __future__ import annotations
import hashlib
from dataclasses import dataclass
from .courier_ack import CourierAcknowledgement,build_ack
from .enrollment import EnrollmentError
from .protected_wire import decode
from .transport_contract import accept_transport_message

@dataclass(frozen=True)
class ProtectedReceiveResult:
 acknowledgement:CourierAcknowledgement
 payload_identity:str
 plaintext:bytes

def accept_protected_inbound(*,wire,header,context,domain,session,binding,credential,credential_registry,replay_registry,provider,expected_operation:str,expected_artifact_identity:str,expected_sequence:int)->ProtectedReceiveResult:
 # decode validates current credential/session/context, frame integrity and provider bindings.
 plaintext=decode(wire=wire,header=header,context=context,domain=domain,session=session,binding=binding,credential=credential,credential_registry=credential_registry,provider=provider)
 actual="sha256:"+hashlib.sha256(plaintext).hexdigest()
 if actual!=expected_artifact_identity:raise EnrollmentError("protected inbound artifact identity mismatch")
 # Revalidate authority immediately before consuming replay state.
 accept_transport_message(header,context,domain,session,binding,credential,credential_registry,replay_registry,
  expected_operation=expected_operation,expected_artifact_identity=expected_artifact_identity,expected_sequence=expected_sequence)
 ack=build_ack(context,sequence=expected_sequence,operation=expected_operation,artifact_identity=expected_artifact_identity,disposition="ACCEPTED",reason="protected-validated")
 return ProtectedReceiveResult(ack,actual,plaintext)
