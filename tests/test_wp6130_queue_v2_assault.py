import json,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from sentinel_forge.courier_queue_v2 import IntentCourierQueue,_sha
from sentinel_forge.delivery_intent import build_delivery_intent
from sentinel_forge.enrollment import EnrollmentError

FIELDS=("delivery_id","correlation_id","intent_digest","authorization_reference","relationship_id","artifact_identity","operation","payload_identity")
STATES=("QUEUED","PREPARED","IN_FLIGHT","OUTCOME_UNKNOWN","ACKNOWLEDGED","REJECTED","CANCELLED")
LEGAL={("QUEUED","PREPARED"),("PREPARED","IN_FLIGHT"),("IN_FLIGHT","ACKNOWLEDGED"),("IN_FLIGHT","REJECTED"),("IN_FLIGHT","OUTCOME_UNKNOWN"),("OUTCOME_UNKNOWN","ACKNOWLEDGED"),("OUTCOME_UNKNOWN","REJECTED"),("QUEUED","CANCELLED")}

def make_intent(c="c"):return build_delivery_intent(correlation_id=c,relationship_id="rel",artifact_identity="sha256:a",operation="deliver",authorization_reference="auth")
def resign(r):
 core={n:r[n] for n in ("format","delivery_id","correlation_id","intent_digest","authorization_reference","relationship_id","artifact_identity","operation","payload_identity")}
 return "queue2:"+_sha(core)
class QueueV2Assault(unittest.TestCase):
 def setupq(self):
  td=tempfile.TemporaryDirectory();p=Path(td.name)/"q";q=IntentCourierQueue(p);i=q.enqueue(intent=make_intent(),payload_identity="sha256:a");return td,p,q,i
 def test_symlink_authority_file_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   r=Path(td);target=r/"target";target.write_text("{}");link=r/"q";link.symlink_to(target)
   with self.assertRaises(OSError):IntentCourierQueue(link)
 def test_replace_failure_does_not_claim_enqueue(self):
  with tempfile.TemporaryDirectory() as td:
   q=IntentCourierQueue(Path(td)/"q")
   with patch("sentinel_forge.courier_queue_v2.os.replace",side_effect=OSError("disk")):
    with self.assertRaises(OSError):q.enqueue(intent=make_intent(),payload_identity="sha256:a")
   self.assertEqual([],q.pending("rel"))
 def test_file_fsync_failure_not_success(self):
  with tempfile.TemporaryDirectory() as td:
   q=IntentCourierQueue(Path(td)/"q")
   with patch("sentinel_forge.courier_queue_v2.os.fsync",side_effect=OSError("fsync")):
    with self.assertRaises(OSError):q.enqueue(intent=make_intent(),payload_identity="sha256:a")
 def test_restart_preserves_exact_identity(self):
  td,p,q,i=self.setupq()
  try:self.assertEqual(i,IntentCourierQueue(p).enqueue(intent=make_intent(),payload_identity="sha256:a"))
  finally:td.cleanup()
 def test_truncated_json_rejected(self):
  td,p,q,i=self.setupq()
  try:p.write_text("{");self.assertRaises(EnrollmentError,IntentCourierQueue,p)
  finally:td.cleanup()
 def test_extra_field_rejected(self):
  td,p,q,i=self.setupq()
  try:d=json.loads(p.read_text());d[i]["extra"]=1;p.write_text(json.dumps(d));self.assertRaises(EnrollmentError,IntentCourierQueue,p)
  finally:td.cleanup()
 def test_wrong_format_rejected(self):
  td,p,q,i=self.setupq()
  try:d=json.loads(p.read_text());d[i]["format"]="v3";p.write_text(json.dumps(d));self.assertRaises(EnrollmentError,IntentCourierQueue,p)
  finally:td.cleanup()
 def test_bool_sequence_rejected(self):
  td,p,q,i=self.setupq()
  try:d=json.loads(p.read_text());d[i]["state"]="PREPARED";d[i]["sequence"]=True;p.write_text(json.dumps(d));self.assertRaises(EnrollmentError,IntentCourierQueue,p)
  finally:td.cleanup()
 def test_ack_in_wrong_state_rejected(self):
  td,p,q,i=self.setupq()
  try:d=json.loads(p.read_text());d[i]["acknowledgement"]="ack";p.write_text(json.dumps(d));self.assertRaises(EnrollmentError,IntentCourierQueue,p)
  finally:td.cleanup()
 def test_acknowledged_without_ack_rejected(self):
  td,p,q,i=self.setupq()
  try:d=json.loads(p.read_text());d[i]["state"]="ACKNOWLEDGED";d[i]["sequence"]=1;p.write_text(json.dumps(d));self.assertRaises(EnrollmentError,IntentCourierQueue,p)
  finally:td.cleanup()
 def test_cancelled_with_sequence_rejected(self):
  td,p,q,i=self.setupq()
  try:d=json.loads(p.read_text());d[i]["state"]="CANCELLED";d[i]["sequence"]=1;p.write_text(json.dumps(d));self.assertRaises(EnrollmentError,IntentCourierQueue,p)
  finally:td.cleanup()
 def test_duplicate_correlation_persisted_rejected(self):
  td,p,q,i=self.setupq()
  try:
   d=json.loads(p.read_text());r=dict(d[i]);r["correlation_id"]="other";r["delivery_id"]="delivery:bad";r["intent_digest"]="sha256:bad"
   # malformed embedded intent is independently rejected before duplicate ambiguity can become authority.
   n=resign(r);r["item_id"]=n;d[n]=r;p.write_text(json.dumps(d));self.assertRaises(EnrollmentError,IntentCourierQueue,p)
  finally:td.cleanup()
 def test_all_illegal_direct_transitions_rejected(self):
  for a in STATES:
   for b in STATES:
    if (a,b) in LEGAL:continue
    with self.subTest(a=a,b=b),tempfile.TemporaryDirectory() as td:
     q=IntentCourierQueue(Path(td)/"q");i=q.enqueue(intent=make_intent(),payload_identity="sha256:a")
     with self.assertRaises(EnrollmentError):q.transition(i,expected=a,new=b,sequence=1,acknowledgement="ack")
def _mutation(field):
 def t(self):
  td,p,q,i=self.setupq()
  try:
   d=json.loads(p.read_text());r=d.pop(i);r[field]=r[field]+"x"
   if field=="artifact_identity":r["payload_identity"]=r[field]
   n=resign(r);r["item_id"]=n;d[n]=r;p.write_text(json.dumps(d))
   with self.assertRaises(EnrollmentError):IntentCourierQueue(p)
  finally:td.cleanup()
 return t
for _f in FIELDS:
 if _f!="payload_identity":setattr(QueueV2Assault,"test_persisted_mutation_"+_f,_mutation(_f))
