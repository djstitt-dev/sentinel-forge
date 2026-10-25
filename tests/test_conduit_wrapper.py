import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "scripts" / "sentinel-conduit-gate"


class ConduitWrapperProcessTests(unittest.TestCase):

    def run_gate(self, command=None):
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT)

        if command is None:
            env.pop("SSH_ORIGINAL_COMMAND", None)
        else:
            env["SSH_ORIGINAL_COMMAND"] = command

        return subprocess.run(
            [str(WRAPPER)],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
            shell=False,
        )

    def payload(self, result):
        self.assertEqual("", result.stderr)
        lines = result.stdout.splitlines()
        self.assertEqual(1, len(lines))
        return json.loads(lines[0])

    def test_status_process_contract(self):
        result = self.run_gate(
            "sentinel-conduit status --peer sentinel-reaper"
        )

        self.assertEqual(0, result.returncode)

        payload = self.payload(result)

        self.assertEqual(
            "sentinel-conduit-response-v1",
            payload["format"],
        )
        self.assertEqual("status", payload["operation"])
        self.assertEqual("sentinel-reaper", payload["peer_identity"])
        self.assertEqual("OK", payload["result"])
        self.assertTrue(payload["hostname"])

    def test_capabilities_process_contract(self):
        result = self.run_gate(
            "sentinel-conduit capabilities --peer sentinel-reaper"
        )

        self.assertEqual(0, result.returncode)

        payload = self.payload(result)

        self.assertEqual(
            ["status", "capabilities"],
            payload["capabilities"],
        )
        self.assertEqual("OK", payload["result"])

    def test_missing_original_command_denied(self):
        result = self.run_gate()

        self.assertEqual(77, result.returncode)

        payload = self.payload(result)

        self.assertEqual("DENIED", payload["result"])
        self.assertNotIn("operation", payload)

    def test_wrong_peer_denied(self):
        result = self.run_gate(
            "sentinel-conduit status --peer sentinel-scribe"
        )

        self.assertEqual(77, result.returncode)
        self.assertEqual("DENIED", self.payload(result)["result"])

    def test_shell_request_denied_without_effect(self):
        with tempfile.TemporaryDirectory() as td:
            marker = Path(td) / "SHOULD_NOT_EXIST"

            command = (
                "sentinel-conduit status --peer sentinel-reaper; "
                f"touch {marker}"
            )

            result = self.run_gate(command)

            self.assertEqual(77, result.returncode)
            self.assertFalse(marker.exists())
            self.assertEqual(
                "DENIED",
                self.payload(result)["result"],
            )

    def test_command_substitution_denied_without_effect(self):
        with tempfile.TemporaryDirectory() as td:
            marker = Path(td) / "SHOULD_NOT_EXIST"

            command = (
                "sentinel-conduit status --peer "
                f"$(touch {marker})"
            )

            result = self.run_gate(command)

            self.assertEqual(77, result.returncode)
            self.assertFalse(marker.exists())

    def test_environment_cannot_change_peer_binding(self):
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT)
        env["SSH_ORIGINAL_COMMAND"] = (
            "sentinel-conduit status --peer sentinel-scribe"
        )
        env["EXPECTED_PEER_IDENTITY"] = "sentinel-scribe"

        result = subprocess.run(
            [str(WRAPPER)],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
            shell=False,
        )

        self.assertEqual(77, result.returncode)
        self.assertEqual("DENIED", self.payload(result)["result"])


if __name__ == "__main__":
    unittest.main()
