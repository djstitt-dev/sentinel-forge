"""Terminal enrollment revocation and retirement semantics."""

from __future__ import annotations
from .secure_io import private_open
from dataclasses import dataclass,asdict
import fcntl,hashlib,json,os
from pathlib import Path
from .enrollment import EnrollmentError

FORMAT="sentinel-courier-revocation-v1"

@dataclass(frozen=True)
class RevocationRecord:
    format:str
    enrollment_id:str
    remote_identity:str
    operator_authorization_reference:str
    reason:str
    prior_state:str
    terminal_state:str
    record_digest:str
    def as_dict(self):return asdict(self)

def make_revocation(*,enrollment_id:str,remote_identity:str,
                    operator_authorization_reference:str,reason:str,prior_state:str)->RevocationRecord:
    values=(enrollment_id,remote_identity,operator_authorization_reference,reason,prior_state)
    if any(not isinstance(v,str) or not v.strip() for v in values):
        raise EnrollmentError("revocation fields must be explicit")
    if prior_state=="REVOKED":raise EnrollmentError("enrollment already revoked")
    core={"format":FORMAT,"enrollment_id":enrollment_id,"remote_identity":remote_identity,
          "operator_authorization_reference":operator_authorization_reference,
          "reason":reason,"prior_state":prior_state,"terminal_state":"REVOKED"}
    digest="sha256:"+hashlib.sha256(_canonical(core)).hexdigest()
    return RevocationRecord(**core,record_digest=digest)

def verify_revocation(r:RevocationRecord)->bool:
    try:
        expected=make_revocation(enrollment_id=r.enrollment_id,remote_identity=r.remote_identity,
          operator_authorization_reference=r.operator_authorization_reference,reason=r.reason,
          prior_state=r.prior_state)
    except EnrollmentError:return False
    return expected==r

class RevocationRegistry:
    def __init__(self,path:Path):
        self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
        with self._lock(exclusive=True):
            if not self.path.exists():self._save({})
            else:self._load()
    def revoke(self,record:RevocationRecord):
        if not verify_revocation(record):raise EnrollmentError("invalid revocation record")
        with self._lock(exclusive=True):
            db=self._load();prior=db.get(record.enrollment_id)
            if prior is not None:
                if prior==record.as_dict():return
                raise EnrollmentError("conflicting revocation for enrollment")
            db[record.enrollment_id]=record.as_dict();self._save(db)
    def is_revoked(self,enrollment_id:str)->bool:
        with self._lock(exclusive=False):return enrollment_id in self._load()
    def require_not_revoked(self,enrollment_id:str):
        if self.is_revoked(enrollment_id):raise EnrollmentError("enrollment is terminally revoked")
    def get(self,enrollment_id:str):
        with self._lock(exclusive=False):return self._load().get(enrollment_id)
    def _lock(self,*,exclusive:bool):
        return _RevocationFileLock(self.path.with_suffix(self.path.suffix+".lock"),exclusive)
    def _load(self):
        try:v=json.loads(self.path.read_text())
        except (OSError,json.JSONDecodeError) as exc:raise EnrollmentError("malformed revocation registry") from exc
        if not isinstance(v,dict):raise EnrollmentError("malformed revocation registry")
        required={"format","enrollment_id","remote_identity","operator_authorization_reference","reason","prior_state","terminal_state","record_digest"}
        for eid,raw in v.items():
            if not isinstance(eid,str) or not eid.strip() or not isinstance(raw,dict) or set(raw)!=required:
                raise EnrollmentError("malformed revocation registry record")
            try:r=RevocationRecord(**raw)
            except TypeError as exc:raise EnrollmentError("malformed revocation registry record") from exc
            if r.enrollment_id!=eid or not verify_revocation(r):
                raise EnrollmentError("invalid durable revocation record")
        return v
    def _save(self,v):
        t=self.path.with_suffix(self.path.suffix+".tmp")
        with private_open(t,"wb") as f:
            f.write(_canonical(v));f.flush();os.fsync(f.fileno())
        t.replace(self.path)
        dfd=os.open(self.path.parent,os.O_RDONLY)
        try:os.fsync(dfd)
        finally:os.close(dfd)


class _RevocationFileLock:
    def __init__(self,path:Path,exclusive:bool):
        self.path=Path(path);self.exclusive=exclusive;self.fd=None
    def __enter__(self):
        try:
            self.fd=os.open(self.path,os.O_RDWR|os.O_CREAT,0o600)
            fcntl.flock(self.fd,fcntl.LOCK_EX if self.exclusive else fcntl.LOCK_SH)
        except OSError as exc:
            if self.fd is not None:os.close(self.fd);self.fd=None
            raise EnrollmentError("revocation registry lock unavailable") from exc
        return self
    def __exit__(self,exc_type,exc,tb):
        try:
            if self.fd is not None:fcntl.flock(self.fd,fcntl.LOCK_UN)
        finally:
            if self.fd is not None:os.close(self.fd);self.fd=None

def _canonical(v):return (json.dumps(v,sort_keys=True,separators=(",",":"))+"\n").encode()
