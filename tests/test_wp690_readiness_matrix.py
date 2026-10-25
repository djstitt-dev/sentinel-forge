import unittest
from sentinel_forge.courier_acceptance import REQUIRED_OFFLINE,assess_courier_acceptance
from sentinel_forge.readiness_report import build_readiness_report
from sentinel_forge.transport_health import TransportHealth
class ReadinessMatrixTests(unittest.TestCase):
 def acc(self,**kw):
  x=dict(checks={k:True for k in REQUIRED_OFFLINE},framing_complete=True,protection_provider_complete=True,production_protection_approved=True,production_network_approved=True,assistant_independence_verified=True);x.update(kw);return assess_courier_acceptance(**x)
 def report(self,a=None,h=None,**kw):
  x=dict(acceptance=a or self.acc(),health=h or TransportHealth("HEALTHY",()),compatibility_valid=True,configuration_valid=True,activation_plan_valid=True,backup_contract_valid=True,telemetry_contract_valid=True);x.update(kw);return build_readiness_report(**x)
 def test_each_acceptance_production_gate_blocks(self):
  gates=("framing_complete","protection_provider_complete","production_protection_approved","production_network_approved","assistant_independence_verified")
  for g in gates:
   with self.subTest(g=g):self.assertFalse(self.report(a=self.acc(**{g:False})).production_ready)
 def test_each_contract_gate_blocks_offline(self):
  gates=("compatibility_valid","configuration_valid","activation_plan_valid","backup_contract_valid","telemetry_contract_valid")
  for g in gates:
   with self.subTest(g=g):
    r=self.report(**{g:False});self.assertFalse(r.offline_ready);self.assertFalse(r.production_ready)
 def test_each_nonhealthy_transport_status_blocks_production(self):
  for s in ("BLOCKED","DEGRADED","UNKNOWN"):
   with self.subTest(s=s):self.assertFalse(self.report(h=TransportHealth(s,("x",))).production_ready)
 def test_each_offline_invariant_individually_blocks(self):
  for name in REQUIRED_OFFLINE:
   with self.subTest(name=name):
    checks={x:True for x in REQUIRED_OFFLINE};checks[name]=False
    self.assertFalse(self.report(a=self.acc(checks=checks)).offline_ready)
