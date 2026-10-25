import tempfile,unittest
from pathlib import Path
from sentinel_forge.evidence import EvidenceError,EvidenceJournal
class EvidenceFieldSafety(unittest.TestCase):
 def reject(self,key):
  with tempfile.TemporaryDirectory() as td:
   e=EvidenceJournal(Path(td)/"e")
   with self.assertRaises(EvidenceError):e.append(**{key:"x"})
 def test_secret_key_rejected(self):self.reject("secret")
 def test_password_key_rejected(self):self.reject("password")
 def test_token_key_rejected(self):self.reject("token")
 def test_credential_key_rejected(self):self.reject("credential")
 def test_private_key_key_rejected(self):self.reject("private_key")
 def test_api_key_rejected(self):self.reject("api_key")
 def test_integer_scalar_canonicalized(self):
  with tempfile.TemporaryDirectory() as td:self.assertEqual("42",EvidenceJournal(Path(td)/"e").append(reason=42).reason)
 def test_boolean_scalar_canonicalized(self):
  with tempfile.TemporaryDirectory() as td:self.assertEqual("True",EvidenceJournal(Path(td)/"e").append(reason=True).reason)
 def test_float_scalar_canonicalized(self):
  with tempfile.TemporaryDirectory() as td:self.assertEqual("1.5",EvidenceJournal(Path(td)/"e").append(reason=1.5).reason)
