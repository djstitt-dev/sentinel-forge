import unittest
from sentinel_forge.peer_configuration import PeerProfile,compile_peer_configuration,render_remote_script_template
from sentinel_forge.enrollment import EnrollmentError

FP="SHA256:abcdefghijklmnopqrstuvwxyzABCDE1234567890"

def profile(**kw):
    d=dict(peer_identity="sentinel-reaper",role="reaper",host="192.0.2.10",ssh_user="reaperadmin",
           ssh_port=22,ssh_host_key_sha256=FP,
           requested_actions=("courier.send","courier.receive","health.report"))
    d.update(kw); return PeerProfile(**d)

class PeerConfigurationTests(unittest.TestCase):
    def test_compiles_target_bound_pairwise_plan(self):
        p=compile_peer_configuration(profile())
        self.assertEqual("sentinel-forge",p.forge_identity)
        self.assertEqual("sentinel-reaper",p.peer_identity)
        self.assertIn("AES-256-GCM",p.payload_protection)
        self.assertIn("no fleet-wide symmetric key",p.relationship_key_policy)
        self.assertIn("no implicit peer-to-peer trust",p.trust_topology)
        self.assertTrue(p.enrollment_id.startswith("enroll:"))
        self.assertTrue(p.challenge_id.startswith("challenge:"))
        self.assertTrue(p.plan_digest.startswith("sha256:"))

    def test_rejects_broad_or_unknown_authority(self):
        for action in ("shell.execute","credential.export","courier.admin"):
            with self.subTest(action=action):
                with self.assertRaises(EnrollmentError):
                    compile_peer_configuration(profile(requested_actions=(action,)))

    def test_rejects_ambiguous_identity_and_bad_host_key(self):
        with self.assertRaises(EnrollmentError): compile_peer_configuration(profile(peer_identity=""))
        with self.assertRaises(EnrollmentError): compile_peer_configuration(profile(ssh_host_key_sha256="unknown"))

    def test_script_template_is_non_operational_and_secret_free(self):
        s=render_remote_script_template(compile_peer_configuration(profile()))
        self.assertIn("NO secret material",s)
        self.assertIn("exit 78",s)
        self.assertNotIn("PRIVATE KEY",s)

    def test_each_peer_plan_is_relationship_specific(self):
        a=compile_peer_configuration(profile(peer_identity="sentinel-reaper"))
        b=compile_peer_configuration(profile(peer_identity="sentinel-scribe",role="scribe"))
        self.assertNotEqual(a.enrollment_id,b.enrollment_id)
        self.assertNotEqual(a.challenge_id,b.challenge_id)
        self.assertNotEqual(a.plan_digest,b.plan_digest)
