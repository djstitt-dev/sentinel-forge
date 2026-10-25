import json,tempfile,unittest
from pathlib import Path
from sentinel_forge.evidence import EvidenceError,EvidenceJournal,REDACTED,UNKNOWN
class EvidenceAssaultTests(unittest.TestCase):
 def e(self,td):
  e=EvidenceJournal(Path(td)/"e");e.append(correlation_id="1",actor="forge");e.append(correlation_id="2",actor="forge");return e
 def test_deleted_first_record_detected(self):
  with tempfile.TemporaryDirectory() as td:
   e=self.e(td);lines=e.path.read_text().splitlines();e.path.write_text(lines[1]+"\n")
   with self.assertRaises(EvidenceError):e.verify()
 def test_deleted_last_record_is_not_intrinsically_detectable(self):
  with tempfile.TemporaryDirectory() as td:
   e=self.e(td);lines=e.path.read_text().splitlines();e.path.write_text(lines[0]+"\n");self.assertEqual(1,len(e.verify()))
 def test_reordered_records_detected(self):
  with tempfile.TemporaryDirectory() as td:
   e=self.e(td);lines=e.path.read_text().splitlines();e.path.write_text("\n".join(reversed(lines))+"\n")
   with self.assertRaises(EvidenceError):e.verify()
 def test_duplicate_record_detected(self):
  with tempfile.TemporaryDirectory() as td:
   e=self.e(td);lines=e.path.read_text().splitlines();e.path.write_text("\n".join(lines+[lines[-1]])+"\n")
   with self.assertRaises(EvidenceError):e.verify()
 def test_extra_field_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   e=self.e(td);lines=e.path.read_text().splitlines();r=json.loads(lines[0]);r["evil"]=1;lines[0]=json.dumps(r);e.path.write_text("\n".join(lines)+"\n")
   with self.assertRaises(EvidenceError):e.verify()
 def test_missing_field_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   e=self.e(td);lines=e.path.read_text().splitlines();r=json.loads(lines[0]);del r["actor"];lines[0]=json.dumps(r);e.path.write_text("\n".join(lines)+"\n")
   with self.assertRaises(EvidenceError):e.verify()
 def test_private_key_text_redacted(self):
  with tempfile.TemporaryDirectory() as td:e=EvidenceJournal(Path(td)/"e");self.assertEqual(REDACTED,e.append(reason="-----BEGIN PRIVATE KEY-----").reason)
 def test_bearer_text_redacted(self):
  with tempfile.TemporaryDirectory() as td:e=EvidenceJournal(Path(td)/"e");self.assertEqual(REDACTED,e.append(reason="Bearer abc").reason)
 def test_password_text_redacted(self):
  with tempfile.TemporaryDirectory() as td:e=EvidenceJournal(Path(td)/"e");self.assertEqual(REDACTED,e.append(reason="password=abc").reason)
 def test_token_text_redacted(self):
  with tempfile.TemporaryDirectory() as td:e=EvidenceJournal(Path(td)/"e");self.assertEqual(REDACTED,e.append(reason="token=abc").reason)
 def test_missing_value_explicit_unknown(self):
  with tempfile.TemporaryDirectory() as td:e=EvidenceJournal(Path(td)/"e");self.assertEqual(UNKNOWN,e.append().actor)
 def test_nested_value_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   e=EvidenceJournal(Path(td)/"e")
   with self.assertRaises(EvidenceError):e.append(reason={"x":1})
