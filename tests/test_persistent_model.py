import unittest

from sentinel_forge.enrollment import EnrollmentError
from sentinel_forge.persistent_model import PersistentLocalModel, PersistentModelConfig


class PersistentModelTests(unittest.TestCase):
    def test_non_loopback_binding_rejected(self):
        with self.assertRaises(EnrollmentError):
            PersistentLocalModel(PersistentModelConfig("/usr/bin/x", "/models/m.gguf", host="0.0.0.0"))

    def test_bad_port_rejected(self):
        with self.assertRaises(EnrollmentError):
            PersistentLocalModel(PersistentModelConfig("/usr/bin/x", "/models/m.gguf", port=80))

    def test_provider_identity_is_persistent(self):
        m = PersistentLocalModel(PersistentModelConfig("/usr/bin/x", "/models/m.gguf"))
        self.assertEqual("sentinel-local-persistent-model-v1", m.provider_id)
        self.assertEqual("http://127.0.0.1:18081", m.base_url)


if __name__ == "__main__":
    unittest.main()
