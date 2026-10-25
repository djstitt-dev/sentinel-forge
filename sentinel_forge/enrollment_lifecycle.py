"""Guarded Forge enrollment lifecycle with terminal revocation."""

from __future__ import annotations
from .enrollment import EnrollmentBundle,EnrollmentProof,EnrollmentRegistry,EnrollmentError
from .enrollment_proof import EnrollmentChallenge,AuthenticatedEnrollmentProof
from .enrollment_session import ChallengeRegistry
from .authenticity import Verifier
from .revocation import RevocationRegistry,make_revocation

_ACTIVATION_CAPABILITY=object()
_REMOTE_AUTH_CAPABILITY=object()

class GuardedEnrollmentLifecycle:
    def __init__(self,enrollments:EnrollmentRegistry,challenges:ChallengeRegistry,revocations:RevocationRegistry):
        self.enrollments=enrollments;self.challenges=challenges;self.revocations=revocations
    def stage(self,bundle:EnrollmentBundle):
        self.revocations.require_not_revoked(bundle.enrollment_id);self.enrollments.stage(bundle)
    def issue_challenge(self,bundle:EnrollmentBundle,challenge:EnrollmentChallenge):
        self.revocations.require_not_revoked(bundle.enrollment_id)
        if self.enrollments.state(bundle.enrollment_id)!="STAGED":
            raise EnrollmentError("challenge requires STAGED enrollment")
        self.challenges.issue(bundle,challenge)
    def verify_authenticated_remote(self,bundle:EnrollmentBundle,authenticated:AuthenticatedEnrollmentProof,
                                    verifier:Verifier,*,expected_remote_key_reference:str):
        self.revocations.require_not_revoked(bundle.enrollment_id)
        ok=self.challenges.verify_and_consume(bundle,authenticated,verifier,
          expected_remote_key_reference=expected_remote_key_reference)
        self.enrollments._mark_remote_authenticated(bundle.enrollment_id,
          capability=_REMOTE_AUTH_CAPABILITY,expected_capability=_REMOTE_AUTH_CAPABILITY)
        return ok
    def accept_installation_proof(self,bundle:EnrollmentBundle,proof:EnrollmentProof):
        self.revocations.require_not_revoked(bundle.enrollment_id);self.enrollments.accept_proof(bundle,proof)
    def activate(self,enrollment_id:str,*,operator_approved:bool):
        self.revocations.require_not_revoked(enrollment_id)
        if not operator_approved:raise EnrollmentError("explicit operator approval required")
        self.enrollments._transition_verified_to_active(enrollment_id,
          capability=_ACTIVATION_CAPABILITY,expected_capability=_ACTIVATION_CAPABILITY)
    def revoke(self,bundle:EnrollmentBundle,*,operator_authorization_reference:str,reason:str):
        state=self.enrollments.state(bundle.enrollment_id)
        if state is None:raise EnrollmentError("cannot revoke unknown enrollment")
        record=make_revocation(enrollment_id=bundle.enrollment_id,remote_identity=bundle.remote_identity,
          operator_authorization_reference=operator_authorization_reference,reason=reason,prior_state=state)
        self.revocations.revoke(record);return record
    def state(self,enrollment_id:str):
        if self.revocations.is_revoked(enrollment_id):return "REVOKED"
        return self.enrollments.state(enrollment_id)
