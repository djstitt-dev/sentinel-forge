import unittest

from sentinel_forge.enrollment import EnrollmentError
from sentinel_forge.conduit_gate import (
    ConduitRequest,
    authorize_request,
    parse_forced_command,
)


class ConduitGateAdversarialTests(unittest.TestCase):

    def assert_rejected(self, command):
        with self.subTest(command=repr(command)):
            with self.assertRaises(EnrollmentError):
                parse_forced_command(command)

    def test_noncanonical_whitespace_rejected(self):
        bad = (
            " sentinel-conduit status --peer sentinel-reaper",
            "sentinel-conduit status --peer sentinel-reaper ",
            "sentinel-conduit  status --peer sentinel-reaper",
            "sentinel-conduit\tstatus --peer sentinel-reaper",
            "sentinel-conduit status\t--peer sentinel-reaper",
            "sentinel-conduit status --peer\tsentinel-reaper",
            "sentinel-conduit\nstatus --peer sentinel-reaper",
            "sentinel-conduit status --peer sentinel-reaper\n",
            "sentinel-conduit status --peer sentinel-reaper\r\n",
        )

        for command in bad:
            self.assert_rejected(command)

    def test_quoted_tokens_rejected_even_if_semantically_equivalent(self):
        bad = (
            "'sentinel-conduit' status --peer sentinel-reaper",
            'sentinel-conduit "status" --peer sentinel-reaper',
            "sentinel-conduit status '--peer' sentinel-reaper",
            'sentinel-conduit status --peer "sentinel-reaper"',
            "sentinel-conduit status --peer 'sentinel-reaper'",
        )

        for command in bad:
            self.assert_rejected(command)

    def test_alternate_executable_forms_rejected(self):
        bad = (
            "/usr/local/sbin/sentinel-conduit status --peer sentinel-reaper",
            "./sentinel-conduit status --peer sentinel-reaper",
            "../sentinel-conduit status --peer sentinel-reaper",
            "SENTINEL-CONDUIT status --peer sentinel-reaper",
            "sentinel_conduit status --peer sentinel-reaper",
        )

        for command in bad:
            self.assert_rejected(command)

    def test_shell_control_operators_rejected(self):
        bad = (
            "sentinel-conduit status --peer sentinel-reaper;id",
            "sentinel-conduit status --peer sentinel-reaper; id",
            "sentinel-conduit status --peer sentinel-reaper&&id",
            "sentinel-conduit status --peer sentinel-reaper || id",
            "sentinel-conduit status --peer sentinel-reaper|id",
            "sentinel-conduit status --peer sentinel-reaper &",
            "sentinel-conduit status --peer sentinel-reaper >x",
            "sentinel-conduit status --peer sentinel-reaper 2>&1",
        )

        for command in bad:
            self.assert_rejected(command)

    def test_command_substitution_and_expansion_rejected(self):
        bad = (
            "sentinel-conduit status --peer $(id)",
            "sentinel-conduit status --peer ${USER}",
            "sentinel-conduit status --peer $USER",
            "sentinel-conduit status --peer `id`",
            "sentinel-conduit status --peer sentinel-${USER}",
            "sentinel-conduit status --peer sentinel-*",
            "sentinel-conduit status --peer sentinel-?",
        )

        for command in bad:
            self.assert_rejected(command)

    def test_option_smuggling_rejected(self):
        bad = (
            "sentinel-conduit status --peer --help",
            "sentinel-conduit status --peer -v",
            "sentinel-conduit --help --peer sentinel-reaper",
            "sentinel-conduit status --peer=sentinel-reaper",
            "sentinel-conduit status --peer sentinel-reaper --help",
            "sentinel-conduit status --peer sentinel-reaper --peer sentinel-scribe",
        )

        for command in bad:
            self.assert_rejected(command)

    def test_peer_path_and_address_forms_rejected(self):
        bad_peers = (
            ".",
            "..",
            "../sentinel-reaper",
            "sentinel-reaper/..",
            "/sentinel-reaper",
            "sentinel-reaper/",
            "sentinel_reaper",
            "sentinel.reaper",
            "sentinel@reaper",
            "sentinel:reaper",
            "192.168.56.105",
        )

        for peer in bad_peers:
            self.assert_rejected(
                f"sentinel-conduit status --peer {peer}"
            )

    def test_unicode_lookalikes_rejected(self):
        bad_peers = (
            "sentinel\u2010reaper",  # U+2010 hyphen
            "sentinel\u2011reaper",  # U+2011 non-breaking hyphen
            "sentinel\u2013reaper",  # U+2013 en dash
            "\u0455entinel-reaper",  # Cyrillic small dze
            "sentinel-r\u0435aper",  # Cyrillic small ie
        )

        for peer in bad_peers:
            self.assert_rejected(
                f"sentinel-conduit status --peer {peer}"
            )

    def test_control_characters_rejected(self):
        bad = (
            "sentinel-conduit status --peer sentinel-reaper\x00",
            "sentinel-conduit status --peer sentinel-reaper\x07",
            "sentinel-conduit status --peer sentinel-reaper\x1b",
        )

        for command in bad:
            self.assert_rejected(command)

    def test_overlong_peer_rejected(self):
        peer = "a" * 129

        self.assert_rejected(
            f"sentinel-conduit status --peer {peer}"
        )

    def test_authorizer_rejects_forged_request_operation(self):
        forged = ConduitRequest(
            operation="execute",
            peer_identity="sentinel-reaper",
        )

        with self.assertRaises(EnrollmentError):
            authorize_request(
                forged,
                expected_peer_identity="sentinel-reaper",
            )

    def test_authorizer_rejects_forged_request_peer(self):
        forged = ConduitRequest(
            operation="status",
            peer_identity="../sentinel-reaper",
        )

        with self.assertRaises(EnrollmentError):
            authorize_request(
                forged,
                expected_peer_identity="sentinel-reaper",
            )

    def test_exact_canonical_commands_still_pass(self):
        for operation in ("status", "capabilities"):
            command = (
                f"sentinel-conduit {operation} "
                "--peer sentinel-reaper"
            )

            request = parse_forced_command(command)

            approved = authorize_request(
                request,
                expected_peer_identity="sentinel-reaper",
            )

            self.assertEqual(operation, approved.operation)
            self.assertEqual(
                "sentinel-reaper",
                approved.peer_identity,
            )


if __name__ == "__main__":
    unittest.main()
