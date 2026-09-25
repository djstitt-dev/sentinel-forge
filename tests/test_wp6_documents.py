"""Offline structural checks for WP6.1 preparation documents.

These tests validate repository documentation only. Passing them does not
establish runtime correctness, host state, deployment approval, release approval,
or operational readiness.
"""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]

PLAN = ROOT / "docs/plans/wp6-forge-courier-scribe-preparation.md"
CONTRACT = ROOT / "docs/architecture/forge-courier-scribe-contract.md"
WP5_ARCH = ROOT / "docs/architecture/forge-operational-architecture.md"
WP5_REQ = ROOT / "docs/plans/wp5-operational-requirements.md"

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

DEFERRED_DECISIONS = tuple(f"DEC-{number:02d}" for number in range(6, 14))


class WP61DocumentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = PLAN.read_text()
        cls.contract = CONTRACT.read_text()
        cls.wp5_arch = WP5_ARCH.read_text()
        cls.wp5_req = WP5_REQ.read_text()

    def test_documents_bind_to_approved_wp5_revision(self):
        self.assertIn(APPROVED_WP5_REVISION, self.plan)
        self.assertIn(APPROVED_WP5_REVISION, self.contract)

    def test_required_logical_object_sections_exist_once(self):
        for name in LOGICAL_OBJECTS:
            matches = re.findall(
                rf"^## \d+\. Logical object: {re.escape(name)}$",
                self.contract,
                flags=re.MULTILINE,
            )
            self.assertEqual(
                len(matches),
                1,
                f"{name} logical-object section must exist exactly once",
            )

    def test_authority_separation_is_explicit(self):
        required = (
            "Forge cannot mark Scribe-controlled release/evidence state.",
            "Courier cannot mark Scribe-controlled release/evidence state.",
            "Courier cannot create deployment authority.",
            "Scribe controlled release/evidence acceptance cannot create deployment authority.",
            "A successful Forge build does not authorize transfer.",
            "A successful Courier transfer does not establish Scribe acceptance.",
            "A Scribe ACCEPT disposition does not authorize deployment.",
        )
        for statement in required:
            self.assertIn(statement, self.contract)

    def test_transfer_request_requires_core_bindings(self):
        section = self._section(
            "## 9. Logical object: TransferRequest",
            "## 10. Logical object: TransferReceipt",
        )
        required = (
            "requesting/source principal or component",
            "exact target component/destination",
            "exact requested transfer operation",
            "exact `WorkPackageRevision`",
            "`AuthorizationReference`",
            "`ArtifactIdentity`",
            "`CorrelationIdentity`",
            "classification/data-handling designation",
            "known prior-attempt/reconciliation state",
        )
        for field in required:
            self.assertIn(field, section)

    def test_transfer_receipt_preserves_failure_states_and_ordering(self):
        section = self._section(
            "## 10. Logical object: TransferReceipt",
            "## 11. Logical object: ScribeDisposition",
        )
        required = (
            "`INCOMPLETE`/`PARTIAL`/`UNKNOWN`",
            "start/end time information with uncertainty",
            "ordered-event",
            "retry/reconciliation state",
            "destination acknowledgement state",
            "Forge consumes `TransferReceipt` as evidence only.",
        )
        for field in required:
            self.assertIn(field, section)

        self.assertIn(
            "not establish trusted chronological freshness",
            section,
        )

    def test_scribe_disposition_is_bounded(self):
        section = self._section(
            "## 11. Logical object: ScribeDisposition",
            "## 12. Logical processing sequence",
        )
        self.assertIn(
            "controlled disposition: `ACCEPT`, `REJECT` or `UNKNOWN`",
            section,
        )
        self.assertIn(
            "Only Scribe's approved controlled release/evidence decision path",
            section,
        )
        self.assertIn(
            "`ACCEPT` establishes only Scribe-controlled release/evidence acceptance.",
            section,
        )
        for prohibited in (
            "deployment;",
            "Conduit execution;",
            "direct Forge administration;",
            "host mutation;",
            "privileged execution;",
            "AIDE trust transition;",
        ):
            self.assertIn(prohibited, section)

    def test_unknown_partial_incomplete_cannot_collapse_to_success(self):
        required = (
            "An unresolved sensitive outcome remains `UNKNOWN`.",
            "`PARTIAL` and `INCOMPLETE` objects or operations cannot become accepted",
            "`UNKNOWN`, `PARTIAL` and `INCOMPLETE` shall survive cross-component handoff",
            "Omission of a field or missing result shall not collapse such a state into",
        )
        for statement in required:
            self.assertIn(statement, self.contract)

    def test_replay_duplicate_and_unknown_retry_require_reconciliation(self):
        required = (
            "A sensitive operation with unresolved prior outcome shall not be blindly",
            "permit duplicate detection",
            "permit replay detection under approved policy",
            "link retries to the prior attempt",
            "A retry following `UNKNOWN` shall first reconcile the prior operation",
        )
        for statement in required:
            self.assertIn(statement, self.contract)

    def test_deferred_decisions_remain_deferred(self):
        deferred_section = self._section(
            "## 16. Deferred-dependency register",
            "## 17. Required offline test cases for WP6.1",
        )
        for decision in DEFERRED_DECISIONS:
            self.assertRegex(
                deferred_section,
                rf"(?m)^### {re.escape(decision)}\b",
            )

        self.assertIn(
            "DEC-06 through DEC-13 retain their capability-scoped deferrals.",
            self.plan,
        )
        self.assertIn(
            "A deferral is not approval of an unknown value.",
            self.plan,
        )

    def test_dec08_does_not_gain_trusted_time_default(self):
        required = (
            "No trusted time source, skew bound or numeric freshness interval is selected.",
            "timestamps alone shall not establish authorization or freshness",
            "no implementation may invent a freshness window",
        )
        for statement in required:
            self.assertIn(statement, self.contract)

    def test_no_runtime_mechanism_is_authorized(self):
        required = (
            "does not authorize runtime implementation",
            "network connectivity",
            "credential creation",
            "deployment",
            "privileged execution",
            "AIDE operations",
        )
        for statement in required:
            self.assertIn(statement, self.plan)

        self.assertIn(
            "No application source package, runtime configuration, network service, credential",
            self.plan,
        )

    def test_admission_matrix_contains_required_classifications(self):
        matrix = self._section(
            "## 15. Requirement admission matrix",
            "## 16. Deferred-dependency register",
        )
        for classification in (
            "ADMITTED_FOR_PREPARATION",
            "PARTIAL_PREPARATION_ONLY",
            "BLOCKED_PENDING_OPERATOR_DECISION",
        ):
            self.assertIn(classification, matrix)

        blocked = (
            "FORGE-AI-004",
            "FORGE-AI-007",
            "FORGE-AI-010",
        )
        for requirement in blocked:
            self.assertRegex(
                matrix,
                rf"\|\s*{re.escape(requirement)}\s*\|\s*BLOCKED_PENDING_OPERATOR_DECISION\s*\|",
            )

    def test_wp5_source_preserves_transfer_release_deployment_separation(self):
        required = (
            "Creation, transfer authorization, execution, destination acceptance, release and",
            "A successful build cannot authorize transfer.",
            "Neither transfer nor its receipt grants",
            "release/deployment approval.",
        )
        for statement in required:
            self.assertIn(statement, self.wp5_arch)

    def test_wp5_source_preserves_unknown_retry_rule(self):
        required = (
            "an unknown outcome is not a",
            "successful outcome.",
            "No automatic retry may repeat a privileged effect whose prior",
            "result is unknown.",
        )
        for statement in required:
            self.assertIn(statement, self.wp5_arch)

    def test_plan_and_contract_deny_operational_readiness_claim(self):
        self.assertIn(
            "operational-readiness claims",
            self.plan,
        )
        self.assertIn(
            "This document is an implementation-preparation artifact only.",
            self.contract,
        )
        self.assertIn(
            "production readiness.",
            self.contract,
        )

    def test_document_tests_are_not_operational_acceptance(self):
        self.assertIn(
            "Passing document tests cannot be represented as operational acceptance.",
            self.contract,
        )
        self.assertIn(
            "offline structural validation",
            self.plan,
        )

    def test_wp5_decisions_06_through_13_are_still_deferred(self):
        for decision in DEFERRED_DECISIONS:
            pattern = (
                rf"(?m)^\|\s*{re.escape(decision)}\s*\|.*"
                rf"DEFERRED FOR INITIAL CAPABILITY"
            )
            self.assertRegex(
                self.wp5_req,
                pattern,
                f"{decision} must remain deferred in WP5 source",
            )

    def test_stop_boundary_blocks_dependent_runtime_choices(self):
        section = self._section(
            "## 19. WP6.1 stop boundary",
            "## 20. Readiness statement",
        )
        required = (
            "runtime transport must be selected",
            "credential technology or secrets must be created",
            "trusted-time behavior is required",
            "numeric resource or retry bounds become required",
            "workload isolation must be selected",
            "network egress or inbound connectivity becomes required",
            "deployment or Conduit execution becomes required",
            "host, privileged or AIDE action would be required",
            "repository identity/integrity becomes unexplained",
        )
        for statement in required:
            self.assertIn(statement, section)

    def test_contract_contains_no_obvious_selected_runtime_stack(self):
        prohibited_selected_patterns = (
            r"\buse\s+SSH\b",
            r"\buse\s+HTTPS\b",
            r"\buse\s+gRPC\b",
            r"\buse\s+REST\b",
            r"\buse\s+SQLite\b",
            r"\buse\s+PostgreSQL\b",
            r"\buse\s+mTLS\b",
            r"\buse\s+OAuth\b",
            r"\buse\s+OIDC\b",
            r"\buse\s+JWT\b",
        )
        for pattern in prohibited_selected_patterns:
            self.assertNotRegex(self.contract, pattern)

    @staticmethod
    def _section(text_start, text_end):
        text = WP61DocumentTests.contract
        start = text.find(text_start)
        end = text.find(text_end)
        if start == -1 or end == -1 or end <= start:
            raise AssertionError(
                f"Unable to isolate section {text_start!r} -> {text_end!r}"
            )
        return text[start:end]


if __name__ == "__main__":
    unittest.main()
