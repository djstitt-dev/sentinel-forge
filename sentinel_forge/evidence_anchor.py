"""Local evidence-head checkpoint contract for future independent anchoring."""
from dataclasses import dataclass
import hashlib,json
from .evidence import EvidenceJournal,EvidenceError,GENESIS
@dataclass(frozen=True)
class EvidenceHead:
 journal_identity:str
 sequence:int
 event_hash:str
 checkpoint_digest:str
def build_evidence_head(journal:EvidenceJournal,*,journal_identity:str)->EvidenceHead:
 if not isinstance(journal_identity,str) or not journal_identity.strip():raise EvidenceError("journal identity required")
 events=journal.verify();seq=len(events);head=events[-1].event_hash if events else GENESIS
 core={"journal_identity":journal_identity,"sequence":seq,"event_hash":head};return EvidenceHead(journal_identity,seq,head,_sha(core))
def verify_against_head(journal:EvidenceJournal,head:EvidenceHead)->None:
 if not isinstance(head,EvidenceHead):raise EvidenceError("evidence checkpoint contract required")
 if not isinstance(head.journal_identity,str) or not head.journal_identity.strip():raise EvidenceError("evidence checkpoint identity invalid")
 if not isinstance(head.sequence,int) or isinstance(head.sequence,bool) or head.sequence<0:raise EvidenceError("evidence checkpoint sequence invalid")
 for value in (head.event_hash,head.checkpoint_digest):
  if not isinstance(value,str) or not value.strip():raise EvidenceError("evidence checkpoint digest invalid")
 core={"journal_identity":head.journal_identity,"sequence":head.sequence,"event_hash":head.event_hash}
 if head.checkpoint_digest!=_sha(core):raise EvidenceError("evidence checkpoint integrity failure")
 events=journal.verify()
 if len(events)<head.sequence:raise EvidenceError("evidence journal rollback detected")
 if head.sequence and events[head.sequence-1].event_hash!=head.event_hash:raise EvidenceError("evidence journal diverged from checkpoint")
 if head.sequence==0 and head.event_hash!=GENESIS:raise EvidenceError("evidence checkpoint genesis mismatch")
def _sha(v):return hashlib.sha256((json.dumps(v,sort_keys=True,separators=(",",":"))+"\n").encode()).hexdigest()
