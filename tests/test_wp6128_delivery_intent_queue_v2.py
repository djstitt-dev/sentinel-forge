import json,multiprocessing as mp,os,stat,tempfile,unittest
from pathlib import Path
from sentinel_forge.courier_queue_v2 import IntentCourierQueue
from sentinel_forge.delivery_intent import build_delivery_intent
from sentinel_forge.enrollment import EnrollmentError

def intent(c="c1",a="sha256:a",auth="auth",rel="rel",op="deliver"):
 return build_delivery_intent(correlation_id=c,relationship_id=rel,artifact_identity=a,operation=op,authorization_reference=auth)
def worker(path,q):
 try:q.put(("OK",IntentCourierQueue(Path(path)).enqueue(intent=intent(),payload_identity="sha256:a")))
 except Exception as e:q.put((type(e).__name__,str(e)))

class QueueV2Tests(unittest.TestCase):
 def test_exact_intent_replay_converges(self):
  with tempfile.TemporaryDirectory() as td:
   q=IntentCourierQueue(Path(td)/"q");self.assertEqual(q.enqueue(intent=intent(),payload_identity="sha256:a"),q.enqueue(intent=intent(),payload_identity="sha256:a"))
 def test_new_correlation_is_new_delivery(self):
  with tempfile.TemporaryDirectory() as td:
   q=IntentCourierQueue(Path(td)/"q");self.assertNotEqual(q.enqueue(intent=intent("c1"),payload_identity="sha256:a"),q.enqueue(intent=intent("c2"),payload_identity="sha256:a"))
 def test_new_authorization_is_new_delivery(self):
  with tempfile.TemporaryDirectory() as td:
   q=IntentCourierQueue(Path(td)/"q");a=q.enqueue(intent=intent("c1",auth="a1"),payload_identity="sha256:a")
   with self.assertRaisesRegex(EnrollmentError,"correlation conflict"):q.enqueue(intent=intent("c1",auth="a2"),payload_identity="sha256:a")
 def test_payload_must_equal_intent_artifact(self):
  with tempfile.TemporaryDirectory() as td:
   with self.assertRaises(EnrollmentError):IntentCourierQueue(Path(td)/"q").enqueue(intent=intent(),payload_identity="sha256:b")
 def test_file_is_owner_only(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"q";IntentCourierQueue(p);self.assertEqual(0o600,stat.S_IMODE(p.stat().st_mode))
 def test_concurrent_exact_enqueue_converges(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"q";IntentCourierQueue(p);ctx=mp.get_context("spawn");out=ctx.Queue();ps=[ctx.Process(target=worker,args=(str(p),out)) for _ in range(8)]
   [x.start() for x in ps];[x.join(10) for x in ps];rows=[out.get(timeout=2) for _ in ps]
   self.assertTrue(all(x[0]=="OK" for x in rows),rows);self.assertEqual(1,len({x[1] for x in rows}))
 def test_v1_file_is_not_silently_reinterpreted(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"q";p.write_text('{"x":{"format":"sentinel-courier-outbound-queue-v1"}}')
   with self.assertRaises(EnrollmentError):IntentCourierQueue(p)
 def test_transition_rules_preserved(self):
  with tempfile.TemporaryDirectory() as td:
   q=IntentCourierQueue(Path(td)/"q");i=q.enqueue(intent=intent(),payload_identity="sha256:a");q.transition(i,expected="QUEUED",new="PREPARED",sequence=1);q.transition(i,expected="PREPARED",new="IN_FLIGHT",sequence=1)
   q.transition(i,expected="IN_FLIGHT",new="ACKNOWLEDGED",sequence=1,acknowledgement="ack");self.assertEqual("ACKNOWLEDGED",q.get(i)["state"])
 def test_sequence_immutable(self):
  with tempfile.TemporaryDirectory() as td:
   q=IntentCourierQueue(Path(td)/"q");i=q.enqueue(intent=intent(),payload_identity="sha256:a");q.transition(i,expected="QUEUED",new="PREPARED",sequence=1)
   with self.assertRaises(EnrollmentError):q.transition(i,expected="PREPARED",new="IN_FLIGHT",sequence=2)
 def test_embedded_intent_mutations_fail_even_if_queue_id_recomputed(self):
  from sentinel_forge.courier_queue_v2 import _sha
  fields=("delivery_id","correlation_id","intent_digest","authorization_reference","relationship_id","artifact_identity","operation")
  for field in fields:
   with self.subTest(field=field),tempfile.TemporaryDirectory() as td:
    p=Path(td)/"q";q=IntentCourierQueue(p);item=q.enqueue(intent=intent(),payload_identity="sha256:a");db=json.loads(p.read_text());r=db.pop(item);r[field]+="x"
    if field=="artifact_identity":r["payload_identity"]=r[field]
    core={n:r[n] for n in ("format","delivery_id","correlation_id","intent_digest","authorization_reference","relationship_id","artifact_identity","operation","payload_identity")}
    new="queue2:"+_sha(core);r["item_id"]=new;db[new]=r;p.write_text(json.dumps(db))
    with self.assertRaises(EnrollmentError):IntentCourierQueue(p)
