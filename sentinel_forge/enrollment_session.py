"""Forge-local one-time challenge lifecycle for enrollment verification."""

from __future__ import annotations
from .secure_io import private_open
import fcntl,json,os
from pathlib import Path
from .enrollment import EnrollmentBundle, EnrollmentError
from .enrollment_proof import EnrollmentChallenge, AuthenticatedEnrollmentProof, verify_authenticated_proof
from .authenticity import Verifier

class ChallengeRegistry:
    def __init__(self,path:Path):
        self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True)
        with self._lock(exclusive=True):
            if not self.path.exists():self._save({})
            else:self._load()
    def issue(self,bundle:EnrollmentBundle,challenge:EnrollmentChallenge):
        with self._lock(exclusive=True):
            db=self._load()
            if challenge.enrollment_id!=bundle.enrollment_id:raise EnrollmentError("challenge enrollment mismatch")
            prior=db.get(bundle.enrollment_id)
            if prior and prior["state"]=="OUTSTANDING":raise EnrollmentError("outstanding challenge already exists")
            db[bundle.enrollment_id]={"state":"OUTSTANDING","challenge_id":challenge.challenge_id,
                                      "remote_identity":bundle.remote_identity}
            self._save(db)
    def verify_and_consume(self,bundle:EnrollmentBundle,proof:AuthenticatedEnrollmentProof,
                           verifier:Verifier,*,expected_remote_key_reference:str)->bool:
        with self._lock(exclusive=True):
            db=self._load(); rec=db.get(bundle.enrollment_id)
            if rec is None or rec["state"]!="OUTSTANDING":raise EnrollmentError("no outstanding challenge")
            if rec["remote_identity"]!=bundle.remote_identity:raise EnrollmentError("remote identity mismatch")
            ok=verify_authenticated_proof(bundle,proof,verifier,
                 expected_remote_key_reference=expected_remote_key_reference,
                 expected_challenge_id=rec["challenge_id"])
            if not ok:raise EnrollmentError("authenticated proof verification failed")
            rec["state"]="CONSUMED";self._save(db);return True
    def state(self,enrollment_id):
        with self._lock(exclusive=False):
            r=self._load().get(enrollment_id);return None if r is None else r["state"]
    def _lock(self,*,exclusive:bool):
        return _ChallengeFileLock(self.path.with_suffix(self.path.suffix+".lock"),exclusive)
    def _load(self):
        try:v=json.loads(self.path.read_text())
        except (OSError,json.JSONDecodeError) as exc:raise EnrollmentError("malformed challenge registry") from exc
        if not isinstance(v,dict):raise EnrollmentError("malformed challenge registry")
        for eid,r in v.items():
            if not isinstance(eid,str) or not eid.strip() or not isinstance(r,dict) or set(r)!={"state","challenge_id","remote_identity"}:
                raise EnrollmentError("malformed challenge registry")
            if r["state"] not in {"OUTSTANDING","CONSUMED"}:
                raise EnrollmentError("malformed challenge registry")
            if any(not isinstance(r[x],str) or not r[x].strip() for x in ("challenge_id","remote_identity")):
                raise EnrollmentError("malformed challenge registry")
        return v
    def _save(self,v):
        tmp=self.path.with_suffix(self.path.suffix+".tmp")
        payload=(json.dumps(v,sort_keys=True,separators=(",",":"))+"\n").encode()
        with private_open(tmp,"wb") as f:
            f.write(payload);f.flush();os.fsync(f.fileno())
        tmp.replace(self.path)
        dfd=os.open(self.path.parent,os.O_RDONLY)
        try:os.fsync(dfd)
        finally:os.close(dfd)


class _ChallengeFileLock:
    def __init__(self,path:Path,exclusive:bool):
        self.path=Path(path);self.exclusive=exclusive;self.fd=None
    def __enter__(self):
        try:
            self.fd=os.open(self.path,os.O_RDWR|os.O_CREAT,0o600)
            fcntl.flock(self.fd,fcntl.LOCK_EX if self.exclusive else fcntl.LOCK_SH)
        except OSError as exc:
            if self.fd is not None:os.close(self.fd);self.fd=None
            raise EnrollmentError("challenge registry lock unavailable") from exc
        return self
    def __exit__(self,exc_type,exc,tb):
        try:
            if self.fd is not None:fcntl.flock(self.fd,fcntl.LOCK_UN)
        finally:
            if self.fd is not None:os.close(self.fd);self.fd=None
