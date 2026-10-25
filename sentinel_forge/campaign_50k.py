"""Deterministic 20K->50K Sentinel Forge security campaign accounting."""
from __future__ import annotations
from dataclasses import dataclass,asdict
import hashlib,json
@dataclass(frozen=True)
class Campaign:
 start:int;end:int;name:str;evidence:str
 @property
 def count(self):return self.end-self.start+1
NAMES=(
"enrollment persisted-state parser assault",
"enrollment identity derivation uniqueness",
"challenge registry persisted-state assault",
"terminal revocation integrity assault",
"transition-intent lifecycle assault",
"recovery classification assault",
"recovery-intent lifecycle assault",
"credential-reference generation/binding assault",
"credential-registry persisted-state assault",
"pairwise session identity assault",
"receive anti-replay sequencing assault",
"outbound sequence authority assault",
"delivery-intent identity assault",
"queue-v2 illegal-transition assault",
"acknowledgement binding assault",
"delivery reconciliation assault",
"canonical frame mutation assault",
"framing hostile-length/resource assault",
"protection-provider binding assault",
"protected-wire context assault",
"protected-receive ordering assault",
"authenticity signer/key binding assault",
"evidence-journal mutation assault",
"evidence-anchor rollback/type assault",
"backup-restore manifest assault",
"release-evidence contradiction assault",
"transport-readiness state/type assault",
"assistant-independence state assault",
"cross-authority/fleet consistency assault",
"integrated offline Sentinel lifecycle assault",
)
CAMPAIGNS=tuple(Campaign(20001+i*1000,21000+i*1000,NAMES[i],f"test_wp50000_campaign_{i+1:02d}") for i in range(30))
def report():
 rows=[asdict(x)|{"count":x.count} for x in CAMPAIGNS]
 core={"format":"sentinel-forge-campaign-50k-v1","range":[20001,50000],"checkpoint_count":sum(x.count for x in CAMPAIGNS),"campaigns":rows}
 digest=hashlib.sha256((json.dumps(core,sort_keys=True,separators=(",",":"))+"\n").encode()).hexdigest()
 return core|{"campaign_digest":"sha256:"+digest,"production_ready":False}
