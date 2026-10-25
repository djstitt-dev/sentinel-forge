"""Crash-aware journal-guarded enrollment authority facade."""

from __future__ import annotations
from .enrollment import EnrollmentBundle,EnrollmentProof,EnrollmentError
from .enrollment_lifecycle import GuardedEnrollmentLifecycle
from .enrollment_state import EnrollmentStateJournal
from .transition_intent import TransitionIntentLedger

class JournaledEnrollmentLifecycle:
 def __init__(self,lifecycle:GuardedEnrollmentLifecycle,journal:EnrollmentStateJournal,
              intents:TransitionIntentLedger|None=None):
  self.lifecycle=lifecycle;self.journal=journal
  self.intents=intents or TransitionIntentLedger(journal.path.with_suffix(".intents.json"))
 def _clean(self,eid):
  if self.intents.unresolved(eid):raise EnrollmentError("RECONCILIATION_REQUIRED: unresolved enrollment transition")
 def _run(self,bundle,*,to_state,auth,reason,mutation,defer_commit=False):
  eid=bundle.enrollment_id;self._clean(eid);before=self.journal.state(eid)
  iid=self.intents.prepare(enrollment_id=eid,remote_identity=bundle.remote_identity,
   from_state=before,to_state=to_state,authorization_reference=auth,reason=reason)
  try:mutation()
  except EnrollmentError:
   # A deterministic policy/authorization rejection raised by the guarded
   # lifecycle is known not to have crossed the state-mutation boundary.
   self.intents.abort(eid,iid,authorization_reference=auth)
   raise
  except Exception:
   # Unknown exceptions may have occurred during a mutation. Preserve PREPARED
   # so restart requires evidence-based reconciliation rather than blind retry.
   raise
  self.intents.mark_mutated(eid,iid)
  self.journal.transition(enrollment_id=eid,remote_identity=bundle.remote_identity,new_state=to_state,
   authorization_reference=auth,reason=reason)
  if defer_commit:return iid
  self.intents.commit(eid,iid)
  return None
 def commit_deferred(self,enrollment_id:str,intent_id:str):
  intent=self.intents.unresolved(enrollment_id)
  if intent is None or intent["intent_id"]!=intent_id or intent["status"]!="MUTATED":
   raise EnrollmentError("deferred transition intent is not ready to commit")
  self.intents.commit(enrollment_id,intent_id)
 def stage_deferred(self,bundle:EnrollmentBundle,*,authorization_reference:str):
  if self.journal.state(bundle.enrollment_id) is not None:raise EnrollmentError("journal already knows enrollment")
  return self._run(bundle,to_state="STAGED",auth=authorization_reference,reason="enrollment staged",
   mutation=lambda:self.lifecycle.stage(bundle),defer_commit=True)
 def stage(self,bundle:EnrollmentBundle,*,authorization_reference:str):
  if self.journal.state(bundle.enrollment_id) is not None:raise EnrollmentError("journal already knows enrollment")
  self._run(bundle,to_state="STAGED",auth=authorization_reference,reason="enrollment staged",
   mutation=lambda:self.lifecycle.stage(bundle))
 def verify_authenticated_remote_deferred(self,bundle,authenticated,verifier,*,expected_remote_key_reference:str,authorization_reference:str):
  if self.journal.state(bundle.enrollment_id)!="STAGED":raise EnrollmentError("journal does not authorize remote authentication")
  holder={}
  iid=self._run(bundle,to_state="REMOTE_AUTHENTICATED",auth=authorization_reference,reason="remote identity authenticated",
   mutation=lambda:holder.setdefault("ok",self.lifecycle.verify_authenticated_remote(bundle,authenticated,verifier,
    expected_remote_key_reference=expected_remote_key_reference)),defer_commit=True)
  return holder["ok"],iid
 def verify_authenticated_remote(self,bundle,authenticated,verifier,*,expected_remote_key_reference:str,authorization_reference:str):
  if self.journal.state(bundle.enrollment_id)!="STAGED":raise EnrollmentError("journal does not authorize remote authentication")
  holder={}
  self._run(bundle,to_state="REMOTE_AUTHENTICATED",auth=authorization_reference,reason="remote identity authenticated",
   mutation=lambda:holder.setdefault("ok",self.lifecycle.verify_authenticated_remote(bundle,authenticated,verifier,
    expected_remote_key_reference=expected_remote_key_reference)))
  return holder["ok"]
 def accept_installation_proof_deferred(self,bundle:EnrollmentBundle,proof:EnrollmentProof,*,authorization_reference:str):
  if self.journal.state(bundle.enrollment_id)!="REMOTE_AUTHENTICATED":raise EnrollmentError("journal requires authenticated remote before proof acceptance")
  return self._run(bundle,to_state="VERIFIED",auth=authorization_reference,reason="installation proof accepted",
   mutation=lambda:self.lifecycle.accept_installation_proof(bundle,proof),defer_commit=True)
 def accept_installation_proof(self,bundle:EnrollmentBundle,proof:EnrollmentProof,*,authorization_reference:str):
  if self.journal.state(bundle.enrollment_id)!="REMOTE_AUTHENTICATED":raise EnrollmentError("journal requires authenticated remote before proof acceptance")
  self._run(bundle,to_state="VERIFIED",auth=authorization_reference,reason="installation proof accepted",
   mutation=lambda:self.lifecycle.accept_installation_proof(bundle,proof))
 def activate_deferred(self,bundle:EnrollmentBundle,*,operator_approved:bool,authorization_reference:str):
  if self.journal.state(bundle.enrollment_id)!="VERIFIED":raise EnrollmentError("journal does not authorize activation")
  return self._run(bundle,to_state="ACTIVE",auth=authorization_reference,reason="operator activation",
   mutation=lambda:self.lifecycle.activate(bundle.enrollment_id,operator_approved=operator_approved),defer_commit=True)
 def activate(self,bundle:EnrollmentBundle,*,operator_approved:bool,authorization_reference:str):
  if self.journal.state(bundle.enrollment_id)!="VERIFIED":raise EnrollmentError("journal does not authorize activation")
  self._run(bundle,to_state="ACTIVE",auth=authorization_reference,reason="operator activation",
   mutation=lambda:self.lifecycle.activate(bundle.enrollment_id,operator_approved=operator_approved))
 def revoke_deferred(self,bundle:EnrollmentBundle,*,operator_authorization_reference:str,reason:str):
  state=self.journal.state(bundle.enrollment_id)
  if state not in {"STAGED","REMOTE_AUTHENTICATED","VERIFIED","ACTIVE"}:raise EnrollmentError("journal does not authorize revocation")
  holder={}
  iid=self._run(bundle,to_state="REVOKED",auth=operator_authorization_reference,reason=reason,
   mutation=lambda:holder.setdefault("record",self.lifecycle.revoke(bundle,
    operator_authorization_reference=operator_authorization_reference,reason=reason)),defer_commit=True)
  return holder["record"],iid
 def revoke(self,bundle:EnrollmentBundle,*,operator_authorization_reference:str,reason:str):
  state=self.journal.state(bundle.enrollment_id)
  if state not in {"STAGED","REMOTE_AUTHENTICATED","VERIFIED","ACTIVE"}:raise EnrollmentError("journal does not authorize revocation")
  holder={}
  self._run(bundle,to_state="REVOKED",auth=operator_authorization_reference,reason=reason,
   mutation=lambda:holder.setdefault("record",self.lifecycle.revoke(bundle,
    operator_authorization_reference=operator_authorization_reference,reason=reason)))
  return holder["record"]
 def state(self,enrollment_id:str):
  self._clean(enrollment_id)
  journal_state=self.journal.state(enrollment_id);lifecycle_state=self.lifecycle.state(enrollment_id)
  if journal_state!=lifecycle_state:raise EnrollmentError("RECONCILIATION_REQUIRED: enrollment authority stores disagree")
  return journal_state
