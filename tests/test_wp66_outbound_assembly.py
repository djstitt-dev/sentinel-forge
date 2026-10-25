import dataclasses
from pathlib import Path
import tempfile
import unittest

from sentinel_forge.assembly import AssemblyContext, AssemblyError, assemble_outbound
from sentinel_forge.contract import ContractBundle
from sentinel_forge.package import build_manifest

class OutboundAssemblyTests(unittest.TestCase):
    def setUp(self):
        self.td=tempfile.TemporaryDirectory()
        self.root=Path(self.td.name)
        (self.root/"candidate.bin").write_bytes(b"sentinel candidate\n")
        self.manifest=build_manifest(
            self.root,["candidate.bin"],work_package_revision="rev-42",
            artifact_type_class="candidate",classification_handling="controlled")
        self.ctx=AssemblyContext(
            work_package_id="wp6",revision_id="rev-42",authorization_id="auth-7",
            authorizing_authority="operator",authorized_principal="forge",
            scope_reference="scope-7",target="scribe",operation="controlled-transfer",
            policy_reference="policy-7",classification_handling="controlled",
            correlation_id="corr-9",allowed_action_classes="transfer",
            intended_purpose_disposition="scribe-evaluation",
            expected_transfer_effect_class="controlled-copy",
            canonical_integrity_reference="revision-integrity-42")

    def tearDown(self): self.td.cleanup()

    def test_assembly_passes_contract_validation(self):
        p=assemble_outbound(self.manifest,self.ctx)
        self.assertTrue(p.approved_for_courier_boundary)
        self.assertTrue(ContractBundle(p.objects).validate().accepted)

    def test_assembly_does_not_fabricate_transfer_or_scribe_success(self):
        p=assemble_outbound(self.manifest,self.ctx)
        self.assertEqual("PROPOSED",p.objects["TransferReceipt"]["transfer_disposition"])
        self.assertEqual("UNKNOWN",p.objects["TransferReceipt"]["validation_outcome"])
        self.assertEqual("UNKNOWN",p.objects["ScribeDisposition"]["disposition"])
        self.assertFalse(p.courier_effect_established)
        self.assertFalse(p.scribe_acceptance_established)

    def test_exact_identity_propagates_across_objects(self):
        p=assemble_outbound(self.manifest,self.ctx).objects
        aid=self.manifest.artifact_id
        self.assertEqual(aid,p["ArtifactIdentity"]["artifact_id"])
        self.assertEqual(aid,p["CorrelationIdentity"]["artifact_identity"])
        self.assertEqual(aid,p["TransferRequest"]["artifact_identity"])
        self.assertEqual(aid,p["TransferReceipt"]["artifact_identity"])
        self.assertEqual(aid,p["ScribeDisposition"]["artifact_identity"])

    def test_revision_mismatch_refused_before_assembly(self):
        bad=dataclasses.replace(self.ctx,revision_id="rev-wrong")
        with self.assertRaises(AssemblyError): assemble_outbound(self.manifest,bad)

    def test_classification_mismatch_refused(self):
        bad=dataclasses.replace(self.ctx,classification_handling="wrong")
        with self.assertRaises(AssemblyError): assemble_outbound(self.manifest,bad)

    def test_revoked_authority_refused(self):
        bad=dataclasses.replace(self.ctx,revocation_cancellation_state="REVOKED")
        with self.assertRaises(AssemblyError): assemble_outbound(self.manifest,bad)

    def test_unknown_authority_refused(self):
        bad=dataclasses.replace(self.ctx,authorization_state="UNKNOWN")
        with self.assertRaises(AssemblyError): assemble_outbound(self.manifest,bad)

    def test_unresolved_prior_attempt_refused(self):
        bad=dataclasses.replace(self.ctx,prior_attempt_reconciliation_state="UNRESOLVED_UNKNOWN")
        with self.assertRaises(AssemblyError): assemble_outbound(self.manifest,bad)

    def test_empty_context_value_refused(self):
        bad=dataclasses.replace(self.ctx,target="")
        with self.assertRaises(AssemblyError): assemble_outbound(self.manifest,bad)

    def test_post_assembly_artifact_substitution_detected(self):
        p=assemble_outbound(self.manifest,self.ctx)
        p.objects["TransferRequest"]["artifact_identity"]="evil"
        r=ContractBundle(p.objects).validate()
        self.assertFalse(r.accepted)
        self.assertIn("ARTIFACT_MISMATCH",{x.code for x in r.issues})

    def test_post_assembly_target_substitution_detected(self):
        p=assemble_outbound(self.manifest,self.ctx)
        p.objects["TransferRequest"]["destination"]="evil-target"
        self.assertIn("TARGET_MISMATCH",
            {x.code for x in ContractBundle(p.objects).validate().issues})

    def test_post_assembly_operation_substitution_detected(self):
        p=assemble_outbound(self.manifest,self.ctx)
        p.objects["TransferReceipt"]["transfer_operation"]="evil-op"
        self.assertIn("OPERATION_MISMATCH",
            {x.code for x in ContractBundle(p.objects).validate().issues})

if __name__=="__main__": unittest.main()
