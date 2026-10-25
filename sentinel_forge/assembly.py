"""Offline assembly of a Forge outbound logical package.

Assembly creates no transfer, release, deployment, credential, or network effect.
It produces a validator-approved logical envelope that stops at the Courier boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .contract import ContractBundle, ValidationResult
from .package import CandidateManifest

class AssemblyError(ValueError):
    pass

@dataclass(frozen=True)
class AssemblyContext:
    work_package_id: str
    revision_id: str
    authorization_id: str
    authorizing_authority: str
    authorized_principal: str
    scope_reference: str
    target: str
    operation: str
    policy_reference: str
    classification_handling: str
    correlation_id: str
    allowed_action_classes: str
    intended_purpose_disposition: str
    expected_transfer_effect_class: str
    canonical_integrity_reference: str
    authorization_state: str = "AUTHORIZED"
    revocation_cancellation_state: str = "ACTIVE"
    prior_attempt_reconciliation_state: str = "NO_KNOWN_PREDECESSOR"

@dataclass(frozen=True)
class OutboundLogicalPackage:
    objects: dict[str, dict[str, Any]]
    validation: ValidationResult

    @property
    def approved_for_courier_boundary(self) -> bool:
        """Logical validation only. This is not transfer authorization."""
        return (
            self.validation.accepted
            and self.objects["TransferReceipt"]["transfer_disposition"] == "PROPOSED"
            and self.objects["TransferReceipt"]["validation_outcome"] == "UNKNOWN"
            and self.objects["ScribeDisposition"]["disposition"] == "UNKNOWN"
        )

    @property
    def courier_effect_established(self) -> bool:
        return (
            self.objects["TransferReceipt"]["transfer_disposition"] == "TRANSFERRED"
            and self.objects["TransferReceipt"]["validation_outcome"] not in ("UNKNOWN", None, "")
        )

    @property
    def scribe_acceptance_established(self) -> bool:
        return self.objects["ScribeDisposition"]["disposition"] == "ACCEPT"

def assemble_outbound(manifest: CandidateManifest, context: AssemblyContext) -> OutboundLogicalPackage:
    _required_context(context)
    if manifest.work_package_revision != context.revision_id:
        raise AssemblyError("candidate manifest revision does not match assembly revision")
    if manifest.classification_handling != context.classification_handling:
        raise AssemblyError("candidate classification does not match assembly classification")

    artifact = manifest.artifact_identity()
    objects: dict[str, dict[str, Any]] = {
        "WorkPackageRevision": {
            "work_package_id": context.work_package_id,
            "revision_id": context.revision_id,
            "authorization_state": context.authorization_state,
            "authorization_reference": context.authorization_id,
            "scope_reference": context.scope_reference,
            "resource_target_scope": context.target,
            "allowed_action_classes": context.allowed_action_classes,
            "policy_reference": context.policy_reference,
            "cancellation_revocation_state": context.revocation_cancellation_state,
            "canonical_integrity_reference": context.canonical_integrity_reference,
        },
        "ArtifactIdentity": artifact,
        "AuthorizationReference": {
            "authorization_id": context.authorization_id,
            "authorizing_authority": context.authorizing_authority,
            "authorized_principal": context.authorized_principal,
            "authorized_work_package_revision": context.revision_id,
            "permitted_action": context.operation,
            "permitted_target_resource": context.target,
            "policy_reference": context.policy_reference,
            "authorization_state": context.authorization_state,
            "revocation_cancellation_state": context.revocation_cancellation_state,
        },
        "CorrelationIdentity": {
            "operation_correlation_id": context.correlation_id,
            "originating_identity": context.authorized_principal,
            "work_package_revision": context.revision_id,
            "target_component": context.target,
            "requested_operation": context.operation,
            "artifact_identity": manifest.artifact_id,
        },
        "TransferRequest": {
            "source_identity": context.authorized_principal,
            "destination": context.target,
            "transfer_operation": context.operation,
            "work_package_revision": context.revision_id,
            "authorization_reference": context.authorization_id,
            "artifact_identity": manifest.artifact_id,
            "policy_reference": context.policy_reference,
            "classification_handling": context.classification_handling,
            "correlation_identity": context.correlation_id,
            "intended_purpose_disposition": context.intended_purpose_disposition,
            "expected_transfer_effect_class": context.expected_transfer_effect_class,
            "prior_attempt_reconciliation_state": context.prior_attempt_reconciliation_state,
        },
        # These are explicit not-yet-effected placeholders. They prevent assembly
        # from fabricating successful Courier or Scribe outcomes.
        "TransferReceipt": {
            "courier_identity": "NOT_YET_ASSIGNED",
            "source_identity": context.authorized_principal,
            "destination": context.target,
            "transfer_operation": context.operation,
            "work_package_revision": context.revision_id,
            "authorization_reference": context.authorization_id,
            "artifact_identity": manifest.artifact_id,
            "correlation_identity": context.correlation_id,
            "policy_classification": context.classification_handling,
            "transfer_disposition": "PROPOSED",
            "validation_outcome": "UNKNOWN",
            "completeness_state": "COMPLETE",
            "retry_reconciliation_state": context.prior_attempt_reconciliation_state,
        },
        "ScribeDisposition": {
            "scribe_authority_identity": "NOT_YET_ASSIGNED",
            "work_package_revision": context.revision_id,
            "artifact_identity": manifest.artifact_id,
            "authorization_policy_reference": context.policy_reference,
            "release_evidence_policy_identity": "NOT_YET_EVALUATED",
            "disposition": "UNKNOWN",
            "validation_evaluation_references": "NOT_YET_EVALUATED",
            "reason_reference": "AWAITING_SCRIBE_EVALUATION",
        },
    }
    result = ContractBundle(objects).validate()
    if not result.accepted:
        details = "; ".join(f"{i.code}:{i.path}" for i in result.issues)
        raise AssemblyError(f"assembled logical package failed validation: {details}")
    return OutboundLogicalPackage(objects, result)

def _required_context(context: AssemblyContext) -> None:
    for name, value in vars(context).items():
        if not isinstance(value, str) or not value.strip():
            raise AssemblyError(f"assembly context {name} is required")
