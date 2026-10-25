"""Authenticated portable enrollment artifact v2; algorithm-neutral signer/verifier."""
from __future__ import annotations
import hashlib,json,tarfile,tempfile
from pathlib import Path,PurePosixPath
from typing import Any
from .authenticity import AuthenticityEnvelope,create_envelope,verify_envelope,canonical_envelope
from .enrollment import EnrollmentBundle,EnrollmentError,verify_bundle
from .enrollment_artifact import INSTALLER,README
from .secure_io import ensure_private_file

FORMAT="sentinel-courier-enrollment-artifact-v2"
FILES=("bundle.json","install.py","README.txt")
ORDER=("MANIFEST.json","AUTHENTICITY.json",*FILES)
MAX_ARTIFACT_BYTES=5*1024*1024
MAX_MEMBER_BYTES=1024*1024

def export_authenticated_artifact(bundle:EnrollmentBundle,destination:Path,*,signer)->Path:
 if not verify_bundle(bundle):raise EnrollmentError("cannot export invalid enrollment bundle")
 destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory() as td:
  root=Path(td);(root/"bundle.json").write_bytes(_canonical(bundle.as_dict()));(root/"install.py").write_text(INSTALLER);(root/"README.txt").write_text(README)
  manifest={"format":FORMAT,"enrollment_id":bundle.enrollment_id,"remote_identity":bundle.remote_identity,"files":{}}
  for name in FILES:
   raw=(root/name).read_bytes();manifest["files"][name]={"size":len(raw),"sha256":hashlib.sha256(raw).hexdigest()}
  manifest_raw=_canonical(manifest);(root/"MANIFEST.json").write_bytes(manifest_raw)
  subject=_subject(manifest_raw,(root/"bundle.json").read_bytes())
  envelope=create_envelope(subject,signer);(root/"AUTHENTICITY.json").write_bytes(canonical_envelope(envelope))
  ensure_private_file(destination)
  with tarfile.open(destination,"w",format=tarfile.PAX_FORMAT) as tf:
   for name in ORDER:
    info=tf.gettarinfo(str(root/name),arcname=name);info.uid=0;info.gid=0;info.uname="";info.gname="";info.mtime=0;info.mode=0o755 if name=="install.py" else 0o600
    with (root/name).open("rb") as fh:tf.addfile(info,fh)
 return destination

def validate_authenticated_artifact(path:Path,*,verifier,expected_signer_identity:str,expected_key_reference:str,expected_remote_identity:str|None=None)->dict[str,Any]:
 path=Path(path)
 try:
  st=path.lstat()
  if not path.is_file() or path.is_symlink():raise EnrollmentError("authenticated artifact must be a regular non-symlink file")
  if st.st_size>MAX_ARTIFACT_BYTES:raise EnrollmentError("authenticated artifact exceeds bound")
  with tarfile.open(path,"r") as tf:
   members=tf.getmembers()
   if tuple(m.name for m in members)!=ORDER:raise EnrollmentError("authenticated artifact member set/order invalid")
   raw={}
   for m in members:
    pp=PurePosixPath(m.name)
    if pp.is_absolute() or ".." in pp.parts or not m.isfile() or m.size>MAX_MEMBER_BYTES:raise EnrollmentError("unsafe authenticated artifact member")
    fh=tf.extractfile(m)
    if fh is None:raise EnrollmentError("authenticated artifact member unreadable")
    raw[m.name]=fh.read(MAX_MEMBER_BYTES+1)
    if len(raw[m.name])!=m.size:raise EnrollmentError("authenticated artifact member size mismatch")
 except (OSError,tarfile.TarError) as exc:raise EnrollmentError("cannot read authenticated artifact") from exc
 try:
  manifest=json.loads(raw["MANIFEST.json"]);bundle=json.loads(raw["bundle.json"]);env=AuthenticityEnvelope(**json.loads(raw["AUTHENTICITY.json"]))
 except (json.JSONDecodeError,UnicodeDecodeError,TypeError,KeyError) as exc:raise EnrollmentError("malformed authenticated artifact metadata") from exc
 if set(manifest)!={"format","enrollment_id","remote_identity","files"} or manifest["format"]!=FORMAT:raise EnrollmentError("authenticated artifact manifest malformed")
 if set(manifest["files"])!=set(FILES):raise EnrollmentError("authenticated artifact file manifest malformed")
 if manifest["enrollment_id"]!=bundle.get("enrollment_id") or manifest["remote_identity"]!=bundle.get("remote_identity"):raise EnrollmentError("authenticated artifact identity mismatch")
 if expected_remote_identity is not None and bundle.get("remote_identity")!=expected_remote_identity:raise EnrollmentError("authenticated artifact bound to another remote")
 for name in FILES:
  spec=manifest["files"].get(name)
  if not isinstance(spec,dict) or set(spec)!={"size","sha256"} or spec["size"]!=len(raw[name]) or spec["sha256"]!=hashlib.sha256(raw[name]).hexdigest():raise EnrollmentError("authenticated artifact file integrity failure")
 if not verify_envelope(_subject(raw["MANIFEST.json"],raw["bundle.json"]),env,verifier,expected_signer_identity=expected_signer_identity,expected_key_reference=expected_key_reference):raise EnrollmentError("authenticated artifact authenticity failure")
 return {"format":FORMAT,"enrollment_id":bundle["enrollment_id"],"remote_identity":bundle["remote_identity"],"signer_identity":env.signer_identity,"key_reference":env.key_reference,"validated":True}

def _subject(manifest_raw:bytes,bundle_raw:bytes)->bytes:
 return _canonical({"format":"sentinel-enrollment-artifact-auth-subject-v1","manifest_sha256":hashlib.sha256(manifest_raw).hexdigest(),"bundle_sha256":hashlib.sha256(bundle_raw).hexdigest()})
def _canonical(v):return (json.dumps(v,sort_keys=True,separators=(",",":"))+"\n").encode()
