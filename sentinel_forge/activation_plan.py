"""Pure planning for controlled Courier activation and shutdown."""
from dataclasses import dataclass
from .enrollment import EnrollmentError

@dataclass(frozen=True)
class ActivationStep:
 order:int
 action:str
 requires_operator_approval:bool

ACTIVATION_ACTIONS=(
 "VERIFY_ASSISTANT_INDEPENDENCE","VERIFY_RELATIONSHIP_ACTIVE","VERIFY_NOT_REVOKED",
 "VERIFY_CURRENT_CREDENTIAL","VERIFY_CURRENT_SESSION","VERIFY_COMPATIBILITY",
 "VERIFY_PROTECTION_PROVIDER","VERIFY_NETWORK_PROVIDER","VERIFY_AUDIT",
 "VERIFY_NO_UNRESOLVED_EFFECTS","OPERATOR_APPROVAL","ENABLE_TRANSPORT",
)
SHUTDOWN_ACTIONS=("BLOCK_NEW_PREPARATION","BLOCK_NEW_EFFECTS","PRESERVE_IN_FLIGHT_STATE","FLUSH_AUDIT","DISABLE_TRANSPORT","VERIFY_DISABLED")

def activation_plan()->tuple[ActivationStep,...]:
 return tuple(ActivationStep(i+1,a,a in {"OPERATOR_APPROVAL","ENABLE_TRANSPORT"}) for i,a in enumerate(ACTIVATION_ACTIONS))
def shutdown_plan()->tuple[ActivationStep,...]:
 return tuple(ActivationStep(i+1,a,a=="DISABLE_TRANSPORT") for i,a in enumerate(SHUTDOWN_ACTIONS))
def require_activation_order(actions)->None:
 if tuple(actions)!=ACTIVATION_ACTIONS:raise EnrollmentError("Courier activation order invalid")
