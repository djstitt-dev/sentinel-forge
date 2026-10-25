"""Forge-side visual Courier connection state rendering."""
from __future__ import annotations
from dataclasses import dataclass
from .enrollment import EnrollmentError
STATES=("STAGED","BOOTSTRAPPING","CALLBACK_RECEIVED","AUTHENTICATED","PROTECTED","ACTIVE","REVOKED","BLOCKED")
@dataclass(frozen=True)
class ConnectionView:
 child_identity:str;state:str;protection:str;detail:str
 def render(self):
  mark={"ACTIVE":"●","PROTECTED":"◆","AUTHENTICATED":"◇","BLOCKED":"!","REVOKED":"×"}.get(self.state,"○")
  return f"{mark} {self.child_identity:<24} {self.state:<18} {self.protection:<14} {self.detail}"
def view(*,child_identity,state,protected=False,detail=""):
 if not isinstance(child_identity,str) or not child_identity.strip():raise EnrollmentError("child identity required")
 if state not in STATES:raise EnrollmentError("connection state invalid")
 if type(protected) is not bool:raise EnrollmentError("protected flag must be boolean")
 if state=="ACTIVE" and not protected:raise EnrollmentError("active Courier connection must be protected")
 return ConnectionView(child_identity,state,"AES-256-GCM" if protected else "NOT-PROTECTED",detail)
