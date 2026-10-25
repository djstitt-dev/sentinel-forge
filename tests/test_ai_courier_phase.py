import os,tempfile,unittest
from pathlib import Path
from sentinel_forge.aes256_gcm import Aes256GcmProvider
from sentinel_forge.ai_engine import ForgeAiEngine,Tool,ToolResult,UnavailableLocalModel
from sentinel_forge.child_bootstrap import build_child_bootstrap,bootstrap_digest
from sentinel_forge.connection_view import view
from sentinel_forge.enrollment import EnrollmentError
from sentinel_forge.ssh_bootstrap import build_ssh_bootstrap_plan

class P:
 provider_id="test-local-model"
 def respond(self,c,ctx):return "response:"+c
class AiCourierPhase(unittest.TestCase):
 def test_aes256_gcm_roundtrip_and_random_nonce(self):
  k=os.urandom(32);p=Aes256GcmProvider(lambda r:k)
  a=p.protect(b"hello",b"context", "child-key")
  b=p.protect(b"hello",b"context", "child-key")
  self.assertNotEqual(a,b);self.assertEqual(b"hello",p.unprotect(a,b"context","child-key"))
 def test_aes_wrong_key_context_and_mutation_fail(self):
  k=os.urandom(32);p=Aes256GcmProvider(lambda r:k)
  x=p.protect(b"hello",b"context","k")
  for q in (
   Aes256GcmProvider(lambda r:os.urandom(32)),
  ):
   with self.assertRaises(EnrollmentError):q.unprotect(x,b"context","k")
  with self.assertRaises(EnrollmentError):p.unprotect(x,b"wrong","k")
  y=bytearray(x);y[-1]^=1
  with self.assertRaises(EnrollmentError):p.unprotect(bytes(y),b"context","k")
 def test_aes_rejects_non_256_key(self):
  for n in (0,16,24,31,33,64):
   with self.assertRaises(EnrollmentError):Aes256GcmProvider(lambda r,n=n:b"x"*n).protect(b"x",b"ad","k")
 def test_child_bootstrap_is_target_bound(self):
  b=build_child_bootstrap(child_identity="reaper",endpoint="reaper.local",enrollment_id="e1",challenge_id="c1",artifact_digest="sha256:"+"a"*64)
  d=bootstrap_digest(b)
  b2=build_child_bootstrap(child_identity="scribe",endpoint="reaper.local",enrollment_id="e1",challenge_id="c1",artifact_digest="sha256:"+"a"*64)
  self.assertNotEqual(d,bootstrap_digest(b2));self.assertEqual("Sentinel Courier connected to Forge.",b.notification)
 def test_ssh_plan_is_argv_not_shell(self):
  p=build_ssh_bootstrap_plan(child_identity="reaper",host="10.0.0.2",user="courier",port=22,known_hosts="/etc/sentinel/known_hosts",local_artifact="/tmp/a.tgz")
  self.assertIsInstance(p.copy_argv,tuple);self.assertNotIn("sh",p.copy_argv);self.assertIn("StrictHostKeyChecking=yes",p.copy_argv)
 def test_ssh_rejects_bad_port_and_relative_paths(self):
  with self.assertRaises(EnrollmentError):build_ssh_bootstrap_plan(child_identity="x",host="h",user="u",port=True,known_hosts="/k",local_artifact="/a")
  with self.assertRaises(EnrollmentError):build_ssh_bootstrap_plan(child_identity="x",host="h",user="u",port=22,known_hosts="/k",local_artifact="a")
 def test_ai_responds_but_model_is_not_authority(self):
  e=ForgeAiEngine(P());self.assertEqual("response:status",e.ask("status").response)
 def test_ai_mutating_tool_requires_operator(self):
  t=Tool("fix",lambda a:ToolResult("fix",True,"fixed"),mutating=True);e=ForgeAiEngine(P(),[t])
  with self.assertRaises(EnrollmentError):e.execute_tool("fix",{},operator_approved=False)
  self.assertTrue(e.execute_tool("fix",{},operator_approved=True).ok)
 def test_unallowlisted_tool_rejected(self):
  with self.assertRaises(EnrollmentError):ForgeAiEngine(P()).execute_tool("shell",{},operator_approved=True)
 def test_local_model_absence_is_explicit(self):
  with self.assertRaisesRegex(EnrollmentError,"not installed"):ForgeAiEngine(UnavailableLocalModel()).ask("hello")
 def test_active_visual_requires_protection(self):
  with self.assertRaises(EnrollmentError):view(child_identity="reaper",state="ACTIVE",protected=False)
  s=view(child_identity="reaper",state="ACTIVE",protected=True).render()
  self.assertIn("AES-256-GCM",s);self.assertIn("ACTIVE",s)
from types import SimpleNamespace
from sentinel_forge.child_callback import ExpectedChild,ChildCallback,accept_callback
from sentinel_forge.local_model import LocalExecutableModel,LocalModelConfig
from sentinel_forge.ssh_bootstrap_exec import execute_bootstrap
class ExecutionAndCallback(unittest.TestCase):
 def test_callback_exact_binding(self):
  e=ExpectedChild("reaper","e1","c1","key1")
  self.assertTrue(accept_callback(e,ChildCallback("reaper","e1","c1","key1",True)).accepted)
  for c in (ChildCallback("scribe","e1","c1","key1",True),ChildCallback("reaper","e2","c1","key1",True),ChildCallback("reaper","e1","c2","key1",True),ChildCallback("reaper","e1","c1","key2",True),ChildCallback("reaper","e1","c1","key1",False)):
   with self.assertRaises(EnrollmentError):accept_callback(e,c)
 def test_callback_revocation_kills(self):
  with self.assertRaises(EnrollmentError):accept_callback(ExpectedChild("r","e","c","k"),ChildCallback("r","e","c","k",True),revoked=True)
 def test_ssh_execution_born_blocked(self):
  p=build_ssh_bootstrap_plan(child_identity="r",host="h",user="u",port=22,known_hosts="/k",local_artifact="/a")
  with self.assertRaises(EnrollmentError):execute_bootstrap(p,operator_approved=False,runner=lambda *a,**k:None)
 def test_ssh_exec_copy_failure_stops_install(self):
  p=build_ssh_bootstrap_plan(child_identity="r",host="h",user="u",port=22,known_hosts="/k",local_artifact="/a");calls=[]
  def run(argv,**kw):calls.append(argv);return SimpleNamespace(returncode=1,stdout="",stderr="")
  r=execute_bootstrap(p,operator_approved=True,runner=run);self.assertFalse(r.copied);self.assertEqual(1,len(calls))
 def test_ssh_exec_uses_shell_false(self):
  p=build_ssh_bootstrap_plan(child_identity="r",host="h",user="u",port=22,known_hosts="/k",local_artifact="/a");seen=[]
  def run(argv,**kw):seen.append((argv,kw));return SimpleNamespace(returncode=0,stdout="",stderr="")
  r=execute_bootstrap(p,operator_approved=True,runner=run);self.assertTrue(r.installed);self.assertEqual(2,len(seen));self.assertTrue(all(x[1]["shell"] is False for x in seen))
 def test_local_model_adapter_no_shell_and_prompt(self):
  seen=[]
  def run(argv,**kw):seen.append((argv,kw));return SimpleNamespace(returncode=0,stdout="answer",stderr="")
  m=LocalExecutableModel(LocalModelConfig("/usr/bin/fake-model","/models/m.gguf"),runner=run)
  self.assertEqual("answer",m.respond("fix it","ctx"));self.assertFalse(seen[0][1]["shell"]);self.assertIn("fix it",seen[0][0][7]);self.assertIn("--single-turn",seen[0][0]);self.assertIn("--simple-io",seen[0][0]);self.assertIn("/no_think",seen[0][0][7])
 def test_local_model_strips_llama_cli_transcript(self):
  noisy="Loading model...\n> /no_think\nSYSTEM: x\nASSISTANT:\n\nclean answer\n\n[ Prompt: 10.0 t/s | Generation: 5.0 t/s ]\n\nExiting...\n"
  def run(argv,**kw):return SimpleNamespace(returncode=0,stdout=noisy,stderr="")
  m=LocalExecutableModel(LocalModelConfig("/x","/m"),runner=run)
  self.assertEqual("clean answer",m.respond("x",""))
 def test_local_model_failure_closed(self):
  def run(argv,**kw):return SimpleNamespace(returncode=2,stdout="",stderr="bad")
  with self.assertRaises(EnrollmentError):LocalExecutableModel(LocalModelConfig("/x","/m"),runner=run).respond("x","")
from sentinel_forge.ai_courier_completion import AI_ENGINE,CHILD_ENGINE,assess
class PhaseCompletionTests(unittest.TestCase):
 def test_engineering_complete_does_not_invent_operation(self):
  r=assess(ai_facts={x:True for x in AI_ENGINE},child_facts={x:True for x in CHILD_ENGINE},local_model_operational=False,live_child_operational=False)
  self.assertTrue(r.ai_engine_complete);self.assertTrue(r.child_engine_complete)
  self.assertFalse(r.local_model_operational);self.assertFalse(r.live_child_operational)
  self.assertIn("LOCAL_MODEL_NOT_OPERATIONAL",r.blockers);self.assertIn("LIVE_CHILD_NOT_OPERATIONAL",r.blockers)
 def test_malformed_completion_facts_fail(self):
  with self.assertRaises(EnrollmentError):assess(ai_facts={},child_facts={x:True for x in CHILD_ENGINE},local_model_operational=False,live_child_operational=False)
