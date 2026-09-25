from __future__ import annotations

from collections import Counter
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]

MODEL = ROOT / "docs/architecture/forge-courier-scribe-data-model.md"
CONTRACT = (
    ROOT
    / "docs/architecture/forge-courier-scribe-schema-derivation-contract.md"
)
PLAN = ROOT / "docs/plans/wp6-schema-derivation-contract-preparation.md"

WP62_COMMIT = "3bb6fb09c77d7ca3e11958dad1b0fc3d61692f5d"
WP62_TREE = "1eae8065ce361aaf3165803ecdcb667f450ba652"

OBJECTS = (
    "WorkPackageRevision",
    "ArtifactIdentity",
    "AuthorizationReference",
    "CorrelationIdentity",
    "TransferRequest",
    "TransferReceipt",
    "ScribeDisposition",
)

LOGICAL_TYPES = {
    "Identifier",
    "Reference",
    "Text",
    "Enum",
    "BooleanState",
    "IdentityReference",
    "PrincipalReference",
    "TargetReference",
    "PolicyReference",
    "IntegrityReference",
    "ObjectReference",
    "RelationshipReference",
    "OrderedEventReference",
    "TimeEvidence",
    "ProvenanceValue",
    "UnknownCapableValue",
    "CompletenessState",
    "ReconciliationState",
}

EXPECTED_COUNTS = {
    "REQUIRED": 65,
    "CONDITIONAL": 11,
    "OPTIONAL_OR_AVAILABLE": 7,
}

EXPECTED_CONDITIONAL = {
    "WorkPackageRevision.supersession_amendment_relationship",
    "ArtifactIdentity.source_candidate_build_workspace",
    "AuthorizationReference.validity_information",
    "CorrelationIdentity.artifact_identity",
    "CorrelationIdentity.predecessor_retry_relationship",
    "CorrelationIdentity.reconciliation_state",
    "TransferReceipt.destination_acknowledgement_state",
    "TransferReceipt.failure_information",
    "ScribeDisposition.source_requester_context",
    "ScribeDisposition.transfer_correlation_identity",
    "ScribeDisposition.explicit_unknown_fields",
}

TRANSFER_STATES = {
    "PROPOSED",
    "REJECT",
    "INCOMPLETE",
    "PARTIAL",
    "UNKNOWN",
    "TRANSFERRED",
}

SCRIBE_STATES = {
    "ACCEPT",
    "REJECT",
    "UNKNOWN",
}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_model_fields(text: str):
    rows = []
    current = None

    for line in text.splitlines():
        heading = re.match(
            r"^## \d+\. Logical object: ([A-Za-z0-9_]+)$",
            line,
        )
        if heading:
            current = heading.group(1)
            continue

        if current and line.startswith("| `"):
            parts = [
                part.strip()
                for part in line.strip().strip("|").split("|")
            ]
            if len(parts) < 4:
                continue

            field = parts[0].strip("`")
            requirement = parts[1]
            logical_type = parts[2].strip("`")

            if requirement in EXPECTED_COUNTS:
                rows.append(
                    (current, field, requirement, logical_type)
                )

    return rows


class WP63SchemaDerivationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = read(MODEL)
        cls.contract = read(CONTRACT)
        cls.plan = read(PLAN)
        cls.rows = parse_model_fields(cls.model)

    def test_01_exact_wp62_revision_and_tree_binding(self):
        self.assertIn(WP62_COMMIT, self.contract)
        self.assertIn(WP62_TREE, self.contract)

    def test_02_all_seven_logical_objects_accounted_for(self):
        for obj in OBJECTS:
            self.assertIn(f"`{obj}`", self.contract)

    def test_03_exact_83_field_inventory_from_wp62(self):
        self.assertEqual(len(self.rows), 83)

    def test_04_requirement_class_counts_preserved(self):
        counts = Counter(req for _, _, req, _ in self.rows)
        self.assertEqual(
            {key: counts[key] for key in EXPECTED_COUNTS},
            EXPECTED_COUNTS,
        )

    def test_05_exact_conditional_set_preserved(self):
        conditional = {
            f"{obj}.{field}"
            for obj, field, req, _ in self.rows
            if req == "CONDITIONAL"
        }
        self.assertEqual(conditional, EXPECTED_CONDITIONAL)

        for name in EXPECTED_CONDITIONAL:
            self.assertIn(f"`{name}`", self.contract)

    def test_06_every_canonical_field_remains_attributable(self):
        for obj, field, requirement, logical_type in self.rows:
            self.assertIn(obj, self.contract)
            self.assertTrue(field)
            self.assertIn(requirement, EXPECTED_COUNTS)
            self.assertTrue(logical_type)

    def test_07_logical_type_vocabulary_preserved(self):
        model_types = {
            logical_type
            for _, _, _, logical_type in self.rows
        }

        self.assertTrue(model_types.issubset(LOGICAL_TYPES))

        for logical_type in LOGICAL_TYPES:
            self.assertIn(f"`{logical_type}`", self.contract)

    def test_08_object_reference_remains_nonrecursive(self):
        normalized = " ".join(self.contract.lower().split())
        self.assertIn(
            "does not require recursive embedding",
            normalized,
        )
        self.assertIn(
            "complete canonical representation",
            normalized,
        )

    def test_09_unknown_absent_unavailable_redacted_semantics(self):
        lower = self.contract.lower()

        for phrase in (
            "not applicable",
            "unknown",
            "unavailable",
            "redacted",
            "approved safe reference",
        ):
            self.assertIn(phrase, lower)

        self.assertIn(
            "bare absence shall not be used",
            lower,
        )

    def test_10_transfer_disposition_vocabulary_exactly_preserved(self):
        section = re.search(
            r"## 11\. Transfer disposition vocabulary(.*?)"
            r"## 12\.",
            self.contract,
            flags=re.S,
        )
        self.assertIsNotNone(section)

        found = set(re.findall(
            r"^- `([A-Z_]+)`$",
            section.group(1),
            flags=re.M,
        ))

        self.assertEqual(found, TRANSFER_STATES)

    def test_11_scribe_disposition_vocabulary_exactly_preserved(self):
        section = re.search(
            r"## 12\. Scribe disposition vocabulary(.*?)"
            r"## 13\.",
            self.contract,
            flags=re.S,
        )
        self.assertIsNotNone(section)

        found = set(re.findall(
            r"^- `([A-Z_]+)`$",
            section.group(1),
            flags=re.M,
        ))

        self.assertEqual(found, SCRIBE_STATES)

    def test_12_structural_validity_does_not_create_authority(self):
        lower = self.contract.lower()

        self.assertIn(
            "structural validity is not authorization",
            lower,
        )

        self.assertIn(
            "a structurally valid `transferrequest` does not authorize transfer",
            lower,
        )

    def test_13_transferred_is_not_scribe_accept(self):
        lower = self.contract.lower()

        self.assertIn(
            "`transferred` does not mean",
            lower,
        )
        self.assertIn(
            "scribe `accept`",
            lower,
        )

    def test_14_transferred_does_not_authorize_deployment(self):
        section = re.search(
            r"## 11\. Transfer disposition vocabulary(.*?)"
            r"## 12\.",
            self.contract,
            flags=re.S,
        )
        self.assertIsNotNone(section)
        self.assertIn(
            "deployment approval",
            section.group(1).lower(),
        )

    def test_15_scribe_accept_not_deployment_or_conduit_authority(self):
        section = re.search(
            r"## 12\. Scribe disposition vocabulary(.*?)"
            r"## 13\.",
            self.contract,
            flags=re.S,
        )
        self.assertIsNotNone(section)

        lower = section.group(1).lower()
        self.assertIn("deployment", lower)
        self.assertIn("conduit execution", lower)

    def test_16_cross_object_conflicts_fail_closed(self):
        lower = self.contract.lower()

        self.assertIn(
            "a conflicting consequential binding shall fail validation",
            lower,
        )

        for forbidden_behavior in (
            "rewrite the conflict",
            "merge conflicting identities",
            "normalize away the difference",
            "choose one conflicting value",
        ):
            self.assertIn(forbidden_behavior, lower)

    def test_17_retry_replay_unknown_prior_state_preserved(self):
        lower = self.contract.lower()

        for phrase in (
            "predecessor",
            "retry",
            "duplicate",
            "replay",
        ):
            self.assertIn(phrase, lower)

        for state in (
            "`unknown`",
            "`partial`",
            "`incomplete`",
        ):
            self.assertIn(state, lower)

        self.assertIn(
            "unresolved state shall survive derivation",
            lower,
        )

    def test_18_cancellation_revocation_history_preserved(self):
        lower = self.contract.lower()

        for phrase in (
            "cancellation",
            "revocation",
            "amendment",
            "supersession",
        ):
            self.assertIn(phrase, lower)

        self.assertIn(
            "shall preserve historical attribution",
            lower,
        )

    def test_19_canonical_byte_and_crypto_choices_unselected(self):
        lower = self.contract.lower()

        for phrase in (
            "canonical bytes",
            "byte ordering",
            "field ordering",
            "serialization ordering",
            "hash algorithm",
            "signature algorithm",
            "certificate technology",
            "key technology",
        ):
            self.assertIn(phrase, lower)

        self.assertIn(
            "wp6.3 does not define",
            lower,
        )

    def test_20_dec08_remains_deferred(self):
        lower = self.contract.lower()

        self.assertIn("dec-08 remains deferred", lower)

        for phrase in (
            "trusted time source",
            "clock-skew tolerance",
            "freshness interval",
            "replay time window",
            "time-based authorization guarantee",
        ):
            self.assertIn(phrase, lower)

    def test_21_dec06_through_dec13_remain_deferred(self):
        lower = self.contract.lower()

        self.assertIn(
            "dec-06 through dec-13 remain deferred",
            lower,
        )

        for number in range(6, 14):
            self.assertIn(f"dec-{number:02d}", lower)

    def test_22_schema_evolution_creates_no_authority(self):
        lower = self.contract.lower()

        self.assertIn(
            "representation evolution shall not create authority",
            lower,
        )
        self.assertIn(
            "newer or unsupported representation shall not be silently accepted",
            lower,
        )

    def test_23_semantic_round_trip_required_without_byte_identity(self):
        lower = self.contract.lower()

        self.assertIn(
            "semantic round-trip requirement",
            lower,
        )
        self.assertIn(
            "canonical logical object",
            lower,
        )
        self.assertIn(
            "concrete representation",
            lower,
        )
        self.assertIn(
            "logical interpretation",
            lower,
        )
        self.assertIn(
            "does not require or define byte-for-byte equality",
            lower,
        )

    def test_24_negative_conformance_expectations_exist(self):
        lower = self.contract.lower()

        required_cases = (
            "omitted required security-relevant field",
            "invalid enum value",
            "unsupported logical-object type",
            "unsupported representation or schema version",
            "conflicting work-package revision",
            "conflicting authorization",
            "artifact substitution",
            "target mismatch",
            "operation mismatch",
            "malformed required reference",
            "unresolved required reference",
            "fabricated provenance",
            "unknown value collapsed to success",
            "`partial` collapsed to complete or transferred",
            "`incomplete` collapsed to complete",
            "retry without a required predecessor relationship",
            "replay treated as a fresh operation",
            "revoked authority treated as valid",
            "cancelled authority treated as valid",
            "`transferred` interpreted as scribe `accept`",
            "scribe `accept` interpreted as deployment authority",
            "scribe `accept` interpreted as conduit authority",
        )

        for case in required_cases:
            self.assertIn(case, lower)

    def test_25_no_concrete_schema_or_runtime_selected(self):
        lower = self.contract.lower()

        self.assertIn(
            "wp6.3 defines semantic requirements only",
            lower,
        )

        affirmative_patterns = (
            r"\bshall\s+use\s+json\b",
            r"\bshall\s+use\s+json schema\b",
            r"\bshall\s+use\s+yaml\b",
            r"\bshall\s+use\s+toml\b",
            r"\bshall\s+use\s+xml\b",
            r"\bshall\s+use\s+protocol buffers\b",
            r"\bshall\s+use\s+avro\b",
            r"\bshall\s+use\s+cbor\b",
            r"\bshall\s+use\s+messagepack\b",
            r"\bshall\s+use\s+asn\.1\b",
            r"\bshall\s+use\s+rest\b",
            r"\bshall\s+use\s+grpc\b",
            r"\bshall\s+use\s+sqlite\b",
            r"\bshall\s+use\s+sha-256\b",
            r"\bshall\s+use\s+ed25519\b",
        )

        for pattern in affirmative_patterns:
            self.assertIsNone(
                re.search(pattern, lower),
                msg=f"premature technology selection: {pattern}",
            )

    def test_26_no_numeric_operational_defaults_selected(self):
        lower = self.contract.lower()

        patterns = (
            r"\bport\s*[:=]\s*\d+",
            r"\btimeout\s*[:=]\s*\d+",
            r"\bconcurrency\s*[:=]\s*\d+",
            r"\bretention\s*[:=]\s*\d+",
            r"\bfreshness\s*[:=]\s*\d+",
            r"\bclock\s+skew\s*[:=]\s*\d+",
        )

        for pattern in patterns:
            self.assertIsNone(
                re.search(pattern, lower),
                msg=f"numeric operational default selected: {pattern}",
            )

    def test_27_ai_and_automation_cannot_self_approve(self):
        lower = self.contract.lower()

        self.assertIn(
            "ai output does not constitute architecture approval",
            lower,
        )
        self.assertIn(
            "no loop may convert its own successful tests into architecture approval",
            lower,
        )
        self.assertIn(
            "operator remains the architecture/security approval authority",
            lower,
        )

    def test_28_automation_preserves_distinct_authority_states(self):
        lower = self.contract.lower()

        for state in (
            "proposal",
            "generation",
            "validation",
            "rejection",
            "revision",
            "operator decision",
            "transfer disposition",
            "scribe disposition",
            "deployment disposition",
        ):
            self.assertIn(state, lower)

    def test_29_conduit_does_not_create_authorization(self):
        lower = self.contract.lower()

        self.assertIn(
            "conduit enforces separately applicable authorized management/deployment",
            lower,
        )
        self.assertIn(
            "does not create the authorization it enforces",
            lower,
        )

    def test_30_repository_tests_are_not_operational_acceptance(self):
        lower = self.contract.lower()

        self.assertIn(
            "they are not operational acceptance",
            lower,
        )

        for phrase in (
            "runtime correctness",
            "runtime security",
            "host readiness",
            "network readiness",
            "credential readiness",
            "courier readiness",
            "scribe readiness",
            "deployment readiness",
            "production readiness",
        ):
            self.assertIn(phrase, lower)

    def test_31_completion_requires_operator_approval(self):
        lower = self.contract.lower()

        self.assertIn(
            "operator explicitly approves the wp6.3 candidate",
            lower,
        )
        self.assertIn(
            "completion of wp6.3 does not authorize runtime implementation",
            lower,
        )

    def test_32_plan_and_contract_share_fail_closed_boundary(self):
        self.assertIn(
            "The stop condition is fail closed.",
            self.plan,
        )
        self.assertIn(
            "The stop condition is fail closed.",
            self.contract,
        )


if __name__ == "__main__":
    unittest.main()
