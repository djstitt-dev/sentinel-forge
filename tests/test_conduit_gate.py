import unittest

from sentinel_forge.enrollment import EnrollmentError
from sentinel_forge.conduit_gate import (
    ConduitRequest,
    parse_forced_command,
    authorize_request,
)


class ConduitGateTests(unittest.TestCase):

    def test_status_allowed_for_exact_peer(self):
        req = parse_forced_command(
            "sentinel-conduit status --peer sentinel-reaper"
        )

        self.assertEqual(
            req,
            ConduitRequest(
                operation="status",
                peer_identity="sentinel-reaper",
            ),
        )

        approved = authorize_request(
            req,
            expected_peer_identity="sentinel-reaper",
        )

        self.assertEqual("status", approved.operation)
        self.assertEqual("sentinel-reaper", approved.peer_identity)

    def test_capabilities_allowed_for_exact_peer(self):
        req = parse_forced_command(
            "sentinel-conduit capabilities --peer sentinel-reaper"
        )

        approved = authorize_request(
            req,
            expected_peer_identity="sentinel-reaper",
        )

        self.assertEqual("capabilities", approved.operation)

    def test_arbitrary_shell_rejected(self):
        with self.assertRaises(EnrollmentError):
            parse_forced_command("bash")

    def test_shell_metacharacters_rejected(self):
        bad = (
            "sentinel-conduit status --peer sentinel-reaper; id",
            "sentinel-conduit status --peer sentinel-reaper && id",
            "sentinel-conduit status --peer sentinel-reaper | id",
            "sentinel-conduit status --peer sentinel-reaper > /tmp/x",
            "sentinel-conduit status --peer $(id)",
            "sentinel-conduit status --peer `id`",
        )

        for command in bad:
            with self.subTest(command=command):
                with self.assertRaises(EnrollmentError):
                    parse_forced_command(command)

    def test_unknown_operation_rejected(self):
        with self.assertRaises(EnrollmentError):
            parse_forced_command(
                "sentinel-conduit execute --peer sentinel-reaper"
            )

    def test_missing_peer_rejected(self):
        with self.assertRaises(EnrollmentError):
            parse_forced_command(
                "sentinel-conduit status"
            )

    def test_extra_argument_rejected(self):
        with self.assertRaises(EnrollmentError):
            parse_forced_command(
                "sentinel-conduit status --peer sentinel-reaper extra"
            )

    def test_wrong_peer_binding_rejected(self):
        req = parse_forced_command(
            "sentinel-conduit status --peer sentinel-reaper"
        )

        with self.assertRaises(EnrollmentError):
            authorize_request(
                req,
                expected_peer_identity="sentinel-scribe",
            )

    def test_empty_original_command_rejected(self):
        with self.assertRaises(EnrollmentError):
            parse_forced_command("")

    def test_peer_identity_is_canonical(self):
        bad = (
            "Sentinel-Reaper",
            "../sentinel-reaper",
            "sentinel reaper",
            "sentinel-reaper/",
            "sentinel-reaper;id",
        )

        for peer in bad:
            with self.subTest(peer=peer):
                with self.assertRaises(EnrollmentError):
                    parse_forced_command(
                        f"sentinel-conduit status --peer {peer}"
                    )


if __name__ == "__main__":
    unittest.main()
