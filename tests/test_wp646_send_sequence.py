import multiprocessing,tempfile,unittest
from pathlib import Path
from sentinel_forge.enrollment import EnrollmentError,build_bundle
from sentinel_forge.send_sequence import SendSequenceRegistry
from sentinel_forge.session import derive_session
from sentinel_forge.trust_domain import derive_trust_domain

def setup():
 d=derive_trust_domain(build_bundle(forge_identity="forge",remote_identity="reaper",remote_role="reaper",permitted_actions=["receive"],permitted_target="reaper",policy_reference="p"))
 return d,derive_session(d,generation=1,challenge=b"R"*32)
def worker(path,q):
 d,s=setup()
 try:q.put(("ok",SendSequenceRegistry(Path(path)).reserve(s,d)))
 except Exception as e:q.put(("err",type(e).__name__))

class SendSequenceTests(unittest.TestCase):
 def setUp(self):self.td=tempfile.TemporaryDirectory();self.p=Path(self.td.name)/"s.json";self.r=SendSequenceRegistry(self.p);self.d,self.s=setup()
 def tearDown(self):self.td.cleanup()
 def test_monotonic(self):self.assertEqual([1,2,3],[self.r.reserve(self.s,self.d) for _ in range(3)])
 def test_restart_preserves(self):
  self.assertEqual(1,self.r.reserve(self.s,self.d));self.assertEqual(2,SendSequenceRegistry(self.p).reserve(self.s,self.d))
 def test_new_generation_restarts_at_one(self):
  self.r.reserve(self.s,self.d);s2=derive_session(self.d,generation=2,challenge=b"N"*32)
  self.assertEqual(1,self.r.reserve(s2,self.d))
 def test_stale_generation_rejected(self):
  self.r.reserve(self.s,self.d);s2=derive_session(self.d,generation=2,challenge=b"N"*32);self.r.reserve(s2,self.d)
  with self.assertRaisesRegex(EnrollmentError,"stale"):self.r.reserve(self.s,self.d)
 def test_concurrency_unique(self):
  ctx=multiprocessing.get_context("fork");q=ctx.Queue();ps=[ctx.Process(target=worker,args=(str(self.p),q)) for _ in range(12)]
  [x.start() for x in ps];[x.join() for x in ps];vals=sorted(x[1] for x in [q.get() for _ in ps] if x[0]=="ok")
  self.assertEqual(list(range(1,13)),vals)
