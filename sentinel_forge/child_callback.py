"""Authenticated child callback state machine. Network listening is supplied separately."""
from __future__ import annotations
from dataclasses import dataclass
from .enrollment import EnrollmentError

@dataclass(frozen=True)
class ExpectedChild:
 child_identity:str;enrollment_id:str;challenge_id:str;remote_key_reference:str
@dataclass(frozen=True)
class ChildCallback:
 child_identity:str;enrollment_id:str;challenge_id:str;remote_key_reference:str;authenticated:bool
@dataclass(frozen=True)
class CallbackDecision:
 accepted:bool;state:str;notification:str

def accept_callback(expected:ExpectedChild,callback:ChildCallback,*,revoked:bool=False):
 if not isinstance(expected,ExpectedChild) or not isinstance(callback,ChildCallback):raise EnrollmentError("callback records required")
 for obj in (expected,callback):
  for v in (obj.child_identity,obj.enrollment_id,obj.challenge_id,obj.remote_key_reference):
   if not isinstance(v,str) or not v.strip():raise EnrollmentError("callback identity fields required")
 if type(callback.authenticated) is not bool or type(revoked) is not bool:raise EnrollmentError("callback booleans required")
 if revoked:raise EnrollmentError("child relationship revoked")
 if callback!=ChildCallback(expected.child_identity,expected.enrollment_id,expected.challenge_id,expected.remote_key_reference,callback.authenticated):
  raise EnrollmentError("child callback binding mismatch")
 if not callback.authenticated:raise EnrollmentError("child callback not authenticated")
 return CallbackDecision(True,"AUTHENTICATED","Sentinel Courier connected to Forge.")
