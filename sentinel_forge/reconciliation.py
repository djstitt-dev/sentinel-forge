"""Conservative reconciliation for interrupted enrollment transitions."""

from __future__ import annotations
from dataclasses import dataclass
from .enrollment import EnrollmentError
from .enrollment_state import EnrollmentStateJournal
from .transition_intent import TransitionIntentLedger

@dataclass(frozen=True)
class ReconciliationAssessment:
 enrollment_id:str
 intent_id:str
 status:str
 intended_from_state:str|None
 intended_to_state:str
 journal_state:str|None
 lifecycle_state:str|None
 challenge_state:str|None
 conclusion:str

class EnrollmentReconciler:
 def __init__(self,*,journal:EnrollmentStateJournal,intents:TransitionIntentLedger,lifecycle):
  self.journal=journal;self.intents=intents;self.lifecycle=lifecycle

 def assess(self,enrollment_id:str)->ReconciliationAssessment:
  intent=self.intents.unresolved(enrollment_id)
  if not intent:raise EnrollmentError("no unresolved transition to reconcile")
  js=self.journal.state(enrollment_id);ls=self.lifecycle.state(enrollment_id)
  before=intent["from_state"];after=intent["to_state"]
  challenge_state=None
  # Remote authentication has a third durable side effect: consumption of the
  # one-time challenge. It is evidence-bearing state, so reconciliation must
  # not call the transition NOT_APPLIED after that consumption has occurred.
  if before=="STAGED" and after=="REMOTE_AUTHENTICATED":
   challenge_state=self.lifecycle.challenges.state(enrollment_id)
  if js==after and ls==after:
   conclusion="COMPLETED"
  elif js==before and ls==before:
   if before=="STAGED" and after=="REMOTE_AUTHENTICATED" and challenge_state=="CONSUMED":
    conclusion="AMBIGUOUS"
   else:
    conclusion="NOT_APPLIED"
  else:
   conclusion="AMBIGUOUS"
  return ReconciliationAssessment(enrollment_id,intent["intent_id"],intent["status"],
   before,after,js,ls,challenge_state,conclusion)

 def resolve(self,enrollment_id:str,*,operator_approved:bool,authorization_reference:str,
             expected_conclusion:str):
  if not operator_approved:raise EnrollmentError("explicit operator approval required for reconciliation")
  if not isinstance(authorization_reference,str) or not authorization_reference.strip():
   raise EnrollmentError("reconciliation authorization reference required")
  a=self.assess(enrollment_id)
  if a.conclusion!=expected_conclusion:raise EnrollmentError("reconciliation evidence changed or conclusion mismatch")
  if a.conclusion=="AMBIGUOUS":raise EnrollmentError("ambiguous transition cannot be auto-resolved")
  if a.conclusion=="COMPLETED":
   self.intents.commit(enrollment_id,a.intent_id)
   return "COMMITTED"
  if a.conclusion=="NOT_APPLIED":
   self.intents.abort(enrollment_id,a.intent_id,authorization_reference=authorization_reference)
   return "ABORTED"
  raise EnrollmentError("unsupported reconciliation conclusion")
