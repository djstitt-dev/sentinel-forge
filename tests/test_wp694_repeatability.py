import subprocess,sys,unittest
class RepeatabilityTests(unittest.TestCase):
 def runmod(self,name):
  return subprocess.run([sys.executable,"-m","unittest",name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode
 def test_send_sequence_concurrency_repeats_cleanly(self):
  for _ in range(3):self.assertEqual(0,self.runmod("tests.test_wp646_send_sequence.SendSequenceTests.test_concurrency_unique"))
 def test_replay_concurrency_repeats_cleanly(self):
  for _ in range(3):self.assertEqual(0,self.runmod("tests.test_wp626_session_antireplay.ReplayRegistryConcurrencyTests"))
 def test_credential_registry_concurrency_repeats_cleanly(self):
  for _ in range(3):self.assertEqual(0,self.runmod("tests.test_wp630_credential_registry.CredentialRegistryConcurrencyTests"))
 def test_enrollment_registry_concurrency_repeats_cleanly(self):
  for _ in range(3):self.assertEqual(0,self.runmod("tests.test_wp612_courier_enrollment.EnrollmentRegistryConcurrencyTests"))
