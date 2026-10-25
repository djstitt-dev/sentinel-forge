import random,struct,tempfile,unittest
from pathlib import Path
from sentinel_forge.enrollment import EnrollmentError
from sentinel_forge.framing import frame,unframe,HEADER,MAGIC,VERSION,TYPE_PROTECTED,MAX_PROTECTED_BYTES
from sentinel_forge.courier_queue_v2 import IntentCourierQueue
from sentinel_forge.delivery_intent import build_delivery_intent
class ResourceParserMatrix(unittest.TestCase):
 def test_200_declared_lengths_fail_closed(self):
  good=frame(b"x"*32);rng=random.Random(7100)
  for _ in range(200):
   n=rng.randrange(0,2**32);m=bytearray(good);m[6:10]=struct.pack(">I",n)
   if n==32:continue
   with self.subTest(n=n):
    with self.assertRaises(EnrollmentError):unframe(bytes(m))
 def test_100_random_magic_values_rejected(self):
  good=frame(b"x");rng=random.Random(7101)
  for _ in range(100):
   m=bytearray(good);magic=bytes(rng.randrange(256) for _ in range(4))
   if magic==MAGIC:continue
   m[:4]=magic
   with self.assertRaises(EnrollmentError):unframe(bytes(m))
 def test_100_queue_identity_lengths(self):
  with tempfile.TemporaryDirectory() as td:
   q=IntentCourierQueue(Path(td)/"q")
   for n in range(1,101):
    a="sha256:"+("a"*n);i=build_delivery_intent(correlation_id=f"c{n}",relationship_id="r",artifact_identity=a,operation="d",authorization_reference="auth")
    self.assertTrue(q.enqueue(intent=i,payload_identity=a).startswith("queue2:"))
 def test_queue_capacity_counts_only_nonterminal(self):
  with tempfile.TemporaryDirectory() as td:
   q=IntentCourierQueue(Path(td)/"q")
   for n in range(50):
    a="sha256:a";i=build_delivery_intent(correlation_id=f"c{n}",relationship_id="r",artifact_identity=a,operation="d",authorization_reference="auth");item=q.enqueue(intent=i,payload_identity=a);q.transition(item,expected="QUEUED",new="CANCELLED")
   self.assertEqual([],q.pending("r"))
