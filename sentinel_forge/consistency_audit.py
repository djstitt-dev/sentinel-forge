"""Read-only cross-authority consistency audit for one Courier relationship."""
from __future__ import annotations
from dataclasses import dataclass
from .enrollment import EnrollmentError
from .credential_session import require_registry_current_credential_session
from .session import require_session

@dataclass(frozen=True)
class ConsistencyAudit:
 relationship_id:str
 enrollment_state:str|None
 revoked:bool
 credential_generation:int
 session_generation:int
 send_highest:int
 receive_highest:int
 pending_queue_items:int
 consistent:bool
 blockers:tuple[str,...]

def audit_relationship(*,bundle,domain,session,binding,credential,credential_registry,enrollment_registry,
                       revocation_registry,send_registry,replay_registry,queue)->ConsistencyAudit:
 blockers=[]
 try:
  require_session(session,domain)
 except EnrollmentError:blockers.append("SESSION_DOMAIN_MISMATCH")
 try:
  require_registry_current_credential_session(binding,session,domain,credential,credential_registry)
 except EnrollmentError:blockers.append("CREDENTIAL_SESSION_MISMATCH")
 if bundle.enrollment_id!=domain.enrollment_id or bundle.remote_identity!=domain.peer_identity:
  blockers.append("ENROLLMENT_DOMAIN_MISMATCH")
 state=enrollment_registry.state(bundle.enrollment_id)
 revoked=revocation_registry.is_revoked(bundle.enrollment_id)
 if revoked:blockers.append("RELATIONSHIP_REVOKED")
 if state is None:blockers.append("ENROLLMENT_UNKNOWN")
 ss=send_registry.state(domain.relationship_id)
 rs=replay_registry.state(domain.relationship_id)
 if ss is not None and (ss["generation"]!=session.generation or ss["session_id"]!=session.session_id):
  blockers.append("SEND_SESSION_DISAGREEMENT")
 if rs is not None and (rs["generation"]!=session.generation or rs["session_id"]!=session.session_id):
  blockers.append("RECEIVE_SESSION_DISAGREEMENT")
 pending=queue.pending(domain.relationship_id)
 for r in pending:
  if r["relationship_id"]!=domain.relationship_id: blockers.append("QUEUE_RELATIONSHIP_DISAGREEMENT")
 return ConsistencyAudit(domain.relationship_id,state,revoked,credential.generation,session.generation,
  0 if ss is None else ss["highest"],0 if rs is None else rs["highest"],len(pending),not blockers,tuple(blockers))
