import unittest
from sentinel_forge.enrollment import EnrollmentError,build_bundle
from sentinel_forge.trust_domain import derive_trust_domain
class FleetTargetRoleTests(unittest.TestCase):
 def test_same_identity_wrong_role_changes_relationship(self):
  a=derive_trust_domain(build_bundle(forge_identity="forge",remote_identity="peer",remote_role="reaper",permitted_actions=["receive"],permitted_target="peer",policy_reference="p"));b=derive_trust_domain(build_bundle(forge_identity="forge",remote_identity="peer",remote_role="scribe",permitted_actions=["receive"],permitted_target="peer",policy_reference="p"));self.assertNotEqual(a.relationship_id,b.relationship_id)
 def test_same_identity_wrong_target_changes_relationship(self):
  a=derive_trust_domain(build_bundle(forge_identity="forge",remote_identity="peer",remote_role="reaper",permitted_actions=["receive"],permitted_target="peer",policy_reference="p"));b=derive_trust_domain(build_bundle(forge_identity="forge",remote_identity="peer",remote_role="reaper",permitted_actions=["receive"],permitted_target="other",policy_reference="p"));self.assertNotEqual(a.relationship_id,b.relationship_id)
