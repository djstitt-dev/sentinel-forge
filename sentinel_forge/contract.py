"""Fail-closed validator for the WP6 Forge/Courier/Scribe logical contract.

No network, credential, deployment, host mutation, or privileged behavior exists
here. Values remain opaque strings/references unless WP6 defines an exact enum.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

TRANSFER_DISPOSITIONS = frozenset(
    {"PROPOSED", "REJECT", "INCOMPLETE", "PARTIAL", "UNKNOWN", "TRANSFERRED"}
)
SCRIBE_DISPOSITIONS = frozenset({"ACCEPT", "REJECT", "UNKNOWN"})

FIELD_RULES: dict[str, dict[str, str]] = {
    "WorkPackageRevision": {
        "work_package_id": "REQUIRED", "revision_id": "REQUIRED",
        "authorization_state": "REQUIRED", "authorization_reference": "REQUIRED",
        "scope_reference": "REQUIRED", "resource_target_scope": "REQUIRED",
        "allowed_action_classes": "REQUIRED", "policy_reference": "REQUIRED",
        "cancellation_revocation_state": "REQUIRED",
        "supersession_amendment_relationship": "CONDITIONAL",
        "canonical_integrity_reference": "REQUIRED",
    },
    "ArtifactIdentity": {
        "artifact_id": "REQUIRED", "artifact_type_class": "REQUIRED",
        "integrity_reference": "REQUIRED", "integrity_provenance": "REQUIRED",
        "source_work_package_revision": "REQUIRED",
        "source_candidate_build_workspace": "CONDITIONAL",
        "source_component": "REQUIRED", "classification_handling": "REQUIRED",
        "completeness_state": "REQUIRED", "lineage_provenance": "OPTIONAL_OR_AVAILABLE",
    },
    "AuthorizationReference": {
        "authorization_id": "REQUIRED", "authorizing_authority": "REQUIRED",
        "authorized_principal": "REQUIRED", "authorized_work_package_revision": "REQUIRED",
        "permitted_action": "REQUIRED", "permitted_target_resource": "REQUIRED",
        "policy_reference": "REQUIRED", "authorization_state": "REQUIRED",
        "revocation_cancellation_state": "REQUIRED", "validity_information": "CONDITIONAL",
    },
    "CorrelationIdentity": {
        "operation_correlation_id": "REQUIRED", "originating_identity": "REQUIRED",
        "work_package_revision": "REQUIRED", "target_component": "REQUIRED",
        "requested_operation": "REQUIRED", "artifact_identity": "CONDITIONAL",
        "predecessor_retry_relationship": "CONDITIONAL",
        "known_ordering_relationship": "OPTIONAL_OR_AVAILABLE",
        "reconciliation_state": "CONDITIONAL",
    },
    "TransferRequest": {
        "source_identity": "REQUIRED", "destination": "REQUIRED",
        "transfer_operation": "REQUIRED", "work_package_revision": "REQUIRED",
        "authorization_reference": "REQUIRED", "artifact_identity": "REQUIRED",
        "policy_reference": "REQUIRED", "classification_handling": "REQUIRED",
        "correlation_identity": "REQUIRED", "intended_purpose_disposition": "REQUIRED",
        "expected_transfer_effect_class": "REQUIRED",
        "provenance": "OPTIONAL_OR_AVAILABLE",
        "prior_attempt_reconciliation_state": "REQUIRED",
    },
    "TransferReceipt": {
        "courier_identity": "REQUIRED", "source_identity": "REQUIRED",
        "destination": "REQUIRED", "transfer_operation": "REQUIRED",
        "work_package_revision": "REQUIRED", "authorization_reference": "REQUIRED",
        "artifact_identity": "REQUIRED", "correlation_identity": "REQUIRED",
        "policy_classification": "REQUIRED", "transfer_disposition": "REQUIRED",
        "validation_outcome": "REQUIRED",
        "destination_acknowledgement_state": "CONDITIONAL",
        "completeness_state": "REQUIRED", "failure_information": "CONDITIONAL",
        "start_end_time_evidence": "OPTIONAL_OR_AVAILABLE",
        "ordered_event_references": "OPTIONAL_OR_AVAILABLE",
        "retry_reconciliation_state": "REQUIRED", "provenance": "OPTIONAL_OR_AVAILABLE",
    },
    "ScribeDisposition": {
        "scribe_authority_identity": "REQUIRED", "source_requester_context": "CONDITIONAL",
        "work_package_revision": "REQUIRED", "artifact_identity": "REQUIRED",
        "transfer_correlation_identity": "CONDITIONAL",
        "authorization_policy_reference": "REQUIRED",
        "release_evidence_policy_identity": "REQUIRED", "disposition": "REQUIRED",
        "validation_evaluation_references": "REQUIRED", "reason_reference": "REQUIRED",
        "provenance": "OPTIONAL_OR_AVAILABLE", "explicit_unknown_fields": "CONDITIONAL",
    },
}

@dataclass(frozen=True)
class ValidationIssue:
    code: str
    path: str
    message: str

@dataclass(frozen=True)
class ValidationResult:
    accepted: bool
    issues: tuple[ValidationIssue, ...]

    @classmethod
    def from_issues(cls, issues: list[ValidationIssue]) -> "ValidationResult":
        return cls(not issues, tuple(issues))

@dataclass(frozen=True)
class ContractBundle:
    objects: Mapping[str, Mapping[str, Any]]

    def validate(self) -> ValidationResult:
        issues: list[ValidationIssue] = []
        self._validate_structure(issues)
        if not issues:
            self._validate_exact_vocabularies(issues)
            self._validate_cross_bindings(issues)
            self._validate_fail_closed_states(issues)
        return ValidationResult.from_issues(issues)

    def _validate_structure(self, issues: list[ValidationIssue]) -> None:
        expected = set(FIELD_RULES)
        actual = set(self.objects)
        for name in sorted(expected - actual):
            issues.append(ValidationIssue("MISSING_OBJECT", name, "canonical object is required"))
        for name in sorted(actual - expected):
            issues.append(ValidationIssue("UNKNOWN_OBJECT", name, "object is not in canonical WP6 inventory"))
        for name in sorted(expected & actual):
            value = self.objects[name]
            if not isinstance(value, Mapping):
                issues.append(ValidationIssue("INVALID_OBJECT", name, "object must be a mapping"))
                continue
            rules = FIELD_RULES[name]
            for field, requirement in rules.items():
                if requirement == "REQUIRED" and not _present(value.get(field)):
                    issues.append(ValidationIssue(
                        "MISSING_REQUIRED_FIELD", f"{name}.{field}",
                        "required canonical field is absent or empty",
                    ))
            for field in sorted(set(value) - set(rules)):
                issues.append(ValidationIssue(
                    "UNKNOWN_FIELD", f"{name}.{field}",
                    "field has no attributable canonical WP6 mapping",
                ))

    def _validate_exact_vocabularies(self, issues: list[ValidationIssue]) -> None:
        receipt = self.objects["TransferReceipt"]
        disposition = receipt["transfer_disposition"]
        if disposition not in TRANSFER_DISPOSITIONS:
            issues.append(ValidationIssue(
                "INVALID_TRANSFER_DISPOSITION", "TransferReceipt.transfer_disposition",
                "value is outside the exact WP6 TransferDisposition vocabulary",
            ))
        scribe = self.objects["ScribeDisposition"]["disposition"]
        if scribe not in SCRIBE_DISPOSITIONS:
            issues.append(ValidationIssue(
                "INVALID_SCRIBE_DISPOSITION", "ScribeDisposition.disposition",
                "value is outside the exact WP6 ScribeDispositionState vocabulary",
            ))

    def _validate_cross_bindings(self, issues: list[ValidationIssue]) -> None:
        o = self.objects
        checks = [
            ("WORK_PACKAGE_MISMATCH", [
                ("WorkPackageRevision.revision_id", o["WorkPackageRevision"]["revision_id"]),
                ("ArtifactIdentity.source_work_package_revision", o["ArtifactIdentity"]["source_work_package_revision"]),
                ("AuthorizationReference.authorized_work_package_revision", o["AuthorizationReference"]["authorized_work_package_revision"]),
                ("CorrelationIdentity.work_package_revision", o["CorrelationIdentity"]["work_package_revision"]),
                ("TransferRequest.work_package_revision", o["TransferRequest"]["work_package_revision"]),
                ("TransferReceipt.work_package_revision", o["TransferReceipt"]["work_package_revision"]),
                ("ScribeDisposition.work_package_revision", o["ScribeDisposition"]["work_package_revision"]),
            ]),
            ("AUTHORIZATION_MISMATCH", [
                ("WorkPackageRevision.authorization_reference", o["WorkPackageRevision"]["authorization_reference"]),
                ("AuthorizationReference.authorization_id", o["AuthorizationReference"]["authorization_id"]),
                ("TransferRequest.authorization_reference", o["TransferRequest"]["authorization_reference"]),
                ("TransferReceipt.authorization_reference", o["TransferReceipt"]["authorization_reference"]),
            ]),
            ("ARTIFACT_MISMATCH", [
                ("ArtifactIdentity.artifact_id", o["ArtifactIdentity"]["artifact_id"]),
                ("TransferRequest.artifact_identity", o["TransferRequest"]["artifact_identity"]),
                ("TransferReceipt.artifact_identity", o["TransferReceipt"]["artifact_identity"]),
                ("ScribeDisposition.artifact_identity", o["ScribeDisposition"]["artifact_identity"]),
            ]),
            ("CORRELATION_MISMATCH", [
                ("CorrelationIdentity.operation_correlation_id", o["CorrelationIdentity"]["operation_correlation_id"]),
                ("TransferRequest.correlation_identity", o["TransferRequest"]["correlation_identity"]),
                ("TransferReceipt.correlation_identity", o["TransferReceipt"]["correlation_identity"]),
            ]),
            ("SOURCE_MISMATCH", [
                ("AuthorizationReference.authorized_principal", o["AuthorizationReference"]["authorized_principal"]),
                ("CorrelationIdentity.originating_identity", o["CorrelationIdentity"]["originating_identity"]),
                ("TransferRequest.source_identity", o["TransferRequest"]["source_identity"]),
                ("TransferReceipt.source_identity", o["TransferReceipt"]["source_identity"]),
            ]),
            ("TARGET_MISMATCH", [
                ("AuthorizationReference.permitted_target_resource", o["AuthorizationReference"]["permitted_target_resource"]),
                ("CorrelationIdentity.target_component", o["CorrelationIdentity"]["target_component"]),
                ("TransferRequest.destination", o["TransferRequest"]["destination"]),
                ("TransferReceipt.destination", o["TransferReceipt"]["destination"]),
            ]),
            ("OPERATION_MISMATCH", [
                ("AuthorizationReference.permitted_action", o["AuthorizationReference"]["permitted_action"]),
                ("CorrelationIdentity.requested_operation", o["CorrelationIdentity"]["requested_operation"]),
                ("TransferRequest.transfer_operation", o["TransferRequest"]["transfer_operation"]),
                ("TransferReceipt.transfer_operation", o["TransferReceipt"]["transfer_operation"]),
            ]),
        ]
        for code, bindings in checks:
            values = {_stable(v) for _, v in bindings}
            if len(values) != 1:
                issues.append(ValidationIssue(code, ",".join(p for p, _ in bindings),
                                              "security-relevant shared binding disagrees"))

    def _validate_fail_closed_states(self, issues: list[ValidationIssue]) -> None:
        o = self.objects
        auth = str(o["AuthorizationReference"]["authorization_state"]).upper()
        revoke = str(o["AuthorizationReference"]["revocation_cancellation_state"]).upper()
        wp_auth = str(o["WorkPackageRevision"]["authorization_state"]).upper()
        wp_revoke = str(o["WorkPackageRevision"]["cancellation_revocation_state"]).upper()
        blocked = {"UNKNOWN", "REJECT", "REJECTED", "DENIED", "REVOKED", "CANCELLED", "CANCELED"}
        if auth in blocked or wp_auth in blocked:
            issues.append(ValidationIssue("AUTHORITY_NOT_ESTABLISHED", "authorization_state",
                                          "authority is denied, revoked, cancelled, rejected, or unknown"))
        if revoke not in {"NONE", "NOT_REVOKED", "ACTIVE", "CLEAR"} or wp_revoke not in {
            "NONE", "NOT_REVOKED", "ACTIVE", "CLEAR"
        }:
            issues.append(ValidationIssue("REVOCATION_STATE_BLOCKS", "revocation_cancellation_state",
                                          "revocation/cancellation state does not establish active authority"))
        for path, value in [
            ("ArtifactIdentity.completeness_state", o["ArtifactIdentity"]["completeness_state"]),
            ("TransferReceipt.completeness_state", o["TransferReceipt"]["completeness_state"]),
        ]:
            if str(value).upper() not in {"COMPLETE", "ESTABLISHED_COMPLETE"}:
                issues.append(ValidationIssue("INCOMPLETE_OR_UNKNOWN", path,
                                              "complete state is not established"))
        for path, value in [
            ("TransferRequest.prior_attempt_reconciliation_state", o["TransferRequest"]["prior_attempt_reconciliation_state"]),
            ("TransferReceipt.retry_reconciliation_state", o["TransferReceipt"]["retry_reconciliation_state"]),
        ]:
            if "UNKNOWN" in str(value).upper() or "UNRESOLVED" in str(value).upper():
                issues.append(ValidationIssue("UNRESOLVED_PRIOR_OUTCOME", path,
                                              "sensitive retry/replay outcome remains unresolved"))

def _present(value: Any) -> bool:
    return value is not None and value != "" and value != [] and value != {}

def _stable(value: Any) -> str:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return repr(value)
    return repr(value)
