"""Deterministic offline release-evidence summary. No production authorization is conferred."""
from __future__ import annotations
from dataclasses import dataclass,asdict
import hashlib,json
from .enrollment import EnrollmentError

FORMAT="sentinel-forge-release-evidence-v1"
@dataclass(frozen=True)
class ReleaseEvidence:
 format:str;repository_head:str;test_count:int;checkpoint_end:int;offline_invariants_passed:bool;production_ready:bool;blockers:tuple[str,...];evidence_digest:str
 def as_dict(self):return asdict(self)

def build_release_evidence(*,repository_head:str,test_count:int,checkpoint_end:int,offline_invariants_passed:bool,production_ready:bool,blockers)->ReleaseEvidence:
 if not isinstance(repository_head,str) or len(repository_head)!=40 or any(c not in "0123456789abcdef" for c in repository_head):raise EnrollmentError("release evidence repository head invalid")
 for n,v in (("test_count",test_count),("checkpoint_end",checkpoint_end)):
  if not isinstance(v,int) or isinstance(v,bool) or v<1:raise EnrollmentError("release evidence numeric field invalid")
 if type(offline_invariants_passed) is not bool or type(production_ready) is not bool:raise EnrollmentError("release evidence booleans required")
 b=tuple(blockers)
 if any(not isinstance(x,str) or not x.strip() for x in b) or len(set(b))!=len(b):raise EnrollmentError("release evidence blockers invalid")
 if production_ready and (not offline_invariants_passed or b):raise EnrollmentError("production-ready evidence contradicts blockers/invariants")
 if not production_ready and not b:raise EnrollmentError("non-production release evidence requires explicit blockers")
 core={"format":FORMAT,"repository_head":repository_head,"test_count":test_count,"checkpoint_end":checkpoint_end,"offline_invariants_passed":offline_invariants_passed,"production_ready":production_ready,"blockers":b}
 return ReleaseEvidence(**core,evidence_digest="sha256:"+_sha(core))
def verify_release_evidence(e):
 if not isinstance(e,ReleaseEvidence):raise EnrollmentError("release evidence contract required")
 d=e.as_dict();digest=d.pop("evidence_digest");d["blockers"]=tuple(d["blockers"])
 if d["format"]!=FORMAT:raise EnrollmentError("release evidence format invalid")
 if digest!="sha256:"+_sha(d):raise EnrollmentError("release evidence integrity failure")
 build_release_evidence(repository_head=d["repository_head"],test_count=d["test_count"],checkpoint_end=d["checkpoint_end"],
  offline_invariants_passed=d["offline_invariants_passed"],production_ready=d["production_ready"],blockers=d["blockers"])
 return True
def _sha(v):return hashlib.sha256((json.dumps(v,sort_keys=True,separators=(",",":"))+"\n").encode()).hexdigest()
