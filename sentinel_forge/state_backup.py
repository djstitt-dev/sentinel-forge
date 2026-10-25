"""Offline disposable-state backup verification; never includes credential secrets."""
from dataclasses import dataclass
import hashlib,json
from pathlib import Path
from .enrollment import EnrollmentError
FORMAT="sentinel-courier-state-backup-v1"
ALLOWED=("queue","delivery_journal","evidence","credential_references")
@dataclass(frozen=True)
class StateBackupManifest:
 format:str
 relationship_id:str
 files:tuple[tuple[str,str,int],...]
 manifest_digest:str
def build_state_backup_manifest(*,relationship_id:str,files:dict[str,Path])->StateBackupManifest:
 if not isinstance(relationship_id,str) or not relationship_id.strip():raise EnrollmentError("backup relationship required")
 if set(files)!=set(ALLOWED):raise EnrollmentError("backup state set incomplete")
 rows=[]
 for name in ALLOWED:
  p=Path(files[name])
  try:
   if p.is_symlink() or not p.is_file():raise EnrollmentError("backup source must be regular non-symlink file")
   data=p.read_bytes()
  except OSError as exc:raise EnrollmentError("backup source unreadable") from exc
  rows.append((name,"sha256:"+hashlib.sha256(data).hexdigest(),len(data)))
 core={"format":FORMAT,"relationship_id":relationship_id,"files":rows};return StateBackupManifest(FORMAT,relationship_id,tuple(rows),"sha256:"+_sha(core))
def verify_restored_state(manifest:StateBackupManifest,*,expected_relationship_id:str,files:dict[str,Path])->None:
 if manifest.format!=FORMAT or manifest.relationship_id!=expected_relationship_id:raise EnrollmentError("backup restore identity mismatch")
 if not isinstance(manifest,StateBackupManifest):raise EnrollmentError("backup manifest contract required")
 if not isinstance(manifest.files,tuple) or len(manifest.files)!=len(ALLOWED):raise EnrollmentError("backup manifest state set invalid")
 names=[]
 for row in manifest.files:
  if not isinstance(row,tuple) or len(row)!=3:raise EnrollmentError("backup manifest row invalid")
  n,d,z=row
  if not isinstance(n,str) or not isinstance(d,str) or not isinstance(z,int) or isinstance(z,bool) or z<0:raise EnrollmentError("backup manifest row invalid")
  names.append(n)
 if tuple(names)!=ALLOWED:raise EnrollmentError("backup manifest state order invalid")
 core={"format":manifest.format,"relationship_id":manifest.relationship_id,"files":[list(x) for x in manifest.files]}
 if manifest.manifest_digest!="sha256:"+_sha(core):raise EnrollmentError("backup manifest integrity failure")
 if set(files)!=set(ALLOWED):raise EnrollmentError("restored state set incomplete")
 expected={n:(d,z) for n,d,z in manifest.files}
 for name in ALLOWED:
  try:
   p=Path(files[name])
   if p.is_symlink() or not p.is_file():raise EnrollmentError("restored state must be regular non-symlink file")
   data=p.read_bytes()
  except OSError as exc:raise EnrollmentError("restored state unreadable") from exc
  digest="sha256:"+hashlib.sha256(data).hexdigest()
  if (digest,len(data))!=expected[name]:raise EnrollmentError(f"restored state mismatch: {name}")
def _sha(v):return hashlib.sha256((json.dumps(v,sort_keys=True,separators=(",",":"))+"\n").encode()).hexdigest()
