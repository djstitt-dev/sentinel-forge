"""Durable authority for current pairwise credential-reference metadata.

Stores references only. It never creates, reads, exports, or rotates key material.
"""
from __future__ import annotations
from .secure_io import private_open
import fcntl,hashlib,json,os
from pathlib import Path
from .credential_reference import RelationshipCredentialReference,require_rotation,verify_credential_reference
from .enrollment import EnrollmentError
from .trust_domain import PairwiseTrustDomain

FORMAT="sentinel-pairwise-credential-registry-v1"

class CredentialReferenceRegistry:
 def __init__(self,path:Path):
  self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
  with self._lock(True):
   if not self.path.exists():self._write({"format":FORMAT,"relationships":{}})
   self._load()

 def register_initial(self,domain:PairwiseTrustDomain,reference:RelationshipCredentialReference):
  with self._lock(True):
   db=self._load();rels=db["relationships"]
   if domain.relationship_id in rels:raise EnrollmentError("credential relationship already registered")
   if reference.generation!=1:raise EnrollmentError("initial credential generation must be one")
   if not verify_credential_reference(reference,domain):raise EnrollmentError("credential reference relationship mismatch")
   self._require_key_reference_unique(rels,reference)
   rels[domain.relationship_id]=reference.as_dict();self._write(db);return reference

 def rotate(self,domain:PairwiseTrustDomain,reference:RelationshipCredentialReference):
  with self._lock(True):
   db=self._load();rels=db["relationships"];raw=rels.get(domain.relationship_id)
   if raw is None:raise EnrollmentError("credential relationship is not registered")
   previous=self._decode(raw);require_rotation(previous,reference,domain)
   self._require_key_reference_unique(rels,reference,ignore_relationship=domain.relationship_id)
   rels[domain.relationship_id]=reference.as_dict();self._write(db);return reference

 def current(self,domain:PairwiseTrustDomain)->RelationshipCredentialReference:
  with self._lock(False):
   raw=self._load()["relationships"].get(domain.relationship_id)
   if raw is None:raise EnrollmentError("credential relationship is not registered")
   ref=self._decode(raw)
   if not verify_credential_reference(ref,domain):raise EnrollmentError("credential registry relationship binding mismatch")
   return ref

 def require_current(self,domain:PairwiseTrustDomain,reference:RelationshipCredentialReference)->None:
  if self.current(domain)!=reference:raise EnrollmentError("stale or non-current credential reference")

 def _require_key_reference_unique(self,rels,reference,ignore_relationship=None):
  for rid,raw in rels.items():
   if rid==ignore_relationship:continue
   existing=self._decode(raw)
   if existing.key_reference==reference.key_reference:
    raise EnrollmentError("fleet-wide credential reuse across pairwise relationships is prohibited")

 def _decode(self,raw):
  try:
   if not isinstance(raw,dict):raise TypeError
   return RelationshipCredentialReference(**raw)
  except (TypeError,KeyError) as exc:raise EnrollmentError("malformed credential registry record") from exc

 def _load(self):
  try:db=json.loads(self.path.read_text())
  except (OSError,json.JSONDecodeError) as exc:raise EnrollmentError("malformed credential registry") from exc
  if not isinstance(db,dict) or set(db)!={"format","relationships"} or db.get("format")!=FORMAT or not isinstance(db.get("relationships"),dict):
   raise EnrollmentError("malformed credential registry")
  for rid,raw in db["relationships"].items():
   if not isinstance(rid,str) or not rid.strip():raise EnrollmentError("malformed credential registry relationship")
   ref=self._decode(raw)
   if ref.relationship_id!=rid:raise EnrollmentError("credential registry relationship identity mismatch")
   for value in (ref.relationship_id,ref.forge_identity,ref.peer_identity,ref.enrollment_id,ref.key_reference,ref.reference_digest):
    if not isinstance(value,str) or not value.strip():raise EnrollmentError("malformed credential registry record")
   if not isinstance(ref.generation,int) or isinstance(ref.generation,bool) or ref.generation<1:
    raise EnrollmentError("malformed credential registry record")
   core={"format":ref.format,"relationship_id":ref.relationship_id,"forge_identity":ref.forge_identity,
         "peer_identity":ref.peer_identity,"enrollment_id":ref.enrollment_id,
         "generation":ref.generation,"key_reference":ref.key_reference}
   expected="sha256:"+hashlib.sha256((json.dumps(core,sort_keys=True,separators=(",",":"))+"\n").encode()).hexdigest()
   if ref.format!="sentinel-pairwise-credential-reference-v1" or ref.reference_digest!=expected:
    raise EnrollmentError("credential registry record integrity failure")
  # Fail closed even if durable state was externally edited to reuse a key reference.
  owners={}
  for rid,raw in db["relationships"].items():
   ref=self._decode(raw);owner=owners.setdefault(ref.key_reference,rid)
   if owner!=rid:raise EnrollmentError("fleet-wide credential reuse detected in durable registry")
  return db

 def _write(self,db):
  tmp=self.path.with_suffix(self.path.suffix+".tmp")
  data=(json.dumps(db,sort_keys=True,separators=(",",":"))+"\n").encode()
  with private_open(tmp,"wb") as f:f.write(data);f.flush();os.fsync(f.fileno())
  tmp.replace(self.path)
  dfd=os.open(self.path.parent,os.O_RDONLY)
  try:os.fsync(dfd)
  finally:os.close(dfd)

 def _lock(self,exclusive):
  return _RegistryLock(self.path.with_suffix(self.path.suffix+".lock"),exclusive)

class _RegistryLock:
 def __init__(self,path,exclusive):self.path=Path(path);self.exclusive=exclusive;self.fd=None
 def __enter__(self):
  try:
   self.fd=os.open(self.path,os.O_RDWR|os.O_CREAT,0o600)
   fcntl.flock(self.fd,fcntl.LOCK_EX if self.exclusive else fcntl.LOCK_SH)
  except OSError as exc:
   if self.fd is not None:os.close(self.fd);self.fd=None
   raise EnrollmentError("credential registry lock unavailable") from exc
  return self
 def __exit__(self,*_):
  try:
   if self.fd is not None:fcntl.flock(self.fd,fcntl.LOCK_UN)
  finally:
   if self.fd is not None:os.close(self.fd);self.fd=None
