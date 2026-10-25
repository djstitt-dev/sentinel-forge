"""Append-only local evidence journal with integrity chaining.

This repository reference journal is authority-free: successful recording never
implies authorization, transfer, release, deployment, or Scribe acceptance.
"""

from __future__ import annotations
from .secure_io import private_open
from dataclasses import dataclass, asdict
import fcntl, hashlib, json, os
from pathlib import Path
from typing import Any

GENESIS="0"*64
REDACTED="[REDACTED]"
UNKNOWN="UNKNOWN"
SENSITIVE_KEYS=frozenset({"secret","password","token","credential","private_key","api_key"})

class EvidenceError(RuntimeError): pass

@dataclass(frozen=True)
class EvidenceEvent:
    sequence: int
    correlation_id: str
    actor: str
    target: str
    authorization_reference: str
    input_identity: str
    output_identity: str
    outcome: str
    reason: str
    source_context: str
    collector_method: str
    timestamp: str
    time_uncertainty: str
    previous_hash: str
    event_hash: str

class EvidenceJournal:
    def __init__(self,path:Path):
        self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True)

    def append(self, **fields: Any) -> EvidenceEvent:
        forbidden=SENSITIVE_KEYS & set(fields)
        if forbidden: raise EvidenceError("sensitive field names are prohibited from evidence")
        with self._lock(exclusive=True):
            prior=self.verify()
            seq=len(prior)+1
            prev=prior[-1].event_hash if prior else GENESIS
            body={
                "sequence":seq,
                "correlation_id":_v(fields.get("correlation_id")),
                "actor":_v(fields.get("actor")),
                "target":_v(fields.get("target")),
                "authorization_reference":_v(fields.get("authorization_reference")),
                "input_identity":_v(fields.get("input_identity")),
                "output_identity":_v(fields.get("output_identity")),
                "outcome":_v(fields.get("outcome")),
                "reason":_v(fields.get("reason")),
                "source_context":_v(fields.get("source_context")),
                "collector_method":_v(fields.get("collector_method")),
                "timestamp":_v(fields.get("timestamp")),
                "time_uncertainty":_v(fields.get("time_uncertainty")),
                "previous_hash":prev,
            }
            digest=_hash(body)
            event=EvidenceEvent(**body,event_hash=digest)
            encoded=json.dumps(asdict(event),sort_keys=True,separators=(",",":"))+"\n"
            with private_open(self.path,"a",encoding="utf-8") as fh:
                fh.write(encoded); fh.flush(); os.fsync(fh.fileno())
            return event

    def _lock(self,*,exclusive:bool):
        return _EvidenceJournalLock(self.path.with_suffix(self.path.suffix+".lock"),exclusive)

    def verify(self) -> list[EvidenceEvent]:
        if not self.path.exists(): return []
        events=[]; prev=GENESIS
        try:
            lines=self.path.read_text(encoding="utf-8").splitlines()
        except OSError as exc: raise EvidenceError("cannot read evidence journal") from exc
        for expected,line in enumerate(lines,1):
            try: raw=json.loads(line)
            except json.JSONDecodeError as exc: raise EvidenceError("malformed evidence record") from exc
            try: event=EvidenceEvent(**raw)
            except TypeError as exc: raise EvidenceError("invalid evidence schema") from exc
            if event.sequence != expected: raise EvidenceError("evidence sequence discontinuity")
            if event.previous_hash != prev: raise EvidenceError("evidence chain discontinuity")
            body=asdict(event); supplied=body.pop("event_hash")
            if _hash(body) != supplied: raise EvidenceError("evidence record integrity failure")
            events.append(event); prev=supplied
        return events


class _EvidenceJournalLock:
    def __init__(self,path:Path,exclusive:bool):
        self.path=Path(path);self.exclusive=exclusive;self.fd=None
    def __enter__(self):
        try:
            self.fd=os.open(self.path,os.O_RDWR|os.O_CREAT,0o600)
            fcntl.flock(self.fd,fcntl.LOCK_EX if self.exclusive else fcntl.LOCK_SH)
        except OSError as exc:
            if self.fd is not None:os.close(self.fd);self.fd=None
            raise EvidenceError("evidence journal lock unavailable") from exc
        return self
    def __exit__(self,exc_type,exc,tb):
        try:
            if self.fd is not None:fcntl.flock(self.fd,fcntl.LOCK_UN)
        finally:
            if self.fd is not None:os.close(self.fd);self.fd=None

def _v(value:Any)->str:
    if value is None or value=="": return UNKNOWN
    if not isinstance(value,(str,int,float,bool)): raise EvidenceError("evidence values must be scalar")
    text=str(value)
    lowered=text.lower()
    if any(marker in lowered for marker in ("-----begin private key-----","bearer ","password=","token=")):
        return REDACTED
    return text

def _hash(body:dict[str,Any])->str:
    raw=(json.dumps(body,sort_keys=True,separators=(",",":"))+"\n").encode()
    return hashlib.sha256(raw).hexdigest()
