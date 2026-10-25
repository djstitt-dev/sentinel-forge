"""Consolidated Forge Courier readiness report."""
from dataclasses import dataclass,asdict
import json

@dataclass(frozen=True)
class ReadinessReport:
 offline_ready:bool
 production_ready:bool
 blockers:tuple[str,...]
 observations:tuple[str,...]
 def to_json(self):return json.dumps(asdict(self),sort_keys=True,separators=(",",":"))+"\n"

def build_readiness_report(*,acceptance,health,compatibility_valid:bool,configuration_valid:bool,
                           activation_plan_valid:bool,backup_contract_valid:bool,telemetry_contract_valid:bool)->ReadinessReport:
 blockers=list(acceptance.blockers)
 if not compatibility_valid:blockers.append("COMPATIBILITY_POLICY_INVALID")
 if not configuration_valid:blockers.append("PRODUCTION_CONFIGURATION_INVALID")
 if not activation_plan_valid:blockers.append("ACTIVATION_PLAN_INVALID")
 if not backup_contract_valid:blockers.append("BACKUP_CONTRACT_INVALID")
 if not telemetry_contract_valid:blockers.append("TELEMETRY_CONTRACT_INVALID")
 if health.status!="HEALTHY":blockers.append("TRANSPORT_HEALTH_"+health.status)
 observations=("OFFLINE_INVARIANTS_"+("PASS" if acceptance.offline_invariants_passed else "FAIL"),
               "TRANSPORT_HEALTH_"+health.status)
 offline=acceptance.offline_invariants_passed and compatibility_valid and configuration_valid and activation_plan_valid and backup_contract_valid and telemetry_contract_valid
 return ReadinessReport(offline,offline and acceptance.production_ready and health.status=="HEALTHY" and not blockers,tuple(dict.fromkeys(blockers)),observations)
