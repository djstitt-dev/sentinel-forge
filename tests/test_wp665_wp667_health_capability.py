import unittest
from sentinel_forge.capability import capabilities,negotiate,require_no_downgrade
from sentinel_forge.enrollment import EnrollmentError
from sentinel_forge.transport_health import assess_transport_health

class HealthCapabilityTests(unittest.TestCase):
 def test_health_is_evidence_based(self):
  h=assess_transport_health(relationship_active=True,revoked=False,current_credential=True,current_session=True,queue_consistent=True,audit_available=True,unresolved_effect=False,provider_available=True,last_probe_known=True);self.assertEqual("HEALTHY",h.status)
 def test_reachable_unknown_not_healthy(self):
  h=assess_transport_health(relationship_active=True,revoked=False,current_credential=True,current_session=True,queue_consistent=True,audit_available=True,unresolved_effect=False,provider_available=True,last_probe_known=False);self.assertEqual("UNKNOWN",h.status)
 def test_authority_problem_blocks(self):
  h=assess_transport_health(relationship_active=True,revoked=True,current_credential=True,current_session=True,queue_consistent=True,audit_available=True,unresolved_effect=False,provider_available=True,last_probe_known=True);self.assertEqual("BLOCKED",h.status)
 def test_highest_common_versions(self):
  l=capabilities(peer_identity="forge",protocol_versions=[1,2,3],schema_versions=[1,2],features=["ack","replay"])
  r=capabilities(peer_identity="reaper",protocol_versions=[2,3],schema_versions=[2],features=["ack","replay"])
  n=negotiate(l,r,expected_peer="reaper",minimum_protocol=2,minimum_schema=2,required_features=["ack"]);self.assertEqual((3,2),(n.protocol_version,n.schema_version))
 def test_minimum_prevents_old_version(self):
  l=capabilities(peer_identity="forge",protocol_versions=[1,2],schema_versions=[1],features=[])
  r=capabilities(peer_identity="reaper",protocol_versions=[1],schema_versions=[1],features=[])
  with self.assertRaisesRegex(EnrollmentError,"protocol"):negotiate(l,r,expected_peer="reaper",minimum_protocol=2,minimum_schema=1)
 def test_peer_substitution_fails(self):
  l=capabilities(peer_identity="forge",protocol_versions=[1],schema_versions=[1]);r=capabilities(peer_identity="scribe",protocol_versions=[1],schema_versions=[1])
  with self.assertRaisesRegex(EnrollmentError,"peer identity"):negotiate(l,r,expected_peer="reaper",minimum_protocol=1,minimum_schema=1)
 def test_downgrade_rejected(self):
  l=capabilities(peer_identity="forge",protocol_versions=[1,2],schema_versions=[1,2],features=["ack","replay"])
  r=capabilities(peer_identity="reaper",protocol_versions=[1,2],schema_versions=[1,2],features=["ack","replay"])
  old=negotiate(l,r,expected_peer="reaper",minimum_protocol=1,minimum_schema=1)
  r2=capabilities(peer_identity="reaper",protocol_versions=[1],schema_versions=[1],features=["ack"])
  cur=negotiate(l,r2,expected_peer="reaper",minimum_protocol=1,minimum_schema=1)
  with self.assertRaisesRegex(EnrollmentError,"downgrade"):require_no_downgrade(old,cur)
