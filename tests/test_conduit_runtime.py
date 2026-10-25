import unittest


from sentinel_forge.conduit_runtime import (
    ConduitError,
    ConduitRequest,
    authorize_request,
    parse_forced_command,
)


class ConduitRuntimeTests(unittest.TestCase):

    def test_status_round_trip(self):
        request = parse_forced_command(
            "sentinel-conduit status --peer sentinel-reaper"
        )

        approved = authorize_request(
            request,
            expected_peer_identity="sentinel-reaper",
        )

        self.assertEqual(
            ConduitRequest(
                operation="status",
                peer_identity="sentinel-reaper",
            ),
            approved,
        )

    def test_capabilities_round_trip(self):
        request = parse_forced_command(
            "sentinel-conduit capabilities --peer sentinel-reaper"
        )

        approved = authorize_request(
            request,
            expected_peer_identity="sentinel-reaper",
        )

        self.assertEqual("capabilities", approved.operation)

    def test_shell_rejected(self):
        with self.assertRaises(ConduitError):
            parse_forced_command("bash")

    def test_wrong_peer_rejected(self):
        request = parse_forced_command(
            "sentinel-conduit status --peer sentinel-reaper"
        )

        with self.assertRaises(ConduitError):
            authorize_request(
                request,
                expected_peer_identity="sentinel-scribe",
            )

    def test_noncanonical_command_rejected(self):
        bad = (
            " sentinel-conduit status --peer sentinel-reaper",
            "sentinel-conduit  status --peer sentinel-reaper",
            "sentinel-conduit status --peer sentinel-reaper ",
            "sentinel-conduit status --peer sentinel-reaper;id",
            "sentinel-conduit status --peer $(id)",
            'sentinel-conduit status --peer "sentinel-reaper"',
        )

        for command in bad:
            with self.subTest(command=repr(command)):
                with self.assertRaises(ConduitError):
                    parse_forced_command(command)

    def test_noncanonical_peer_rejected(self):
        bad = (
            "../sentinel-reaper",
            "Sentinel-Reaper",
            "sentinel_reaper",
            "sentinel.reaper",
            "sentinel\u2010reaper",
            "sentinel\u2011reaper",
            "sentinel\u2013reaper",
            "\u0455entinel-reaper",
            "sentinel-r\u0435aper",
        )

        for peer in bad:
            with self.subTest(peer=repr(peer)):
                with self.assertRaises(ConduitError):
                    parse_forced_command(
                        f"sentinel-conduit status --peer {peer}"
                    )

    def test_forged_operation_rejected_by_authorizer(self):
        request = ConduitRequest(
            operation="execute",
            peer_identity="sentinel-reaper",
        )

        with self.assertRaises(ConduitError):
            authorize_request(
                request,
                expected_peer_identity="sentinel-reaper",
            )


if __name__ == "__main__":
    unittest.main()
