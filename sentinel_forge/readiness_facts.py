"""Validated evidence facts used to derive readiness inputs; performs no host observation."""
from dataclasses import dataclass
from .enrollment import EnrollmentError
@dataclass(frozen=True)
class ReadinessFact:
 name:str
 satisfied:bool
 source:str
 observed:bool
def fact(*,name,satisfied,source,observed):
 if not isinstance(name,str) or not name.strip() or not isinstance(source,str) or not source.strip():raise EnrollmentError("readiness fact identity/source required")
 if not isinstance(satisfied,bool) or not isinstance(observed,bool):raise EnrollmentError("readiness fact booleans required")
 return ReadinessFact(name,satisfied,source,observed)
REQUIRED=("compatibility_valid","configuration_valid","activation_plan_valid","backup_contract_valid","telemetry_contract_valid")
def derive_contract_facts(facts)->dict[str,bool]:
 by={}
 for f in facts:
  if not isinstance(f,ReadinessFact):raise EnrollmentError("invalid readiness fact")
  if f.name in by:raise EnrollmentError("duplicate readiness fact")
  by[f.name]=f
 missing=set(REQUIRED)-set(by)
 extra=set(by)-set(REQUIRED)
 if missing or extra:raise EnrollmentError("readiness fact set incomplete")
 out={}
 for name in REQUIRED:
  f=by[name]
  if not f.observed:raise EnrollmentError(f"readiness fact unobserved: {name}")
  out[name]=f.satisfied
 return out
