"""Offline Courier Enrollment Protocol v1 reference implementation.

Forge provisions a host-bound enrollment bundle. A remote-side installer consumes
that bundle against an explicitly supplied filesystem root and emits proof.
No network, service activation, credential generation, or remote execution exists.
"""

from __future__ import annotations
from .secure_io import private_open

from dataclasses import dataclass, asdict
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
from typing import Any

PROTOCOL="sentinel-courier-enrollment-v1"
STATES=("STAGED","REMOTE_AUTHENTICATED","INSTALLED","VERIFIED","ACTIVE")
GENESIS="0"*64

class EnrollmentError(RuntimeError): pass

@dataclass(frozen=True)
class EnrollmentBundle:
    protocol: str
    enrollment_id: str
    forge_identity: str
    remote_identity: str
    remote_role: str
    permitted_actions: tuple[str,...]
    permitted_target: str
    policy_reference: str
    one_time: bool
    payload_digest: str

    def as_dict(self)->dict[str,Any]:
        d=asdict(self); d["permitted_actions"]=list(self.permitted_actions); return d

@dataclass(frozen=True)
class EnrollmentProof:
    protocol: str
    enrollment_id: str
    forge_identity: str
    remote_identity: str
    remote_role: str
    installed_bundle_digest: str
    installed_policy_digest: str
    installer_outcome: str

    def as_dict(self)->dict[str,Any]: return asdict(self)

def build_bundle(*, forge_identity:str, remote_identity:str, remote_role:str,
                 permitted_actions:list[str]|tuple[str,...], permitted_target:str,
                 policy_reference:str)->EnrollmentBundle:
    fields=[forge_identity,remote_identity,remote_role,permitted_target,policy_reference]
    if any(not isinstance(x,str) or not x.strip() for x in fields):
        raise EnrollmentError("all enrollment identity/policy fields are required")
    actions=tuple(sorted(set(permitted_actions)))
    if not actions or any(not isinstance(x,str) or not x.strip() for x in actions):
        raise EnrollmentError("at least one explicit permitted action is required")
    core={"protocol":PROTOCOL,"forge_identity":forge_identity,"remote_identity":remote_identity,
          "remote_role":remote_role,"permitted_actions":list(actions),
          "permitted_target":permitted_target,"policy_reference":policy_reference,"one_time":True}
    enrollment_id="enroll:"+_sha(core)
    digest="sha256:"+_sha({**core,"enrollment_id":enrollment_id})
    return EnrollmentBundle(PROTOCOL,enrollment_id,forge_identity,remote_identity,remote_role,
                            actions,permitted_target,policy_reference,True,digest)

def verify_bundle(bundle:EnrollmentBundle)->bool:
    rebuilt=build_bundle(forge_identity=bundle.forge_identity,remote_identity=bundle.remote_identity,
        remote_role=bundle.remote_role,permitted_actions=bundle.permitted_actions,
        permitted_target=bundle.permitted_target,policy_reference=bundle.policy_reference)
    return rebuilt==bundle

def install_bundle(bundle:EnrollmentBundle, *, expected_remote_identity:str,
                   root:Path)->EnrollmentProof:
    if not verify_bundle(bundle): raise EnrollmentError("bundle integrity/identity validation failed")
    if bundle.remote_identity != expected_remote_identity:
        raise EnrollmentError("bundle is bound to a different remote identity")
    root=Path(root).resolve(strict=True)
    if not root.is_dir(): raise EnrollmentError("installation root must be a directory")
    parent=root/"var"/"lib"/"sentinel-courier"/"enrollments"
    parent.mkdir(parents=True,exist_ok=True)
    name=_safe(bundle.enrollment_id)
    base=parent/name
    staging=parent/(name+".staging")
    if base.exists(): raise EnrollmentError("one-time enrollment bundle already consumed")
    if staging.exists(): raise EnrollmentError("incomplete prior enrollment installation requires reconciliation")
    staging.mkdir(exist_ok=False)
    policy={"protocol":bundle.protocol,"enrollment_id":bundle.enrollment_id,
            "forge_identity":bundle.forge_identity,"remote_identity":bundle.remote_identity,
            "remote_role":bundle.remote_role,"permitted_actions":list(bundle.permitted_actions),
            "permitted_target":bundle.permitted_target,"policy_reference":bundle.policy_reference}
    policy_raw=_canonical(policy)
    with private_open(staging/"policy.json","wb") as f: f.write(policy_raw)
    marker_data={"enrollment_id":bundle.enrollment_id,"bundle_digest":bundle.payload_digest,
                 "remote_identity":bundle.remote_identity,"state":"INSTALLED"}
    with private_open(staging/"consumed.json","wb") as f: f.write(_canonical(marker_data))
    staging.replace(base)
    return EnrollmentProof(PROTOCOL,bundle.enrollment_id,bundle.forge_identity,
        bundle.remote_identity,bundle.remote_role,bundle.payload_digest,
        "sha256:"+hashlib.sha256(policy_raw).hexdigest(),"INSTALLED")

def verify_proof(bundle:EnrollmentBundle, proof:EnrollmentProof)->bool:
    if not verify_bundle(bundle): return False
    return (
        proof.protocol==PROTOCOL and proof.enrollment_id==bundle.enrollment_id
        and proof.forge_identity==bundle.forge_identity
        and proof.remote_identity==bundle.remote_identity
        and proof.remote_role==bundle.remote_role
        and proof.installed_bundle_digest==bundle.payload_digest
        and proof.installer_outcome=="INSTALLED"
        and proof.installed_policy_digest.startswith("sha256:")
        and len(proof.installed_policy_digest)==71
    )

class EnrollmentRegistry:
    """Forge-local lifecycle registry. ACTIVE requires explicit operator activation."""
    def __init__(self,path:Path):
        self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True)
        with self._lock(exclusive=True):
            if not self.path.exists(): self._save({})
            else:self._load()

    def stage(self,bundle:EnrollmentBundle):
        if not verify_bundle(bundle): raise EnrollmentError("cannot stage invalid bundle")
        with self._lock(exclusive=True):
            db=self._load()
            if bundle.enrollment_id in db: raise EnrollmentError("enrollment already registered")
            db[bundle.enrollment_id]={"state":"STAGED","bundle_digest":bundle.payload_digest,
                                      "remote_identity":bundle.remote_identity}
            self._save(db)

    def _mark_remote_authenticated(self,enrollment_id:str,*,capability:object,expected_capability:object):
        if capability is not expected_capability: raise EnrollmentError("remote-authentication capability required")
        with self._lock(exclusive=True):
            db=self._load();rec=db.get(enrollment_id)
            if rec is None or rec["state"]!="STAGED": raise EnrollmentError("remote authentication requires STAGED enrollment")
            rec["state"]="REMOTE_AUTHENTICATED";self._save(db)

    def accept_proof(self,bundle:EnrollmentBundle,proof:EnrollmentProof):
        if not verify_proof(bundle,proof): raise EnrollmentError("remote enrollment proof invalid")
        with self._lock(exclusive=True):
            db=self._load(); rec=db.get(bundle.enrollment_id)
            if rec is None or rec["state"]!="REMOTE_AUTHENTICATED":
                raise EnrollmentError("installation proof requires authenticated remote")
            if rec["bundle_digest"]!=bundle.payload_digest: raise EnrollmentError("staged bundle digest mismatch")
            rec["state"]="VERIFIED"; rec["proof_digest"]="sha256:"+_sha(proof.as_dict()); self._save(db)

    def _transition_verified_to_active(self,enrollment_id:str,*,capability:object,expected_capability:object):
        if capability is not expected_capability:
            raise EnrollmentError("activation capability required")
        with self._lock(exclusive=True):
            db=self._load(); rec=db.get(enrollment_id)
            if rec is None or rec["state"]!="VERIFIED":
                raise EnrollmentError("only VERIFIED enrollment may activate")
            rec["state"]="ACTIVE"; self._save(db)

    def state(self,enrollment_id:str)->str|None:
        with self._lock(exclusive=False):
            rec=self._load().get(enrollment_id); return None if rec is None else rec["state"]

    def _lock(self,*,exclusive:bool):
        return _EnrollmentFileLock(self.path.with_suffix(self.path.suffix+".lock"),exclusive)

    def _load(self):
        try: value=json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError,json.JSONDecodeError) as exc: raise EnrollmentError("malformed enrollment registry") from exc
        if not isinstance(value,dict): raise EnrollmentError("malformed enrollment registry")
        for eid,rec in value.items():
            if not isinstance(eid,str) or not eid.strip() or not isinstance(rec,dict):
                raise EnrollmentError("malformed enrollment registry")
            state=rec.get("state")
            if not isinstance(state,str) or state not in {"STAGED","REMOTE_AUTHENTICATED","VERIFIED","ACTIVE"}:
                raise EnrollmentError("malformed enrollment registry")
            required={"state","bundle_digest","remote_identity"}|({"proof_digest"} if state in {"VERIFIED","ACTIVE"} else set())
            if set(rec)!=required:
                raise EnrollmentError("malformed enrollment registry")
            for name in required-{"state"}:
                if not isinstance(rec[name],str) or not rec[name].strip():
                    raise EnrollmentError("malformed enrollment registry")
        return value
    def _save(self,value):
        tmp=self.path.with_suffix(self.path.suffix+".tmp")
        with private_open(tmp,"wb") as f:
            f.write(_canonical(value));f.flush();os.fsync(f.fileno())
        tmp.replace(self.path)
        dfd=os.open(self.path.parent,os.O_RDONLY)
        try:os.fsync(dfd)
        finally:os.close(dfd)


class _EnrollmentFileLock:
    def __init__(self,path:Path,exclusive:bool):
        self.path=Path(path);self.exclusive=exclusive;self.fd=None
    def __enter__(self):
        try:
            self.fd=os.open(self.path,os.O_RDWR|os.O_CREAT,0o600)
            fcntl.flock(self.fd,fcntl.LOCK_EX if self.exclusive else fcntl.LOCK_SH)
        except OSError as exc:
            if self.fd is not None:os.close(self.fd);self.fd=None
            raise EnrollmentError("enrollment registry lock unavailable") from exc
        return self
    def __exit__(self,exc_type,exc,tb):
        try:
            if self.fd is not None:fcntl.flock(self.fd,fcntl.LOCK_UN)
        finally:
            if self.fd is not None:os.close(self.fd);self.fd=None

def _safe(value:str)->str:
    return hashlib.sha256(value.encode()).hexdigest()

def _canonical(value:Any)->bytes:
    return (json.dumps(value,sort_keys=True,separators=(",",":"))+"\n").encode()

def _sha(value:Any)->str:
    return hashlib.sha256(_canonical(value)).hexdigest()
