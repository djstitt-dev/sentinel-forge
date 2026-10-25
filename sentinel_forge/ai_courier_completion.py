"""Completion assessment for standalone AI and child Courier phase."""
from dataclasses import dataclass,asdict
import json
from .enrollment import EnrollmentError
AI_ENGINE=("COMMAND_ENGINE","TOOL_AUTHORITY","LOCAL_MODEL_ADAPTER","INTERACTIVE_CONSOLE","AI_TESTS")
CHILD_ENGINE=("TARGET_BOOTSTRAP","SSH_PLAN","SSH_EXECUTION_GATE","AUTH_CALLBACK","AES256_GCM","VISUAL_STATUS","CHILD_TESTS")
@dataclass(frozen=True)
class PhaseCompletion:
 ai_engine_complete:bool;local_model_operational:bool;child_engine_complete:bool;live_child_operational:bool
 blockers:tuple[str,...]
 def to_json(self):return json.dumps(asdict(self),sort_keys=True,separators=(",",":"))+"\n"
def _check(names,f):
 if set(f)!=set(names) or any(type(v) is not bool for v in f.values()):raise EnrollmentError("phase completion facts invalid")
 return [x for x in names if not f[x]]
def assess(*,ai_facts,child_facts,local_model_operational,live_child_operational):
 if type(local_model_operational) is not bool or type(live_child_operational) is not bool:raise EnrollmentError("operational facts must be boolean")
 a=_check(AI_ENGINE,ai_facts);c=_check(CHILD_ENGINE,child_facts);b=[f"AI_INCOMPLETE:{x}" for x in a]+[f"CHILD_INCOMPLETE:{x}" for x in c]
 if not local_model_operational:b.append("LOCAL_MODEL_NOT_OPERATIONAL")
 if not live_child_operational:b.append("LIVE_CHILD_NOT_OPERATIONAL")
 return PhaseCompletion(not a,local_model_operational,not c,live_child_operational,tuple(b))
