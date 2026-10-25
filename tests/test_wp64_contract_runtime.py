import copy
import json
import subprocess
import sys
import unittest

from sentinel_forge.contract import ContractBundle, FIELD_RULES

def bundle():
    r, a, c, art, auth = "rev-1", "artifact-1", "corr-1", "forge-worker", "auth-1"
    target, op, policy = "scribe", "controlled-transfer", "policy-1"
    return {
        "WorkPackageRevision": {
            "work_package_id":"wp6","revision_id":r,"authorization_state":"AUTHORIZED",
            "authorization_reference":auth,"scope_reference":"scope-1",
            "resource_target_scope":target,"allowed_action_classes":"transfer",
            "policy_reference":policy,"cancellation_revocation_state":"ACTIVE",
            "canonical_integrity_reference":"integrity-rev-1",
        },
        "ArtifactIdentity": {
            "artifact_id":art,"artifact_type_class":"candidate",
            "integrity_reference":"integrity-art-1","integrity_provenance":"forge",
            "source_work_package_revision":r,"source_component":"forge",
            "classification_handling":"approved-class","completeness_state":"COMPLETE",
        },
        "AuthorizationReference": {
            "authorization_id":auth,"authorizing_authority":"operator",
            "authorized_principal":a,"authorized_work_package_revision":r,
            "permitted_action":op,"permitted_target_resource":target,
            "policy_reference":policy,"authorization_state":"AUTHORIZED",
            "revocation_cancellation_state":"ACTIVE",
        },
        "CorrelationIdentity": {
            "operation_correlation_id":c,"originating_identity":a,
            "work_package_revision":r,"target_component":target,
            "requested_operation":op,"artifact_identity":art,
        },
        "TransferRequest": {
            "source_identity":a,"destination":target,"transfer_operation":op,
            "work_package_revision":r,"authorization_reference":auth,
            "artifact_identity":art,"policy_reference":policy,
            "classification_handling":"approved-class","correlation_identity":c,
            "intended_purpose_disposition":"scribe-evaluation",
            "expected_transfer_effect_class":"controlled-copy",
            "prior_attempt_reconciliation_state":"NO_KNOWN_PREDECESSOR",
        },
        "TransferReceipt": {
            "courier_identity":"courier","source_identity":a,"destination":target,
            "transfer_operation":op,"work_package_revision":r,
            "authorization_reference":auth,"artifact_identity":art,
            "correlation_identity":c,"policy_classification":"approved-class",
            "transfer_disposition":"TRANSFERRED","validation_outcome":"PASS",
            "completeness_state":"COMPLETE",
            "retry_reconciliation_state":"NO_KNOWN_PREDECESSOR",
        },
        "ScribeDisposition": {
            "scribe_authority_identity":"scribe","work_package_revision":r,
            "artifact_identity":art,"authorization_policy_reference":policy,
            "release_evidence_policy_identity":"scribe-policy",
            "disposition":"ACCEPT","validation_evaluation_references":"validation-1",
            "reason_reference":"reason-1",
        },
    }

class ContractRuntimeTests(unittest.TestCase):
    def test_inventory_is_exactly_7_objects_and_83_fields(self):
        self.assertEqual(7, len(FIELD_RULES))
        self.assertEqual(83, sum(len(v) for v in FIELD_RULES.values()))
        counts = {"REQUIRED":0,"CONDITIONAL":0,"OPTIONAL_OR_AVAILABLE":0}
        for fields in FIELD_RULES.values():
            for requirement in fields.values():
                counts[requirement] += 1
        self.assertEqual({"REQUIRED":65,"CONDITIONAL":11,"OPTIONAL_OR_AVAILABLE":7}, counts)

    def test_valid_logical_bundle_passes_offline_validation(self):
        result = ContractBundle(bundle()).validate()
        self.assertTrue(result.accepted, result.issues)

    def test_missing_required_field_fails_closed(self):
        b = bundle(); del b["TransferRequest"]["authorization_reference"]
        result = ContractBundle(b).validate()
        self.assertFalse(result.accepted)
        self.assertIn("MISSING_REQUIRED_FIELD", {x.code for x in result.issues})

    def test_unknown_field_fails_closed(self):
        b = bundle(); b["TransferRequest"]["magic_authority"] = True
        result = ContractBundle(b).validate()
        self.assertFalse(result.accepted)
        self.assertIn("UNKNOWN_FIELD", {x.code for x in result.issues})

    def test_work_package_substitution_fails(self):
        b = bundle(); b["TransferReceipt"]["work_package_revision"] = "rev-evil"
        result = ContractBundle(b).validate()
        self.assertIn("WORK_PACKAGE_MISMATCH", {x.code for x in result.issues})

    def test_artifact_substitution_fails(self):
        b = bundle(); b["ScribeDisposition"]["artifact_identity"] = "artifact-evil"
        result = ContractBundle(b).validate()
        self.assertIn("ARTIFACT_MISMATCH", {x.code for x in result.issues})

    def test_wrong_target_and_operation_fail(self):
        b = bundle(); b["TransferRequest"]["destination"] = "wrong"
        b["TransferReceipt"]["transfer_operation"] = "wrong-op"
        codes = {x.code for x in ContractBundle(b).validate().issues}
        self.assertIn("TARGET_MISMATCH", codes)
        self.assertIn("OPERATION_MISMATCH", codes)

    def test_unknown_authority_fails_closed(self):
        b = bundle(); b["AuthorizationReference"]["authorization_state"] = "UNKNOWN"
        self.assertIn("AUTHORITY_NOT_ESTABLISHED",
                      {x.code for x in ContractBundle(b).validate().issues})

    def test_revoked_authority_fails_closed(self):
        b = bundle(); b["AuthorizationReference"]["revocation_cancellation_state"] = "REVOKED"
        self.assertIn("REVOCATION_STATE_BLOCKS",
                      {x.code for x in ContractBundle(b).validate().issues})

    def test_unknown_or_incomplete_state_fails_closed(self):
        for value in ("UNKNOWN", "INCOMPLETE"):
            with self.subTest(value=value):
                b = bundle(); b["ArtifactIdentity"]["completeness_state"] = value
                self.assertIn("INCOMPLETE_OR_UNKNOWN",
                              {x.code for x in ContractBundle(b).validate().issues})

    def test_unresolved_prior_outcome_blocks_repeat(self):
        b = bundle()
        b["TransferRequest"]["prior_attempt_reconciliation_state"] = "UNRESOLVED_UNKNOWN"
        self.assertIn("UNRESOLVED_PRIOR_OUTCOME",
                      {x.code for x in ContractBundle(b).validate().issues})

    def test_exact_disposition_vocabularies(self):
        b = bundle(); b["TransferReceipt"]["transfer_disposition"] = "SUCCESS"
        self.assertIn("INVALID_TRANSFER_DISPOSITION",
                      {x.code for x in ContractBundle(b).validate().issues})
        b = bundle(); b["ScribeDisposition"]["disposition"] = "APPROVED"
        self.assertIn("INVALID_SCRIBE_DISPOSITION",
                      {x.code for x in ContractBundle(b).validate().issues})

    def test_cli_is_offline_and_machine_readable(self):
        p = subprocess.run(
            [sys.executable, "-m", "sentinel_forge.validate"],
            input=json.dumps(bundle()), text=True, capture_output=True, check=False,
        )
        self.assertEqual(0, p.returncode, p.stderr)
        self.assertTrue(json.loads(p.stdout)["accepted"])

    def test_cli_rejects_malformed_input(self):
        p = subprocess.run(
            [sys.executable, "-m", "sentinel_forge.validate"],
            input="{bad", text=True, capture_output=True, check=False,
        )
        self.assertEqual(2, p.returncode)
        self.assertFalse(json.loads(p.stdout)["accepted"])

if __name__ == "__main__":
    unittest.main()
