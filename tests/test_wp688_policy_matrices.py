import unittest
from sentinel_forge.capability import capabilities,negotiate,NegotiatedCapabilities,require_no_downgrade
from sentinel_forge.compatibility import require_compatible
from sentinel_forge.enrollment import EnrollmentError
from sentinel_forge.transport_health import assess_transport_health

class PolicyMatrixTests(unittest.TestCase):
 def healthy_args(self):return dict(relationship_active=True,revoked=False,current_credential=True,current_session=True,queue_consistent=True,audit_available=True,unresolved_effect=False,provider_available=True,last_probe_known=True)
 def test_each_authority_health_failure_blocks(self):
  mutations={"relationship_active":False,"revoked":True,"current_credential":False,"current_session":False,"queue_consistent":False,"audit_available":False,"unresolved_effect":True}
  for k,v in mutations.items():
   with self.subTest(k=k):
    a=self.healthy_args();a[k]=v;self.assertEqual("BLOCKED",assess_transport_health(**a).status)
 def test_provider_unavailable_degrades(self):
  a=self.healthy_args();a["provider_available"]=False;self.assertEqual("DEGRADED",assess_transport_health(**a).status)
 def test_unknown_observation_unknown(self):
  a=self.healthy_args();a["last_probe_known"]=False;self.assertEqual("UNKNOWN",assess_transport_health(**a).status)
 def test_required_feature_matrix(self):
  l=capabilities(peer_identity="forge",protocol_versions=[1],schema_versions=[1],features=["ack","anti-replay","extra"])
  r=capabilities(peer_identity="reaper",protocol_versions=[1],schema_versions=[1],features=["ack","anti-replay"])
  for feature in ("ack","anti-replay"):
   self.assertEqual(1,negotiate(l,r,expected_peer="reaper",minimum_protocol=1,minimum_schema=1,required_features=[feature]).protocol_version)
  with self.assertRaises(EnrollmentError):negotiate(l,r,expected_peer="reaper",minimum_protocol=1,minimum_schema=1,required_features=["extra"])
 def test_compatibility_each_role(self):
  for role in ("reaper","scribe","watchtower"):require_compatible(role,NegotiatedCapabilities(role,1,1,("ack","anti-replay")))
 def test_feature_downgrade_rejected(self):
  old=NegotiatedCapabilities("reaper",1,1,("ack","anti-replay"));new=NegotiatedCapabilities("reaper",1,1,("ack",))
  with self.assertRaises(EnrollmentError):require_no_downgrade(old,new)
 def test_peer_change_rejected_as_downgrade_context(self):
  with self.assertRaises(EnrollmentError):require_no_downgrade(NegotiatedCapabilities("reaper",1,1,()),NegotiatedCapabilities("scribe",1,1,()))
