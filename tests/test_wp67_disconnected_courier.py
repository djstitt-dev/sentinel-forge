import copy
from pathlib import Path
import tempfile
import unittest

from sentinel_forge.assembly import AssemblyContext, assemble_outbound
from sentinel_forge.courier import ConflictingReplay, CourierRejected, DisconnectedCourier
from sentinel_forge.package import build_manifest

class DisconnectedCourierTests(unittest.TestCase):
    def setUp(self):
        self.td=tempfile.TemporaryDirectory(); root=Path(self.td.name)
        (root/"x").write_bytes(b"x")
        manifest=build_manifest(root,["x"],work_package_revision="r1",
            artifact_type_class="candidate",classification_handling="controlled")
        ctx=AssemblyContext(
            work_package_id="wp",revision_id="r1",authorization_id="a1",
            authorizing_authority="operator",authorized_principal="forge",
            scope_reference="scope",target="scribe",operation="controlled-transfer",
            policy_reference="p1",classification_handling="controlled",
            correlation_id="c1",allowed_action_classes="transfer",
            intended_purpose_disposition="scribe-evaluation",
            expected_transfer_effect_class="controlled-copy",
            canonical_integrity_reference="ri1")
        self.package=assemble_outbound(manifest,ctx)
        self.courier=DisconnectedCourier("courier-test")

    def tearDown(self): self.td.cleanup()

    def test_first_submission_records_proposed_offline_receipt(self):
        r=self.courier.submit(self.package.objects)
        self.assertFalse(r.replayed)
        self.assertEqual("PROPOSED",r.receipt["transfer_disposition"])
        self.assertEqual("PASS_OFFLINE_ONLY",r.receipt["validation_outcome"])
        self.assertNotEqual("TRANSFERRED",r.receipt["transfer_disposition"])

    def test_exact_replay_returns_same_receipt_without_new_effect(self):
        first=self.courier.submit(self.package.objects)
        second=self.courier.submit(self.package.objects)
        self.assertTrue(second.replayed)
        self.assertEqual(first.receipt,second.receipt)
        self.assertEqual(first.request_fingerprint,second.request_fingerprint)

    def test_lookup_is_non_effecting(self):
        self.assertIsNone(self.courier.lookup("c1"))
        first=self.courier.submit(self.package.objects)
        found=self.courier.lookup("c1")
        self.assertTrue(found.replayed)
        self.assertEqual(first.receipt,found.receipt)

    def test_same_correlation_different_request_is_conflicting_replay(self):
        self.courier.submit(self.package.objects)
        altered=copy.deepcopy(self.package.objects)
        altered["TransferRequest"]["intended_purpose_disposition"]="different"
        with self.assertRaises(ConflictingReplay):
            self.courier.submit(altered)

    def test_conflicting_replay_preserves_original_record(self):
        first=self.courier.submit(self.package.objects)
        altered=copy.deepcopy(self.package.objects)
        altered["TransferRequest"]["expected_transfer_effect_class"]="different"
        with self.assertRaises(ConflictingReplay):
            self.courier.submit(altered)
        found=self.courier.lookup("c1")
        self.assertEqual(first.receipt,found.receipt)
        self.assertEqual(first.request_fingerprint,found.request_fingerprint)

    def test_invalid_cross_binding_rejected_before_record(self):
        altered=copy.deepcopy(self.package.objects)
        altered["TransferRequest"]["destination"]="evil"
        with self.assertRaises(CourierRejected):
            self.courier.submit(altered)
        self.assertIsNone(self.courier.lookup("c1"))

    def test_revoked_authority_rejected(self):
        altered=copy.deepcopy(self.package.objects)
        altered["AuthorizationReference"]["revocation_cancellation_state"]="REVOKED"
        with self.assertRaises(CourierRejected): self.courier.submit(altered)

    def test_courier_receipt_does_not_change_scribe_state(self):
        before=copy.deepcopy(self.package.objects["ScribeDisposition"])
        self.courier.submit(self.package.objects)
        self.assertEqual(before,self.package.objects["ScribeDisposition"])
        self.assertEqual("UNKNOWN",self.package.objects["ScribeDisposition"]["disposition"])

    def test_courier_has_no_transport_surface(self):
        self.assertFalse(hasattr(self.courier,"connect"))
        self.assertFalse(hasattr(self.courier,"send"))
        self.assertFalse(hasattr(self.courier,"deploy"))

if __name__=="__main__": unittest.main()
