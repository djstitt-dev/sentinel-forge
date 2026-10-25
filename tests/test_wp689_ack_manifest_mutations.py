import dataclasses,unittest
from sentinel_forge.courier_ack import build_ack,verify_ack
from sentinel_forge.courier_manifest import build_manifest,verify_manifest
from sentinel_forge.enrollment import EnrollmentError
from sentinel_forge.transport_contract import TransportMessageContext

class AckManifestMutationTests(unittest.TestCase):
 def setUp(self):
  self.ctx=TransportMessageContext("sentinel-transport-message-context-v1","rel","session:1",1,1,"k","cb","ph","ctx")
  self.ack=build_ack(self.ctx,sequence=1,operation="deliver",artifact_identity="a",disposition="ACCEPTED",reason="ok")
  self.m=build_manifest(relationship_id="rel",sender_identity="forge",recipient_identity="reaper",operation="deliver",classification="CONTROLLED",artifact_identity="a",payload_identity="a",policy_reference="p")
 def test_each_ack_binding_mutation_rejected(self):
  fields=("relationship_id","session_id","operation","artifact_identity","transport_context_digest","reason","acknowledgement_digest")
  for f in fields:
   with self.subTest(f=f):
    bad=dataclasses.replace(self.ack,**{f:getattr(self.ack,f)+"x"})
    with self.assertRaises(EnrollmentError):verify_ack(bad,self.ctx,sequence=1,operation="deliver",artifact_identity="a")
 def test_each_ack_numeric_mutation_rejected(self):
  for f in ("session_generation","credential_generation","sequence"):
   with self.subTest(f=f):
    bad=dataclasses.replace(self.ack,**{f:getattr(self.ack,f)+1})
    with self.assertRaises(EnrollmentError):verify_ack(bad,self.ctx,sequence=1,operation="deliver",artifact_identity="a")
 def test_ack_disposition_mutation_rejected(self):
  bad=dataclasses.replace(self.ack,disposition="UNKNOWN")
  with self.assertRaises(EnrollmentError):verify_ack(bad,self.ctx,sequence=1,operation="deliver",artifact_identity="a")
 def test_each_manifest_binding_mutation_rejected(self):
  fields=("relationship_id","sender_identity","recipient_identity","operation","classification","artifact_identity","payload_identity","policy_reference","manifest_digest")
  for f in fields:
   with self.subTest(f=f):
    bad=dataclasses.replace(self.m,**{f:getattr(self.m,f)+"x"})
    with self.assertRaises(EnrollmentError):verify_manifest(bad,relationship_id="rel",sender_identity="forge",recipient_identity="reaper",operation="deliver",classification="CONTROLLED",artifact_identity="a",payload_identity="a",policy_reference="p")
