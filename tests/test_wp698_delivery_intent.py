import dataclasses,unittest
from sentinel_forge.delivery_intent import build_delivery_intent,verify_delivery_intent
from sentinel_forge.enrollment import EnrollmentError
class DeliveryIntentTests(unittest.TestCase):
 def make(self,c="corr-1"):return build_delivery_intent(correlation_id=c,relationship_id="rel",artifact_identity="sha256:a",operation="deliver",authorization_reference="auth")
 def test_exact_rebuild_converges(self):self.assertEqual(self.make(),self.make())
 def test_same_artifact_new_correlation_is_new_delivery(self):self.assertNotEqual(self.make("corr-1").delivery_id,self.make("corr-2").delivery_id)
 def test_same_correlation_changed_artifact_is_not_replay(self):
  a=self.make();b=build_delivery_intent(correlation_id="corr-1",relationship_id="rel",artifact_identity="sha256:b",operation="deliver",authorization_reference="auth");self.assertNotEqual(a.delivery_id,b.delivery_id)
 def test_exact_bindings_verify(self):verify_delivery_intent(self.make(),correlation_id="corr-1",relationship_id="rel",artifact_identity="sha256:a")
 def test_mutation_rejected(self):
  a=self.make()
  for f in ("delivery_id","correlation_id","relationship_id","artifact_identity","operation","authorization_reference","intent_digest"):
   with self.subTest(f=f):
    with self.assertRaises(EnrollmentError):verify_delivery_intent(dataclasses.replace(a,**{f:getattr(a,f)+"x"}))
 def test_blank_fields_rejected(self):
  for k in ("correlation_id","relationship_id","artifact_identity","operation","authorization_reference"):
   with self.subTest(k=k):
    x=dict(correlation_id="c",relationship_id="r",artifact_identity="a",operation="d",authorization_reference="z");x[k]=""
    with self.assertRaises(EnrollmentError):build_delivery_intent(**x)
