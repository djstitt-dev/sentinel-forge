"""Courier backup/restore manifest contract; no credential material."""
from dataclasses import dataclass
from .enrollment import EnrollmentError

@dataclass(frozen=True)
class BackupManifest:
 relationship_id:str
 queue_digest:str
 delivery_journal_digest:str
 evidence_digest:str
 credential_reference_digest:str
 includes_secret_material:bool=False

def build_backup_manifest(*,relationship_id,queue_digest,delivery_journal_digest,evidence_digest,credential_reference_digest,includes_secret_material=False):
 if includes_secret_material:raise EnrollmentError("Courier backup must not contain secret credential material")
 vals=(relationship_id,queue_digest,delivery_journal_digest,evidence_digest,credential_reference_digest)
 if any(not isinstance(v,str) or not v.strip() for v in vals):raise EnrollmentError("Courier backup manifest field required")
 return BackupManifest(*vals,False)

def require_restore_identity(manifest:BackupManifest,*,expected_relationship_id:str)->None:
 if manifest.relationship_id!=expected_relationship_id:raise EnrollmentError("Courier backup relationship mismatch")
 if manifest.includes_secret_material:raise EnrollmentError("Courier backup contains forbidden secret material")
