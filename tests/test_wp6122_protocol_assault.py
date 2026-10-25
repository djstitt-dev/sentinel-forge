import unittest
from sentinel_forge.capability import NegotiatedCapabilities,capabilities,negotiate,require_no_downgrade
from sentinel_forge.compatibility import require_compatible,rule_for
from sentinel_forge.enrollment import EnrollmentError
class ProtocolAssaultTests(unittest.TestCase):
 def caps(self,n="peer",p=(1,),s=(1,),f=("ack","anti-replay")):return capabilities(peer_identity=n,protocol_versions=p,schema_versions=s,features=f)
 def neg(self,**kw):
  x=dict(local=self.caps("forge"),remote=self.caps("peer"),expected_peer="peer",minimum_protocol=1,minimum_schema=1,required_features=("ack","anti-replay"));x.update(kw);return negotiate(**x)
 def test_highest_common_protocol_selected(self):self.assertEqual(2,negotiate(self.caps("f",(1,2,3),(1,)),self.caps("p",(1,2),(1,)),expected_peer="p",minimum_protocol=1,minimum_schema=1).protocol_version)
 def test_highest_common_schema_selected(self):self.assertEqual(2,negotiate(self.caps("f",(1,),(1,2,3)),self.caps("p",(1,),(1,2)),expected_peer="p",minimum_protocol=1,minimum_schema=1).schema_version)
 def test_no_protocol_intersection_rejected(self):
  with self.assertRaises(EnrollmentError):negotiate(self.caps("f",(1,),(1,)),self.caps("p",(2,),(1,)),expected_peer="p",minimum_protocol=1,minimum_schema=1)
 def test_no_schema_intersection_rejected(self):
  with self.assertRaises(EnrollmentError):negotiate(self.caps("f",(1,),(1,)),self.caps("p",(1,),(2,)),expected_peer="p",minimum_protocol=1,minimum_schema=1)
 def test_bool_min_protocol_rejected(self):
  with self.assertRaises(EnrollmentError):self.neg(minimum_protocol=True)
 def test_bool_min_schema_rejected(self):
  with self.assertRaises(EnrollmentError):self.neg(minimum_schema=True)
 def test_zero_min_protocol_rejected(self):
  with self.assertRaises(EnrollmentError):self.neg(minimum_protocol=0)
 def test_blank_expected_peer_rejected(self):
  with self.assertRaises(EnrollmentError):self.neg(expected_peer="")
 def test_blank_required_feature_rejected(self):
  with self.assertRaises(EnrollmentError):self.neg(required_features=("ack",""))
 def test_wrong_peer_rejected(self):
  with self.assertRaises(EnrollmentError):self.neg(expected_peer="other")
 def test_missing_required_feature_rejected(self):
  with self.assertRaises(EnrollmentError):self.neg(required_features=("missing",))
 def test_protocol_downgrade_rejected(self):
  with self.assertRaises(EnrollmentError):require_no_downgrade(NegotiatedCapabilities("p",2,1,()),NegotiatedCapabilities("p",1,1,()))
 def test_schema_downgrade_rejected(self):
  with self.assertRaises(EnrollmentError):require_no_downgrade(NegotiatedCapabilities("p",1,2,()),NegotiatedCapabilities("p",1,1,()))
 def test_feature_downgrade_rejected(self):
  with self.assertRaises(EnrollmentError):require_no_downgrade(NegotiatedCapabilities("p",1,1,("a","b")),NegotiatedCapabilities("p",1,1,("a",)))
 def test_peer_change_rejected(self):
  with self.assertRaises(EnrollmentError):require_no_downgrade(NegotiatedCapabilities("a",1,1,()),NegotiatedCapabilities("b",1,1,()))
