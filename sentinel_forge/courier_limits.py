"""Explicit resource/backpressure limits for Courier reference transport."""
from dataclasses import dataclass
from .enrollment import EnrollmentError

@dataclass(frozen=True)
class CourierLimits:
 max_payload_bytes:int=16*1024*1024
 max_frame_bytes:int=17*1024*1024
 max_pending_per_relationship:int=1024
 max_pending_total:int=4096

DEFAULT_LIMITS=CourierLimits()

def enforce_payload(payload:bytes,limits:CourierLimits=DEFAULT_LIMITS)->None:
 if not isinstance(payload,bytes) or not payload:raise EnrollmentError("Courier payload required")
 if len(payload)>limits.max_payload_bytes:raise EnrollmentError("Courier payload exceeds configured limit")

def enforce_backpressure(queue,relationship_id:str,limits:CourierLimits=DEFAULT_LIMITS)->None:
 pending=queue.pending(relationship_id)
 if len(pending)>=limits.max_pending_per_relationship:raise EnrollmentError("Courier relationship backpressure limit reached")
