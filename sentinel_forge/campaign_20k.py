"""Deterministic 5K->20K security campaign metadata and checkpoint accounting."""
from __future__ import annotations
from dataclasses import dataclass,asdict
import hashlib,json
@dataclass(frozen=True)
class Campaign:
 start:int;end:int;name:str;evidence:str
 @property
 def count(self):return self.end-self.start+1
CAMPAIGNS=(
 Campaign(5001,6000,"enrollment lifecycle state-machine assault","test_wp20000_campaign_enrollment"),
 Campaign(6001,7000,"Courier queue-v2 transition and identity assault","test_wp20000_campaign_queue"),
 Campaign(7001,8000,"send/replay sequence authority assault","test_wp20000_campaign_sequences"),
 Campaign(8001,9000,"protected-wire/frame mutation assault","test_wp20000_campaign_wire"),
 Campaign(9001,10000,"authenticated enrollment artifact provenance assault","test_wp20000_campaign_artifact"),
 Campaign(10001,11000,"transport readiness and type-confusion assault","test_wp20000_campaign_readiness"),
 Campaign(11001,12000,"pairwise fleet-isolation substitution assault","test_wp20000_campaign_fleet"),
 Campaign(12001,13000,"evidence-chain rollback/mutation assault","test_wp20000_campaign_evidence"),
 Campaign(13001,14000,"backup/restore manifest assault","test_wp20000_campaign_backup"),
 Campaign(14001,15000,"cross-authority snapshot assault","test_wp20000_campaign_snapshot"),
 Campaign(15001,16000,"release-evidence contradiction assault","test_wp20000_campaign_release"),
 Campaign(16001,17000,"durable crash/fault-state assault","test_wp20000_campaign_crash"),
 Campaign(17001,18000,"resource-bound/parser assault","test_wp20000_campaign_resource"),
 Campaign(18001,19000,"revocation/rotation/authority-change assault","test_wp20000_campaign_rotation"),
 Campaign(19001,20000,"integrated offline Sentinel lifecycle scenarios","test_wp20000_campaign_integrated"),
)
def report():
 rows=[asdict(x)|{"count":x.count} for x in CAMPAIGNS]
 core={"format":"sentinel-forge-campaign-20k-v1","range":[5001,20000],"checkpoint_count":sum(x.count for x in CAMPAIGNS),"campaigns":rows}
 digest=hashlib.sha256((json.dumps(core,sort_keys=True,separators=(",",":"))+"\n").encode()).hexdigest()
 return core|{"campaign_digest":"sha256:"+digest,"production_ready":False}
