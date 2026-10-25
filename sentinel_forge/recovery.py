"""Conservative, authority-free recovery planning for Forge reference state."""

from __future__ import annotations
from dataclasses import dataclass,asdict
import hashlib,json
from typing import Callable
from .enrollment import EnrollmentError

FORMAT="sentinel-conservative-recovery-v1"
SAFE_AUTOMATIC_REPAIR="SAFE_AUTOMATIC_REPAIR"
RECONCILIATION_REQUIRED="RECONCILIATION_REQUIRED"
OPERATOR_REQUIRED="OPERATOR_REQUIRED"
TERMINAL="TERMINAL"
CLASSIFICATIONS=frozenset({SAFE_AUTOMATIC_REPAIR,RECONCILIATION_REQUIRED,OPERATOR_REQUIRED,TERMINAL})

# Only these authority-free local conditions are eligible for automatic repair.
SAFE_CONDITIONS=frozenset({
 "missing_derived_cache",
 "missing_local_index",
 "stale_derived_cache",
 "stale_local_index",
})
RECONCILIATION_CONDITIONS=frozenset({
 "unresolved_transition_intent",
 "ambiguous_authority_state",
 "unknown_external_effect",
 "partial_external_effect",
 "consumed_challenge_without_authority_transition",
})
OPERATOR_CONDITIONS=frozenset({
 "credential_rotation_required",
 "credential_state_mismatch",
 "audit_completion_missing",
 "development_access_present",
 "production_independence_unverified",
})
TERMINAL_CONDITIONS=frozenset({
 "revoked_relationship",
 "malformed_authority_state",
 "evidence_integrity_failure",
})

@dataclass(frozen=True)
class RecoveryObservation:
 condition:str
 target:str
 observed_identity:str
 details:str

@dataclass(frozen=True)
class RecoveryPlan:
 format:str
 classification:str
 condition:str
 target:str
 observed_identity:str
 observation_digest:str
 action:str
 plan_digest:str

def observe(*,condition:str,target:str,observed_identity:str,details:str)->RecoveryObservation:
 for name,value in (("condition",condition),("target",target),("observed_identity",observed_identity),("details",details)):
  if not isinstance(value,str) or not value.strip():raise EnrollmentError(f"recovery {name} required")
 return RecoveryObservation(condition,target,observed_identity,details)

def classify(observation:RecoveryObservation)->str:
 if not isinstance(observation,RecoveryObservation):return OPERATOR_REQUIRED
 c=observation.condition
 if not isinstance(c,str):return OPERATOR_REQUIRED
 if c in SAFE_CONDITIONS:return SAFE_AUTOMATIC_REPAIR
 if c in RECONCILIATION_CONDITIONS:return RECONCILIATION_REQUIRED
 if c in OPERATOR_CONDITIONS:return OPERATOR_REQUIRED
 if c in TERMINAL_CONDITIONS:return TERMINAL
 # Unknown recovery conditions never become permission to repair.
 return OPERATOR_REQUIRED

def build_plan(observation:RecoveryObservation)->RecoveryPlan:
 classification=classify(observation)
 od=_digest(asdict(observation))
 action={
  SAFE_AUTOMATIC_REPAIR:"REBUILD_DERIVED_LOCAL_STATE",
  RECONCILIATION_REQUIRED:"RECONCILE_EXISTING_STATE",
  OPERATOR_REQUIRED:"STOP_FOR_OPERATOR",
  TERMINAL:"NO_REPAIR_PERMITTED",
 }[classification]
 core={"format":FORMAT,"classification":classification,"condition":observation.condition,
       "target":observation.target,"observed_identity":observation.observed_identity,
       "observation_digest":od,"action":action}
 return RecoveryPlan(**core,plan_digest=_digest(core))

def verify_plan(plan:RecoveryPlan,observation:RecoveryObservation)->None:
 expected=build_plan(observation)
 if plan!=expected:raise EnrollmentError("recovery plan is stale, altered, or bound to different observed state")

def execute_safe_repair(plan:RecoveryPlan,observation:RecoveryObservation,
                        repair:Callable[[RecoveryPlan],None])->str:
 verify_plan(plan,observation)
 if plan.classification!=SAFE_AUTOMATIC_REPAIR:
  raise EnrollmentError(f"automatic repair prohibited: {plan.classification}")
 if plan.action!="REBUILD_DERIVED_LOCAL_STATE":
  raise EnrollmentError("automatic repair action is not permitted")
 repair(plan)
 return "REPAIRED"

def _digest(value)->str:
 raw=(json.dumps(value,sort_keys=True,separators=(",",":"))+"\n").encode()
 return hashlib.sha256(raw).hexdigest()

def execute_audited_safe_repair(plan:RecoveryPlan,observation:RecoveryObservation,
                                repair:Callable[[RecoveryPlan],None],evidence,
                                *,actor:str,authorization_reference:str="NOT_REQUIRED",
                                timestamp:str="UNKNOWN",time_uncertainty:str="UNKNOWN")->str:
 """Execute only a safe local repair with required before/after evidence."""
 verify_plan(plan,observation)
 if plan.classification!=SAFE_AUTOMATIC_REPAIR:
  raise EnrollmentError(f"automatic repair prohibited: {plan.classification}")
 common=dict(correlation_id=plan.plan_digest,actor=actor,target=plan.target,
  authorization_reference=authorization_reference,input_identity=plan.observed_identity,
  source_context="CONSERVATIVE_RECOVERY",collector_method="RECOVERY_EXECUTOR",
  timestamp=timestamp,time_uncertainty=time_uncertainty)
 evidence.append(**common,output_identity="NONE",outcome="REPAIR_ATTEMPT_REQUESTED",
                 reason=plan.condition)
 repair(plan)
 try:
  evidence.append(**common,output_identity=plan.plan_digest,outcome="REPAIR_COMPLETED",
                  reason=plan.action)
 except Exception as exc:
  raise EnrollmentError("repair effect occurred but completion evidence failed; reconciliation required") from exc
 return "REPAIRED"

def execute_durable_audited_safe_repair(plan:RecoveryPlan,observation:RecoveryObservation,
                                        repair:Callable[[RecoveryPlan],None],evidence,intents,
                                        *,actor:str,authorization_reference:str="NOT_REQUIRED",
                                        timestamp:str="UNKNOWN",time_uncertainty:str="UNKNOWN")->str:
 """Crash-aware safe repair: PREPARED -> APPLIED -> COMMITTED."""
 verify_plan(plan,observation)
 if plan.classification!=SAFE_AUTOMATIC_REPAIR:
  raise EnrollmentError(f"automatic repair prohibited: {plan.classification}")
 iid=intents.prepare(plan_digest=plan.plan_digest,target=plan.target,
                     observation_digest=plan.observation_digest)
 common=dict(correlation_id=plan.plan_digest,actor=actor,target=plan.target,
  authorization_reference=authorization_reference,input_identity=plan.observed_identity,
  source_context="CONSERVATIVE_RECOVERY",collector_method="DURABLE_RECOVERY_EXECUTOR",
  timestamp=timestamp,time_uncertainty=time_uncertainty)
 try:
  evidence.append(**common,output_identity="NONE",outcome="REPAIR_ATTEMPT_REQUESTED",
                  reason=plan.condition)
 except Exception:
  intents.abort(plan.plan_digest,iid)
  raise
 try:
  repair(plan)
 except Exception:
  intents.abort(plan.plan_digest,iid)
  raise
 intents.mark_applied(plan.plan_digest,iid)
 try:
  evidence.append(**common,output_identity=plan.plan_digest,outcome="REPAIR_COMPLETED",
                  reason=plan.action)
 except Exception as exc:
  raise EnrollmentError("repair applied but completion evidence failed; recovery reconciliation required") from exc
 intents.commit(plan.plan_digest,iid)
 return "REPAIRED"
