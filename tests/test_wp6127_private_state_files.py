import os,stat,tempfile,unittest
from pathlib import Path
from sentinel_forge.courier_effects import DurableEffectCoordinator
from sentinel_forge.courier_queue import CourierQueue
from sentinel_forge.courier_sqlite import SQLiteDisconnectedCourier
from sentinel_forge.evidence import EvidenceJournal
from sentinel_forge.recovery_intent import RecoveryIntentLedger
from sentinel_forge.secure_io import private_open
from sentinel_forge.transition_intent import TransitionIntentLedger
class PrivateStateFileTests(unittest.TestCase):
 def mode(self,p):return stat.S_IMODE(Path(p).stat().st_mode)
 def test_authority_json_and_journal_files_are_0600(self):
  with tempfile.TemporaryDirectory() as td:
   r=Path(td);q=CourierQueue(r/"q");q.enqueue(relationship_id="r",artifact_identity="a",operation="o",payload_identity="p")
   t=TransitionIntentLedger(r/"t");t.prepare(enrollment_id="e",remote_identity="r",from_state=None,to_state="STAGED",authorization_reference="a",reason="x")
   x=RecoveryIntentLedger(r/"x");x.prepare(plan_digest="p",target="t",observation_digest="o");e=EvidenceJournal(r/"e");e.append(correlation_id="c")
   for p in (r/"q",r/"t",r/"x",r/"e"):self.assertEqual(0o600,self.mode(p),p)
 def test_sqlite_authority_files_are_0600(self):
  with tempfile.TemporaryDirectory() as td:
   r=Path(td);SQLiteDisconnectedCourier(r/"c.db");DurableEffectCoordinator(r/"e.db")
   self.assertEqual(0o600,self.mode(r/"c.db"));self.assertEqual(0o600,self.mode(r/"e.db"))
 def test_private_open_restricts_preexisting_permissive_file(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"x";p.write_text("old");os.chmod(p,0o666)
   with private_open(p,"wb") as f:f.write(b"new")
   self.assertEqual(0o600,self.mode(p));self.assertEqual(b"new",p.read_bytes())
 def test_private_open_refuses_symlink(self):
  with tempfile.TemporaryDirectory() as td:
   r=Path(td);target=r/"target";target.write_text("safe");link=r/"link";link.symlink_to(target)
   with self.assertRaises(OSError):
    with private_open(link,"wb") as f:f.write(b"evil")
   self.assertEqual("safe",target.read_text())
