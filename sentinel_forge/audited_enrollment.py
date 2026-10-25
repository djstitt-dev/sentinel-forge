"""Required-audit wrapper for enrollment lifecycle and reconciliation."""

from __future__ import annotations
from .enrollment import EnrollmentError
from .evidence import EvidenceJournal,EvidenceError

class AuditOutcomeUnknown(EnrollmentError):pass

class AuditedEnrollmentLifecycle:
 def __init__(self,lifecycle,journal:EvidenceJournal):
  self.lifecycle=lifecycle;self.journal=journal
 def _base(self,bundle,auth):
  return dict(correlation_id=bundle.enrollment_id,actor=bundle.forge_identity,
   target=bundle.remote_identity,authorization_reference=auth,input_identity=bundle.payload_digest,
   source_context="courier-enrollment-lifecycle",collector_method="local-reference",
   timestamp=None,time_uncertainty="UNKNOWN")
 def _run(self,bundle,auth,operation,fn):
  base=self._base(bundle,auth)
  # Required pre-audit. Failure here blocks the authority action.
  self.journal.append(**base,output_identity=None,outcome="AUTHORITY_ATTEMPT_REQUESTED",reason=operation)
  try:
   result=fn()
  except Exception as exc:
   try:self.journal.append(**base,output_identity=None,outcome="AUTHORITY_ACTION_FAILED",reason=type(exc).__name__)
   except EvidenceError:pass
   raise
  try:
   self.journal.append(**base,output_identity=None,outcome="AUTHORITY_ACTION_COMPLETED",reason=operation)
  except EvidenceError as exc:
   raise AuditOutcomeUnknown("authority action completed but final required audit is unavailable; reconciliation required") from exc
  return result
 def _run_deferred(self,bundle,auth,operation,fn):
  base=self._base(bundle,auth)
  self.journal.append(**base,output_identity=None,outcome="AUTHORITY_ATTEMPT_REQUESTED",reason=operation)
  try:
   result,iid=fn()
  except Exception as exc:
   try:self.journal.append(**base,output_identity=None,outcome="AUTHORITY_ACTION_FAILED",reason=type(exc).__name__)
   except EvidenceError:pass
   raise
  try:
   self.journal.append(**base,output_identity=None,outcome="AUTHORITY_ACTION_COMPLETED",reason=operation)
  except EvidenceError as exc:
   raise AuditOutcomeUnknown("authority action completed but final required audit is unavailable; reconciliation required") from exc
  self.lifecycle.commit_deferred(bundle.enrollment_id,iid)
  return result
 def stage(self,bundle,*,authorization_reference):
  return self._run_deferred(bundle,authorization_reference,"STAGE",
   lambda:(None,self.lifecycle.stage_deferred(bundle,authorization_reference=authorization_reference)))
 def verify_authenticated_remote(self,bundle,authenticated,verifier,*,expected_remote_key_reference,authorization_reference):
  return self._run_deferred(bundle,authorization_reference,"AUTHENTICATE_REMOTE",
   lambda:self.lifecycle.verify_authenticated_remote_deferred(bundle,authenticated,verifier,
    expected_remote_key_reference=expected_remote_key_reference,authorization_reference=authorization_reference))
 def accept_installation_proof(self,bundle,proof,*,authorization_reference):
  return self._run_deferred(bundle,authorization_reference,"VERIFY_INSTALLATION",
   lambda:(None,self.lifecycle.accept_installation_proof_deferred(bundle,proof,authorization_reference=authorization_reference)))
 def activate(self,bundle,*,operator_approved,authorization_reference):
  return self._run_deferred(bundle,authorization_reference,"ACTIVATE",
   lambda:(None,self.lifecycle.activate_deferred(bundle,operator_approved=operator_approved,authorization_reference=authorization_reference)))
 def revoke(self,bundle,*,operator_authorization_reference,reason):
  return self._run_deferred(bundle,operator_authorization_reference,"REVOKE",
   lambda:self.lifecycle.revoke_deferred(bundle,operator_authorization_reference=operator_authorization_reference,reason=reason))

class AuditedEnrollmentReconciler:
 def __init__(self,reconciler,journal:EvidenceJournal):
  self.reconciler=reconciler;self.journal=journal
 def resolve(self,enrollment_id,*,operator_approved,authorization_reference,expected_conclusion):
  base=dict(correlation_id=enrollment_id,actor="operator-reconciliation",target="enrollment-authority",
   authorization_reference=authorization_reference,input_identity=None,source_context="enrollment-reconciliation",
   collector_method="local-reference",timestamp=None,time_uncertainty="UNKNOWN")
  self.journal.append(**base,output_identity=None,outcome="RECONCILIATION_REQUESTED",reason=expected_conclusion)
  try:
   result=self.reconciler.resolve(enrollment_id,operator_approved=operator_approved,
    authorization_reference=authorization_reference,expected_conclusion=expected_conclusion)
  except Exception as exc:
   try:self.journal.append(**base,output_identity=None,outcome="RECONCILIATION_FAILED",reason=type(exc).__name__)
   except EvidenceError:pass
   raise
  try:self.journal.append(**base,output_identity=None,outcome=result,reason="operator-approved reconciliation")
  except EvidenceError as exc:
   raise AuditOutcomeUnknown("reconciliation completed but final required audit is unavailable") from exc
  return result
