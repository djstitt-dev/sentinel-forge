from pathlib import Path
import tempfile, unittest
from sentinel_forge.assembly import AssemblyContext, assemble_outbound
from sentinel_forge.audited_effects import AuditedEffectCoordinator
from sentinel_forge.courier_effects import DurableEffectCoordinator, ReconciliationRequired
from sentinel_forge.evidence import EvidenceJournal
from sentinel_forge.package import build_manifest
from sentinel_forge.transport import DisconnectedTransport

class Boom:
    def effect(self,request): raise RuntimeError("boom")

class AuditedEffectsTests(unittest.TestCase):
    def setUp(self):
        self.td=tempfile.TemporaryDirectory(); root=Path(self.td.name); (root/"x").write_bytes(b"x")
        m=build_manifest(root,["x"],work_package_revision="r1",artifact_type_class="candidate",classification_handling="controlled")
        c=AssemblyContext(work_package_id="wp",revision_id="r1",authorization_id="a1",authorizing_authority="operator",
          authorized_principal="forge",scope_reference="scope",target="scribe",operation="controlled-transfer",
          policy_reference="p1",classification_handling="controlled",correlation_id="c1",allowed_action_classes="transfer",
          intended_purpose_disposition="scribe-evaluation",expected_transfer_effect_class="controlled-copy",
          canonical_integrity_reference="ri1")
        self.objects=assemble_outbound(m,c).objects
        self.j=EvidenceJournal(root/"evidence.jsonl")
        self.a=AuditedEffectCoordinator(DurableEffectCoordinator(root/"effects.sqlite"),self.j)
    def tearDown(self): self.td.cleanup()
    def test_known_rejection_emits_requested_and_outcome(self):
        self.a.execute(self.objects,DisconnectedTransport())
        self.assertEqual(["ATTEMPT_REQUESTED","REJECTED"],[x.outcome for x in self.j.verify()])
    def test_unknown_effect_is_evidenced_and_retry_stays_blocked(self):
        with self.assertRaises(ReconciliationRequired): self.a.execute(self.objects,Boom())
        self.assertEqual(["ATTEMPT_REQUESTED","OUTCOME_UNKNOWN"],[x.outcome for x in self.j.verify()])
        with self.assertRaises(ReconciliationRequired): self.a.execute(self.objects,Boom())
        self.assertEqual("OUTCOME_UNKNOWN",self.j.verify()[-1].outcome)
    def test_reconciliation_is_evidenced(self):
        with self.assertRaises(ReconciliationRequired): self.a.execute(self.objects,Boom())
        self.a.reconcile("c1",established_state="REJECTED")
        e=self.j.verify()[-1]
        self.assertEqual("operator-reconciliation",e.actor); self.assertEqual("REJECTED",e.outcome)
    def test_evidence_success_does_not_create_scribe_authority(self):
        self.a.execute(self.objects,DisconnectedTransport())
        self.assertEqual("UNKNOWN",self.objects["ScribeDisposition"]["disposition"])

if __name__=="__main__": unittest.main()
