"""Evidence-derived Forge-side Courier implementation completion runner."""
from __future__ import annotations
import importlib.util,json
from .acceptance_runner import run_invariant_checks
from .courier_completion import IMPLEMENTATION_GATES,ACTIVATION_GATES,OPERATIONAL_GATES,assess_completion

MODULES={
 "FRAMING_IMPLEMENTED":("sentinel_forge.framing","sentinel_forge.protected_wire"),
 "PROTECTION_BOUNDARY_IMPLEMENTED":("sentinel_forge.protection_provider","sentinel_forge.protected_receive"),
 "ENROLLMENT_IMPLEMENTED":("sentinel_forge.enrollment","sentinel_forge.enrollment_artifact_v2","sentinel_forge.audited_enrollment"),
 "PAIRWISE_TRUST_IMPLEMENTED":("sentinel_forge.trust_domain",),
 "CREDENTIAL_AUTHORITY_IMPLEMENTED":("sentinel_forge.credential_registry","sentinel_forge.credential_session"),
 "SESSION_REPLAY_IMPLEMENTED":("sentinel_forge.session","sentinel_forge.send_sequence"),
 "DELIVERY_INTENT_IMPLEMENTED":("sentinel_forge.delivery_intent",),
 "DURABLE_QUEUE_IMPLEMENTED":("sentinel_forge.courier_queue_v2",),
 "ACK_RECONCILIATION_IMPLEMENTED":("sentinel_forge.courier_ack","sentinel_forge.courier_reconcile"),
 "REVOCATION_ROTATION_IMPLEMENTED":("sentinel_forge.revocation","sentinel_forge.credential_reference","sentinel_forge.credential_registry","sentinel_forge.session"),
 "AUDIT_EVIDENCE_IMPLEMENTED":("sentinel_forge.evidence","sentinel_forge.evidence_anchor","sentinel_forge.courier_audit"),
 "RECOVERY_IMPLEMENTED":("sentinel_forge.recovery","sentinel_forge.recovery_intent","sentinel_forge.courier_recovery"),
 "BACKUP_RESTORE_CONTRACT_IMPLEMENTED":("sentinel_forge.state_backup","sentinel_forge.backup_contract"),
 "CROSS_AUTHORITY_AUDIT_IMPLEMENTED":("sentinel_forge.consistency_audit","sentinel_forge.delivery_consistency"),
 "READINESS_FAIL_CLOSED":("sentinel_forge.transport_readiness","sentinel_forge.courier_acceptance","sentinel_forge.readiness_report"),
}

def _present(name):return importlib.util.find_spec(name) is not None

def derive_implementation_facts(*,full_regression_passed:bool):
 facts={k:all(_present(m) for m in mods) for k,mods in MODULES.items()}
 inv=run_invariant_checks()
 facts["READINESS_FAIL_CLOSED"]=facts["READINESS_FAIL_CLOSED"] and all(inv.values())
 facts["FULL_REGRESSION_PASS"]=full_regression_passed is True
 if set(facts)!=set(IMPLEMENTATION_GATES):raise RuntimeError("implementation gate definition drift")
 return facts

def current_report(*,full_regression_passed:bool=False):
 implementation=derive_implementation_facts(full_regression_passed=full_regression_passed)
 # These are deliberately false until separately authorized production evidence exists.
 activation={x:False for x in ACTIVATION_GATES}
 operational={x:False for x in OPERATIONAL_GATES}
 return assess_completion(implementation_facts=implementation,activation_facts=activation,operational_facts=operational)

if __name__=="__main__":
 print(current_report().to_json(),end="")
