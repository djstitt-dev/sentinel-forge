import unittest
from dataclasses import replace
from sentinel_forge.enrollment import EnrollmentError
from sentinel_forge.recovery import (
 SAFE_AUTOMATIC_REPAIR,RECONCILIATION_REQUIRED,OPERATOR_REQUIRED,TERMINAL,
 build_plan,classify,execute_safe_repair,observe,verify_plan,
)

class ConservativeRecoveryTests(unittest.TestCase):
 def test_known_derived_state_is_safe(self):
  o=observe(condition="missing_derived_cache",target="cache:a",observed_identity="sha256:a",details="absent")
  self.assertEqual(SAFE_AUTOMATIC_REPAIR,classify(o))
  self.assertEqual("REBUILD_DERIVED_LOCAL_STATE",build_plan(o).action)

 def test_unknown_condition_fails_to_operator(self):
  o=observe(condition="mystery",target="x",observed_identity="id",details="unknown")
  self.assertEqual(OPERATOR_REQUIRED,classify(o))

 def test_authority_ambiguity_requires_reconciliation(self):
  for condition in ("unresolved_transition_intent","ambiguous_authority_state","unknown_external_effect",
                    "partial_external_effect","consumed_challenge_without_authority_transition"):
   with self.subTest(condition=condition):
    self.assertEqual(RECONCILIATION_REQUIRED,classify(observe(
     condition=condition,target="enrollment:x",observed_identity="state:x",details="uncertain")))

 def test_revocation_and_integrity_failure_are_terminal(self):
  for condition in ("revoked_relationship","malformed_authority_state","evidence_integrity_failure"):
   with self.subTest(condition=condition):
    self.assertEqual(TERMINAL,classify(observe(
     condition=condition,target="authority:x",observed_identity="state:x",details="blocked")))

 def test_credentials_and_independence_require_operator(self):
  for condition in ("credential_rotation_required","credential_state_mismatch",
                    "development_access_present","production_independence_unverified"):
   with self.subTest(condition=condition):
    self.assertEqual(OPERATOR_REQUIRED,classify(observe(
     condition=condition,target="forge",observed_identity="state:x",details="operator boundary")))

 def test_plan_is_deterministic_and_observation_bound(self):
  o=observe(condition="stale_local_index",target="index:a",observed_identity="sha256:a",details="stale")
  self.assertEqual(build_plan(o),build_plan(o))
  changed=replace(o,details="different")
  with self.assertRaisesRegex(EnrollmentError,"stale, altered"):verify_plan(build_plan(o),changed)

 def test_altered_plan_fails(self):
  o=observe(condition="missing_local_index",target="index:a",observed_identity="sha256:a",details="absent")
  p=build_plan(o)
  with self.assertRaises(EnrollmentError):verify_plan(replace(p,action="ACTIVATE"),o)

 def test_safe_executor_runs_only_bound_safe_plan(self):
  o=observe(condition="missing_derived_cache",target="cache:a",observed_identity="sha256:a",details="absent")
  p=build_plan(o);seen=[]
  self.assertEqual("REPAIRED",execute_safe_repair(p,o,lambda plan:seen.append(plan.plan_digest)))
  self.assertEqual([p.plan_digest],seen)

 def test_reconciliation_condition_cannot_execute(self):
  o=observe(condition="unknown_external_effect",target="effect:a",observed_identity="attempt:a",details="unknown")
  called=[]
  with self.assertRaisesRegex(EnrollmentError,"RECONCILIATION_REQUIRED"):
   execute_safe_repair(build_plan(o),o,lambda p:called.append(p))
  self.assertEqual([],called)

 def test_operator_condition_cannot_execute(self):
  o=observe(condition="credential_rotation_required",target="peer:a",observed_identity="cred:1",details="rotate")
  with self.assertRaisesRegex(EnrollmentError,"OPERATOR_REQUIRED"):
   execute_safe_repair(build_plan(o),o,lambda p:None)

 def test_terminal_condition_cannot_execute(self):
  o=observe(condition="revoked_relationship",target="peer:a",observed_identity="revoked",details="terminal")
  with self.assertRaisesRegex(EnrollmentError,"TERMINAL"):
   execute_safe_repair(build_plan(o),o,lambda p:None)

 def test_missing_observation_fields_fail(self):
  with self.assertRaises(EnrollmentError):observe(condition="",target="x",observed_identity="id",details="d")

class AuditedRecoveryTests(unittest.TestCase):
 def test_pre_audit_failure_blocks_repair(self):
  from sentinel_forge.recovery import execute_audited_safe_repair
  o=observe(condition="missing_local_index",target="index:a",observed_identity="id:a",details="absent");p=build_plan(o)
  class Broken:
   def append(self,**kw):raise RuntimeError("audit down")
  called=[]
  with self.assertRaises(RuntimeError):
   execute_audited_safe_repair(p,o,lambda plan:called.append(plan),Broken(),actor="forge")
  self.assertEqual([],called)

 def test_post_audit_failure_does_not_claim_success(self):
  from sentinel_forge.recovery import execute_audited_safe_repair
  o=observe(condition="missing_local_index",target="index:a",observed_identity="id:a",details="absent");p=build_plan(o)
  class SecondFails:
   def __init__(self):self.n=0
   def append(self,**kw):
    self.n+=1
    if self.n==2:raise RuntimeError("audit down")
  called=[]
  with self.assertRaisesRegex(EnrollmentError,"effect occurred"):
   execute_audited_safe_repair(p,o,lambda plan:called.append(plan.plan_digest),SecondFails(),actor="forge")
  self.assertEqual([p.plan_digest],called)

 def test_audited_safe_repair_records_attempt_and_completion(self):
  import tempfile
  from pathlib import Path
  from sentinel_forge.evidence import EvidenceJournal
  from sentinel_forge.recovery import execute_audited_safe_repair
  o=observe(condition="stale_derived_cache",target="cache:a",observed_identity="id:a",details="stale");p=build_plan(o)
  with tempfile.TemporaryDirectory() as td:
   e=EvidenceJournal(Path(td)/"e.jsonl")
   self.assertEqual("REPAIRED",execute_audited_safe_repair(p,o,lambda plan:None,e,actor="forge"))
   self.assertEqual(["REPAIR_ATTEMPT_REQUESTED","REPAIR_COMPLETED"],[x.outcome for x in e.verify()])
