"""Offline structural tests for the WP6.2 canonical logical data model.

These tests validate repository documentation/model consistency only.

Passing them does not establish runtime correctness, runtime security, host
state, network readiness, credential readiness, Courier readiness, Scribe
readiness, release approval, deployment approval, or production readiness.
"""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]

PLAN = ROOT / "docs/plans/wp6-canonical-data-model-preparation.md"
MODEL = ROOT / "docs/architecture/forge-courier-scribe-data-model.md"
WP61_CONTRACT = ROOT / "docs/architecture/forge-courier-scribe-contract.md"
WP61_PLAN = ROOT / "docs/plans/wp6-forge-courier-scribe-preparation.md"
WP5_ARCH = ROOT / "docs/architecture/forge-operational-architecture.md"
WP5_REQ = ROOT / "docs/plans/wp5-operational-requirements.md"

APPROVED_WP61_REVISION = (
    "1fff05aef06ef79c08a60031f93514a5c0a6b0ee"
)

APPROVED_WP5_REVISION = (
    "0ce6457b31c7d798bf00626aeaeaeb963a103e52"
)

LOGICAL_OBJECTS = (
    "WorkPackageRevision",
    "ArtifactIdentity",
    "AuthorizationReference",
    "CorrelationIdentity",
    "TransferRequest",
    "TransferReceipt",
    "ScribeDisposition",
)

EXPECTED_FIELDS = {
    "WorkPackageRevision": {
        "work_package_id",
        "revision_id",
        "authorization_state",
        "authorization_reference",
        "scope_reference",
        "resource_target_scope",
        "allowed_action_classes",
        "policy_reference",
        "cancellation_revocation_state",
        "supersession_amendment_relationship",
        "canonical_integrity_reference",
    },
    "ArtifactIdentity": {
        "artifact_id",
        "artifact_type_class",
        "integrity_reference",
        "integrity_provenance",
        "source_work_package_revision",
        "source_candidate_build_workspace",
        "source_component",
        "classification_handling",
        "completeness_state",
        "lineage_provenance",
    },
    "AuthorizationReference": {
        "authorization_id",
        "authorizing_authority",
        "authorized_principal",
        "authorized_work_package_revision",
        "permitted_action",
        "permitted_target_resource",
        "policy_reference",
        "authorization_state",
        "revocation_cancellation_state",
        "validity_information",
    },
    "CorrelationIdentity": {
        "operation_correlation_id",
        "originating_identity",
        "work_package_revision",
        "target_component",
        "requested_operation",
        "artifact_identity",
        "predecessor_retry_relationship",
        "known_ordering_relationship",
        "reconciliation_state",
    },
    "TransferRequest": {
        "source_identity",
        "destination",
        "transfer_operation",
        "work_package_revision",
        "authorization_reference",
        "artifact_identity",
        "policy_reference",
        "classification_handling",
        "correlation_identity",
        "intended_purpose_disposition",
        "expected_transfer_effect_class",
        "provenance",
        "prior_attempt_reconciliation_state",
    },
    "TransferReceipt": {
        "courier_identity",
        "source_identity",
        "destination",
        "transfer_operation",
        "work_package_revision",
        "authorization_reference",
        "artifact_identity",
        "correlation_identity",
        "policy_classification",
        "transfer_disposition",
        "validation_outcome",
        "destination_acknowledgement_state",
        "completeness_state",
        "failure_information",
        "start_end_time_evidence",
        "ordered_event_references",
        "retry_reconciliation_state",
        "provenance",
    },
    "ScribeDisposition": {
        "scribe_authority_identity",
        "source_requester_context",
        "work_package_revision",
        "artifact_identity",
        "transfer_correlation_identity",
        "authorization_policy_reference",
        "release_evidence_policy_identity",
        "disposition",
        "validation_evaluation_references",
        "reason_reference",
        "provenance",
        "explicit_unknown_fields",
    },
}

EXPECTED_CONDITIONALS = {
    ("WorkPackageRevision", "supersession_amendment_relationship"),
    ("ArtifactIdentity", "source_candidate_build_workspace"),
    ("AuthorizationReference", "validity_information"),
    ("CorrelationIdentity", "artifact_identity"),
    ("CorrelationIdentity", "predecessor_retry_relationship"),
    ("CorrelationIdentity", "reconciliation_state"),
    ("TransferReceipt", "destination_acknowledgement_state"),
    ("TransferReceipt", "failure_information"),
    ("ScribeDisposition", "source_requester_context"),
    ("ScribeDisposition", "transfer_correlation_identity"),
    ("ScribeDisposition", "explicit_unknown_fields"),
}

TRANSFER_STATES = (
    "PROPOSED",
    "REJECT",
    "INCOMPLETE",
    "PARTIAL",
    "UNKNOWN",
    "TRANSFERRED",
)

SCRIBE_STATES = (
    "ACCEPT",
    "REJECT",
    "UNKNOWN",
)

DEFERRED_DECISIONS = tuple(
    f"DEC-{number:02d}" for number in range(6, 14)
)


class WP62DataModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = PLAN.read_text()
        cls.model = MODEL.read_text()
        cls.model_normalized = re.sub(r"\s+", " ", cls.model)
        cls.wp61_contract = WP61_CONTRACT.read_text()
        cls.wp61_plan = WP61_PLAN.read_text()
        cls.wp5_arch = WP5_ARCH.read_text()
        cls.wp5_req = WP5_REQ.read_text()

    def test_model_binds_to_approved_wp61_and_wp5_revisions(self):
        self.assertIn(APPROVED_WP61_REVISION, self.plan)
        self.assertIn(APPROVED_WP61_REVISION, self.model)
        self.assertIn(APPROVED_WP5_REVISION, self.plan)
        self.assertIn(APPROVED_WP5_REVISION, self.model)

    def test_all_seven_logical_objects_exist_exactly_once(self):
        for name in LOGICAL_OBJECTS:
            matches = re.findall(
                rf"^## \d+\. Logical object: {re.escape(name)}$",
                self.model,
                flags=re.MULTILINE,
            )
            self.assertEqual(
                len(matches),
                1,
                f"{name} must exist exactly once",
            )

    def test_exact_field_inventory_per_object(self):
        for name in LOGICAL_OBJECTS:
            observed = {
                field["name"]
                for field in self._fields(name)
            }
            self.assertEqual(
                observed,
                EXPECTED_FIELDS[name],
                f"{name} field inventory changed",
            )

    def test_total_modeled_field_count(self):
        count = sum(
            len(self._fields(name))
            for name in LOGICAL_OBJECTS
        )
        self.assertEqual(count, 83)

    def test_every_field_has_known_requirement_class_and_type(self):
        allowed_classes = {
            "REQUIRED",
            "CONDITIONAL",
            "OPTIONAL_OR_AVAILABLE",
        }

        for name in LOGICAL_OBJECTS:
            fields = self._fields(name)
            self.assertTrue(fields)

            for field in fields:
                self.assertIn(
                    field["requirement"],
                    allowed_classes,
                )
                self.assertTrue(
                    field["type"],
                    f"{name}.{field['name']} lacks logical type",
                )

    def test_requirement_class_counts(self):
        counts = {
            "REQUIRED": 0,
            "CONDITIONAL": 0,
            "OPTIONAL_OR_AVAILABLE": 0,
        }

        for name in LOGICAL_OBJECTS:
            for field in self._fields(name):
                counts[field["requirement"]] += 1

        self.assertEqual(counts["REQUIRED"], 65)
        self.assertEqual(counts["CONDITIONAL"], 11)
        self.assertEqual(
            counts["OPTIONAL_OR_AVAILABLE"],
            7,
        )

    def test_exact_conditional_field_set(self):
        observed = set()

        for name in LOGICAL_OBJECTS:
            for field in self._fields(name):
                if field["requirement"] == "CONDITIONAL":
                    observed.add((name, field["name"]))

        self.assertEqual(observed, EXPECTED_CONDITIONALS)

    def test_semantic_reference_types_preserve_wp61_meaning(self):
        required = (
            "`PrincipalReference`",
            "`TargetReference`",
            "`ProvenanceValue`",
            "does not imply recursive embedding",
        )

        for value in required:
            self.assertIn(value, self.model_normalized)

        logical_state_types = (
            "CompletenessState",
            "ReconciliationState",
        )

        for value in logical_state_types:
            self.assertIn(value, self.model_normalized)

        self.assertEqual(
            self._field(
                "AuthorizationReference",
                "authorized_principal",
            )["type"],
            "PrincipalReference",
        )

        self.assertEqual(
            self._field(
                "TransferRequest",
                "destination",
            )["type"],
            "TargetReference",
        )

        self.assertEqual(
            self._field(
                "TransferReceipt",
                "destination",
            )["type"],
            "TargetReference",
        )

    def test_correlation_reconciliation_is_conditional(self):
        field = self._field(
            "CorrelationIdentity",
            "reconciliation_state",
        )

        self.assertEqual(field["requirement"], "CONDITIONAL")
        self.assertEqual(field["type"], "ReconciliationState")

        self.assertIn(
            "Required when a predecessor, retry, duplicate, replay "
            "or prior uncertain outcome exists",
            self.model_normalized,
        )

    def test_transfer_and_scribe_vocabularies_are_exact(self):
        transfer = self._bullet_values(
            "### 2.1 TransferDisposition",
            "### 2.2 ScribeDispositionState",
        )

        scribe = self._bullet_values(
            "### 2.2 ScribeDispositionState",
            "### 2.3 CompletenessState",
        )

        self.assertEqual(tuple(transfer), TRANSFER_STATES)
        self.assertEqual(tuple(scribe), SCRIBE_STATES)

    def test_transfer_success_does_not_create_scribe_or_deployment_authority(self):
        required = (
            "`TRANSFERRED` establishes only Courier-controlled transfer completion",
            "It does not establish Scribe acceptance or deployment authorization.",
            "`TRANSFERRED` does not mean Scribe `ACCEPT`.",
            "`TRANSFERRED` does not authorize deployment.",
        )

        for statement in required:
            self.assertIn(statement, self.model_normalized)

    def test_scribe_accept_does_not_create_deployment_or_conduit_authority(self):
        required = (
            "`ACCEPT` establishes only Scribe-controlled release/evidence acceptance",
            "`ACCEPT` does not authorize deployment.",
            "`ACCEPT` does not authorize Conduit execution.",
            "`ACCEPT` does not grant Forge administration.",
        )

        for statement in required:
            self.assertIn(statement, self.model_normalized)

    def test_structural_validity_does_not_create_authority(self):
        required = (
            "Structural validity is not authorization.",
            "Structural validity of the request does not authorize transfer.",
            "Courier independently decides whether the requested transfer effect is",
            "Forge cannot self-issue an authoritative Courier receipt.",
            "Only Scribe's approved controlled release/evidence decision path may create the",
        )

        for statement in required:
            self.assertIn(statement, self.model_normalized)

    def test_unknown_partial_incomplete_are_fail_closed(self):
        for value in (
            "`UNKNOWN`",
            "`PARTIAL`",
            "`INCOMPLETE`",
        ):
            self.assertIn(value, self.model)

        required = (
            "shall not be normalized into successful completion",
            "shall not be treated as safe to repeat",
            "shall not default to authorized",
            "No completeness state may be inferred solely from omission of a field.",
        )

        for statement in required:
            self.assertIn(statement, self.model_normalized)

    def test_retry_and_replay_preserve_prior_identity(self):
        required = (
            "A retry shall reference the applicable predecessor.",
            "A sensitive operation with unresolved prior outcome shall not be treated as safe to repeat",
            "a new operation identifier is generated",
            "retries shall remain linked to prior attempts",
            "a new correlation identifier shall not cleanse an unresolved prior `UNKNOWN`",
        )

        for statement in required:
            self.assertIn(statement, self.model_normalized)

    def test_cancellation_revocation_amendment_preserve_history(self):
        required = (
            "Cancellation or revocation prevents new dependent effects",
            "An amendment creates a distinct new/amended `WorkPackageRevision`.",
            "Historical evidence remains bound to the revision under which it occurred.",
            "shall not rewrite evidence attributable to its predecessor",
        )

        for statement in required:
            self.assertIn(statement, self.model_normalized)

    def test_object_reference_does_not_require_recursive_embedding(self):
        self.assertIn(
            "does not imply recursive embedding",
            self.model_normalized,
        )

    def test_dec08_does_not_gain_trusted_time_semantics(self):
        required = (
            "does not imply trusted chronological freshness",
            "Time evidence alone shall not establish trusted freshness.",
            "trusted time source",
            "skew tolerance",
            "numeric freshness interval",
            "timestamp replay window",
        )

        for statement in required:
            self.assertIn(statement, self.model_normalized)

    def test_dec06_through_dec13_remain_deferred(self):
        self.assertIn(
            "DEC-06 through DEC-13 remain deferred",
            self.model_normalized,
        )

        self.assertIn(
            "This model does not resolve them.",
            self.model,
        )

        self.assertIn(
            "requires one of those unresolved decisions",
            self.model_normalized,
        )

        for decision in DEFERRED_DECISIONS:
            self.assertRegex(
                self.wp5_req,
                rf"(?m)^\|\s*{re.escape(decision)}\s*\|.*"
                rf"DEFERRED FOR INITIAL CAPABILITY",
            )

    def test_no_concrete_schema_runtime_crypto_or_credential_stack_selected(self):
        prohibited = (
            r"\buse\s+JSON\b",
            r"\buse\s+JSON Schema\b",
            r"\buse\s+YAML\b",
            r"\buse\s+CBOR\b",
            r"\buse\s+Protocol Buffers\b",
            r"\buse\s+REST\b",
            r"\buse\s+gRPC\b",
            r"\buse\s+SQLite\b",
            r"\buse\s+PostgreSQL\b",
            r"\buse\s+SHA-256\b",
            r"\buse\s+SHA-512\b",
            r"\buse\s+Ed25519\b",
            r"\buse\s+RSA\b",
            r"\buse\s+mTLS\b",
        )

        for pattern in prohibited:
            self.assertNotRegex(self.model, pattern)

    def test_no_deferred_numeric_defaults_selected(self):
        prohibited = (
            r"\bport\s+\d{1,5}\b",
            r"\btimeout\s*[:=]\s*\d+",
            r"\bfreshness\s*[:=]\s*\d+",
            r"\bconcurrency\s*[:=]\s*\d+",
            r"\bretention\s*[:=]\s*\d+",
            r"\bRTO\s*[:=]\s*\d+",
            r"\bRPO\s*[:=]\s*\d+",
        )

        for pattern in prohibited:
            self.assertNotRegex(
                self.model,
                pattern,
            )

    def test_secrets_are_not_required_model_fields(self):
        prohibited_field_fragments = (
            "password",
            "private_key",
            "bearer_token",
            "authentication_secret",
            "release_credential",
            "deployment_credential",
        )

        field_names = {
            field["name"]
            for name in LOGICAL_OBJECTS
            for field in self._fields(name)
        }

        for fragment in prohibited_field_fragments:
            self.assertTrue(
                all(fragment not in field for field in field_names),
                f"secret-like field introduced: {fragment}",
            )

        self.assertIn(
            "The logical model shall not require raw:",
            self.model,
        )

    def test_cross_object_consistency_is_fail_closed(self):
        required = (
            "A mismatch in a security-relevant shared binding shall fail the affected dependent validation.",
            "Conflicting consequential bindings fail validation.",
            "They shall not be silently rewritten, merged or normalized.",
        )

        for statement in required:
            self.assertIn(statement, self.model_normalized)

    def test_wp61_authority_source_remains_unchanged_semantically(self):
        required = (
            "Forge cannot mark Scribe-controlled release/evidence state.",
            "Courier cannot mark Scribe-controlled release/evidence state.",
            "Courier cannot create deployment authority.",
            "A successful Courier transfer does not establish Scribe acceptance.",
        )

        for statement in required:
            self.assertIn(statement, self.wp61_contract)

    def test_wp61_unknown_retry_source_remains_authoritative(self):
        required = (
            "An unresolved sensitive outcome remains `UNKNOWN`.",
            "A sensitive operation with unresolved prior outcome shall not be blindly",
            "A retry following `UNKNOWN` shall first reconcile the prior operation",
        )

        for statement in required:
            self.assertIn(statement, self.wp61_contract)

    def test_model_tests_are_not_operational_acceptance(self):
        required = (
            "repository-only implementation-preparation artifact",
            "does not authorize executable schema implementation or runtime implementation",
            "does not establish operational acceptance",
        )

        for statement in required:
            self.assertIn(statement, self.model_normalized)

        self.assertIn(
            "A successful WP6.2 test or commit establishes repository preparation only.",
            re.sub(r"\s+", " ", self.plan),
        )

    @classmethod
    def _object_section(cls, name):
        index = LOGICAL_OBJECTS.index(name)
        heading_number = index + 4
        start_heading = (
            f"## {heading_number}. Logical object: {name}"
        )

        start = cls.model.find(start_heading)
        if start < 0:
            raise AssertionError(
                f"unable to locate object section: {name}"
            )

        next_heading = f"\n## {heading_number + 1}. "
        end = cls.model.find(next_heading, start + 1)

        if end < 0:
            end = len(cls.model)

        return cls.model[start:end]

    @classmethod
    def _fields(cls, name):
        section = cls._object_section(name)
        fields = []

        pattern = re.compile(
            r"^\| `([^`]+)` \| "
            r"(REQUIRED|CONDITIONAL|OPTIONAL_OR_AVAILABLE) "
            r"\| ([^|]+) \| (.+) \|$"
        )

        for line in section.splitlines():
            match = pattern.match(line)

            if match:
                fields.append(
                    {
                        "name": match.group(1),
                        "requirement": match.group(2),
                        "type": match.group(3).strip(),
                        "meaning": match.group(4).strip(),
                    }
                )

        return fields

    @classmethod
    def _field(cls, object_name, field_name):
        matches = [
            field
            for field in cls._fields(object_name)
            if field["name"] == field_name
        ]

        if len(matches) != 1:
            raise AssertionError(
                f"{object_name}.{field_name} expected once, "
                f"found {len(matches)}"
            )

        return matches[0]

    @classmethod
    def _bullet_values(cls, start_heading, end_heading):
        start = cls.model.find(start_heading)
        end = cls.model.find(end_heading)

        if start < 0 or end < 0 or end <= start:
            raise AssertionError(
                f"unable to isolate vocabulary "
                f"{start_heading!r} -> {end_heading!r}"
            )

        section = cls.model[start:end]

        return re.findall(
            r"^- `([^`]+)`$",
            section,
            flags=re.MULTILINE,
        )


if __name__ == "__main__":
    unittest.main()
