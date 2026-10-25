"""Offline Assistant Independence / Zero Residual Access contract.

This module evaluates supplied inventory evidence only. It does not inspect the
host, remove software, contact a network, or claim that any real host is clean.
"""
from __future__ import annotations
from dataclasses import dataclass,asdict
import hashlib,json
from .enrollment import EnrollmentError

FORMAT="sentinel-assistant-independence-v1"
REQUIRED_CATEGORIES=frozenset({
 "processes","services","packages","credentials","accounts","persistence",
 "scheduled_jobs","listeners","remote_management","trust_anchors",
})
PROHIBITED_FINDING_CLASSES=frozenset({
 "assistant_credential","assistant_token","assistant_remote_agent",
 "assistant_callback","assistant_persistent_session","assistant_account",
 "assistant_privileged_service","assistant_scheduled_job",
 "assistant_listener","assistant_remote_management",
 "assistant_trust_anchor","undocumented_access_path",
})

@dataclass(frozen=True)
class InventoryFinding:
 category:str
 finding_class:str
 identity:str
 present:bool
 explanation:str

@dataclass(frozen=True)
class IndependenceInventory:
 format:str
 forge_identity:str
 collector_method:str
 categories_observed:tuple[str,...]
 findings:tuple[InventoryFinding,...]
 inventory_digest:str
 def as_dict(self):
  d=asdict(self);d["categories_observed"]=list(self.categories_observed);d["findings"]=list(d["findings"]);return d

@dataclass(frozen=True)
class IndependenceAssessment:
 passed:bool
 reasons:tuple[str,...]
 inventory_digest:str

def build_inventory(*,forge_identity:str,collector_method:str,categories_observed:list[str],
                    findings:list[InventoryFinding])->IndependenceInventory:
 if not _text(forge_identity) or not _text(collector_method):
  raise EnrollmentError("independence inventory identity and collector method required")
 cats=tuple(sorted(set(categories_observed)))
 if any(c not in REQUIRED_CATEGORIES for c in cats):
  raise EnrollmentError("unknown independence inventory category")
 try:
  normalized=tuple(sorted(findings,key=lambda f:(f.category,f.finding_class,f.identity)))
 except Exception as exc:raise EnrollmentError("malformed independence finding") from exc
 for f in normalized:
  if not isinstance(f,InventoryFinding):raise EnrollmentError("malformed independence finding")
  if type(f.present) is not bool:raise EnrollmentError("finding presence must be boolean")
  if f.category not in REQUIRED_CATEGORIES:raise EnrollmentError("finding has unknown category")
  if not _text(f.finding_class) or not _text(f.identity) or not _text(f.explanation):
   raise EnrollmentError("finding fields must be explicit")
 core={"format":FORMAT,"forge_identity":forge_identity,"collector_method":collector_method,
       "categories_observed":list(cats),"findings":[asdict(f) for f in normalized]}
 return IndependenceInventory(FORMAT,forge_identity,collector_method,cats,normalized,"sha256:"+_sha(core))

def assess_independence(inv:IndependenceInventory)->IndependenceAssessment:
 expected=build_inventory(forge_identity=inv.forge_identity,collector_method=inv.collector_method,
  categories_observed=list(inv.categories_observed),findings=list(inv.findings))
 if expected!=inv:raise EnrollmentError("independence inventory integrity mismatch")
 reasons=[]
 missing=sorted(REQUIRED_CATEGORIES-set(inv.categories_observed))
 if missing:reasons.append("missing required inventory categories: "+",".join(missing))
 for f in inv.findings:
  if f.present and f.finding_class in PROHIBITED_FINDING_CLASSES:
   reasons.append(f"prohibited residual access present: {f.finding_class}:{f.identity}")
  if f.present and f.finding_class not in PROHIBITED_FINDING_CLASSES:
   reasons.append(f"unclassified present finding requires review: {f.finding_class}:{f.identity}")
 return IndependenceAssessment(not reasons,tuple(reasons),inv.inventory_digest)

def require_independent(inv:IndependenceInventory)->None:
 a=assess_independence(inv)
 if not a.passed:raise EnrollmentError("ASSISTANT_INDEPENDENCE_FAILED: "+"; ".join(a.reasons))

def _text(v):return isinstance(v,str) and bool(v.strip())
def _canonical(v):return (json.dumps(v,sort_keys=True,separators=(",",":"))+"\n").encode()
def _sha(v):return hashlib.sha256(_canonical(v)).hexdigest()

@dataclass(frozen=True)
class IndependenceAttestation:
 inventory_digest:str
 verifier_identity:str
 verification_scope:str
 host_observed:bool
 development_access_removed:bool
 attestation_digest:str

def build_attestation(inv:IndependenceInventory,*,verifier_identity:str,verification_scope:str,
                      host_observed:bool,development_access_removed:bool)->IndependenceAttestation:
 require_independent(inv)
 if not _text(verifier_identity) or not _text(verification_scope):
  raise EnrollmentError("independence attestation verifier and scope required")
 if type(host_observed) is not bool or type(development_access_removed) is not bool:
  raise EnrollmentError("independence attestation flags must be boolean")
 core={"inventory_digest":inv.inventory_digest,"verifier_identity":verifier_identity,
       "verification_scope":verification_scope,"host_observed":host_observed,
       "development_access_removed":development_access_removed}
 return IndependenceAttestation(**core,attestation_digest="sha256:"+_sha(core))

def require_production_independence(inv:IndependenceInventory,att:IndependenceAttestation)->None:
 require_independent(inv)
 expected=build_attestation(inv,verifier_identity=att.verifier_identity,
  verification_scope=att.verification_scope,host_observed=att.host_observed,
  development_access_removed=att.development_access_removed)
 if expected!=att:raise EnrollmentError("independence attestation integrity mismatch")
 if not att.host_observed:
  raise EnrollmentError("PRODUCTION_INDEPENDENCE_BLOCKED: host verification evidence required")
 if not att.development_access_removed:
  raise EnrollmentError("PRODUCTION_INDEPENDENCE_BLOCKED: development access removal not verified")
