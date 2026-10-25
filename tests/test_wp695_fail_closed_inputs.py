import unittest
from sentinel_forge.capability import capabilities
from sentinel_forge.enrollment import EnrollmentError
from sentinel_forge.production_config import build_production_config
from sentinel_forge.watchtower_telemetry import build_telemetry
class FailClosedInputTests(unittest.TestCase):
 def test_capability_empty_peer(self):
  with self.assertRaises(EnrollmentError):capabilities(peer_identity="",protocol_versions=[1],schema_versions=[1])
 def test_capability_empty_protocols(self):
  with self.assertRaises(EnrollmentError):capabilities(peer_identity="p",protocol_versions=[],schema_versions=[1])
 def test_capability_empty_schemas(self):
  with self.assertRaises(EnrollmentError):capabilities(peer_identity="p",protocol_versions=[1],schema_versions=[])
 def test_capability_bool_protocol(self):
  with self.assertRaises(EnrollmentError):capabilities(peer_identity="p",protocol_versions=[True],schema_versions=[1])
 def test_capability_zero_schema(self):
  with self.assertRaises(EnrollmentError):capabilities(peer_identity="p",protocol_versions=[1],schema_versions=[0])
 def test_capability_bad_feature(self):
  with self.assertRaises(EnrollmentError):capabilities(peer_identity="p",protocol_versions=[1],schema_versions=[1],features=[""])
 def test_config_unknown_field(self):
  base=dict(peer_identity="r",peer_role="reaper",endpoint_reference="e",credential_reference="c",protection_provider_reference="p",network_provider_reference="n",policy_reference="x")
  with self.assertRaises(EnrollmentError):build_production_config(**base,wat="x")
 def test_config_blank_reference(self):
  with self.assertRaises(EnrollmentError):build_production_config(peer_identity="r",peer_role="reaper",endpoint_reference="",credential_reference="c",protection_provider_reference="p",network_provider_reference="n",policy_reference="x")
 def test_telemetry_bool_sequence(self):
  with self.assertRaises(EnrollmentError):build_telemetry(relationship_id="r",peer_identity="p",event_type="e",outcome="o",reason="x",correlation_id="c",sequence=True)
 def test_telemetry_zero_sequence(self):
  with self.assertRaises(EnrollmentError):build_telemetry(relationship_id="r",peer_identity="p",event_type="e",outcome="o",reason="x",correlation_id="c",sequence=0)
 def test_telemetry_unknown_field(self):
  with self.assertRaises(EnrollmentError):build_telemetry(relationship_id="r",peer_identity="p",event_type="e",outcome="o",reason="x",correlation_id="c",wat="x")
