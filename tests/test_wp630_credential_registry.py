import dataclasses,json,multiprocessing,tempfile,unittest
from pathlib import Path
from sentinel_forge.credential_reference import build_credential_reference
from sentinel_forge.credential_registry import CredentialReferenceRegistry
from sentinel_forge.enrollment import EnrollmentError,build_bundle
from sentinel_forge.trust_domain import derive_trust_domain

def domain(peer="sentinel-reaper",role="reaper"):
 return derive_trust_domain(build_bundle(forge_identity="sentinel-forge",remote_identity=peer,remote_role=role,
  permitted_actions=["receive"],permitted_target=peer,policy_reference="policy:v1"))

def ref(d,g,key=None):return build_credential_reference(d,generation=g,key_reference=key or f"credential:{d.peer_identity}:g{g}")

def register_worker(path,q):
 d=domain()
 try:
  CredentialReferenceRegistry(Path(path)).register_initial(d,ref(d,1));q.put("OK")
 except Exception as e:q.put(type(e).__name__+":"+str(e))

def rotate_worker(path,key,q):
 d=domain()
 try:
  CredentialReferenceRegistry(Path(path)).rotate(d,ref(d,2,key));q.put("OK:"+key)
 except Exception as e:q.put(type(e).__name__+":"+str(e))

class CredentialRegistryTests(unittest.TestCase):
 def setUp(self):self.td=tempfile.TemporaryDirectory();self.p=Path(self.td.name)/"credentials.json";self.d=domain();self.r=CredentialReferenceRegistry(self.p)
 def tearDown(self):self.td.cleanup()
 def test_initial_generation_one_and_current(self):
  a=ref(self.d,1);self.r.register_initial(self.d,a);self.assertEqual(a,self.r.current(self.d))
 def test_initial_generation_other_than_one_rejected(self):
  with self.assertRaisesRegex(EnrollmentError,"generation must be one"):self.r.register_initial(self.d,ref(self.d,2))
 def test_duplicate_initial_registration_rejected(self):
  self.r.register_initial(self.d,ref(self.d,1))
  with self.assertRaises(EnrollmentError):self.r.register_initial(self.d,ref(self.d,1))
 def test_rotation_exactly_one_and_new_reference(self):
  a=ref(self.d,1);b=ref(self.d,2);self.r.register_initial(self.d,a);self.r.rotate(self.d,b);self.assertEqual(b,self.r.current(self.d))
  with self.assertRaises(EnrollmentError):self.r.rotate(self.d,ref(self.d,4))
 def test_old_reference_is_stale_after_rotation(self):
  a=ref(self.d,1);b=ref(self.d,2);self.r.register_initial(self.d,a);self.r.rotate(self.d,b)
  with self.assertRaisesRegex(EnrollmentError,"stale"):self.r.require_current(self.d,a)
  self.r.require_current(self.d,b)
 def test_cross_relationship_reference_rejected(self):
  other=domain("sentinel-scribe","scribe")
  with self.assertRaises(EnrollmentError):self.r.register_initial(self.d,ref(other,1))
 def test_fleet_wide_reference_reuse_rejected(self):
  s=domain("sentinel-scribe","scribe");self.r.register_initial(self.d,ref(self.d,1,"credential:shared"))
  with self.assertRaisesRegex(EnrollmentError,"fleet-wide"):self.r.register_initial(s,ref(s,1,"credential:shared"))
 def test_restart_preserves_current(self):
  a=ref(self.d,1);self.r.register_initial(self.d,a);self.assertEqual(a,CredentialReferenceRegistry(self.p).current(self.d))
 def test_malformed_registry_fails_closed(self):
  self.p.write_text("[]")
  with self.assertRaisesRegex(EnrollmentError,"malformed credential registry"):CredentialReferenceRegistry(self.p)
 def test_tampered_relationship_identity_fails_closed(self):
  self.r.register_initial(self.d,ref(self.d,1));db=json.loads(self.p.read_text())
  rid=self.d.relationship_id;db["relationships"][rid]["relationship_id"]="relationship:forged";self.p.write_text(json.dumps(db))
  with self.assertRaisesRegex(EnrollmentError,"relationship identity mismatch"):CredentialReferenceRegistry(self.p)
 def test_tampered_shared_reference_fails_closed(self):
  s=domain("sentinel-scribe","scribe");self.r.register_initial(self.d,ref(self.d,1,"credential:r"));self.r.register_initial(s,ref(s,1,"credential:s"))
  db=json.loads(self.p.read_text());db["relationships"][s.relationship_id]["key_reference"]="credential:r"
  self.p.write_text(json.dumps(db))
  # A tampered shared key reference may now fail earlier on deterministic record
  # integrity before the fleet-wide uniqueness check. Either path is fail-closed.
  with self.assertRaisesRegex(EnrollmentError,"credential registry record integrity failure|fleet-wide credential reuse"):CredentialReferenceRegistry(self.p)

class CredentialRegistryConcurrencyTests(unittest.TestCase):
 def test_initial_registration_has_one_winner(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"c.json";CredentialReferenceRegistry(p);q=multiprocessing.Queue()
   ps=[multiprocessing.Process(target=register_worker,args=(str(p),q)) for _ in range(8)]
   [x.start() for x in ps];[x.join(5) for x in ps];out=[q.get(timeout=2) for _ in ps]
   self.assertEqual(1,out.count("OK"));self.assertEqual(1,CredentialReferenceRegistry(p).current(domain()).generation)
 def test_conflicting_rotation_has_one_winner(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"c.json";d=domain();r=CredentialReferenceRegistry(p);r.register_initial(d,ref(d,1));q=multiprocessing.Queue()
   ps=[multiprocessing.Process(target=rotate_worker,args=(str(p),f"credential:race:{n}",q)) for n in range(8)]
   [x.start() for x in ps];[x.join(5) for x in ps];out=[q.get(timeout=2) for _ in ps]
   self.assertEqual(1,len([x for x in out if x.startswith("OK:")]))
   self.assertEqual(2,CredentialReferenceRegistry(p).current(d).generation)

if __name__=="__main__":unittest.main()

class RegistryBoundSessionGateTests(unittest.TestCase):
 def test_rotation_invalidates_old_session_binding_at_registry_gate(self):
  from sentinel_forge.credential_session import bind_session_credential,require_registry_current_credential_session
  from sentinel_forge.session import derive_session
  with tempfile.TemporaryDirectory() as td:
   d=domain();r=CredentialReferenceRegistry(Path(td)/"c.json")
   c1=ref(d,1);r.register_initial(d,c1)
   s1=derive_session(d,generation=1,challenge=b"0123456789abcdef");b1=bind_session_credential(s1,d,c1)
   require_registry_current_credential_session(b1,s1,d,c1,r)
   c2=ref(d,2);r.rotate(d,c2)
   with self.assertRaisesRegex(EnrollmentError,"stale"):
    require_registry_current_credential_session(b1,s1,d,c1,r)
 def test_current_generation_session_passes_registry_gate(self):
  from sentinel_forge.credential_session import bind_session_credential,require_registry_current_credential_session
  from sentinel_forge.session import derive_session
  with tempfile.TemporaryDirectory() as td:
   d=domain();r=CredentialReferenceRegistry(Path(td)/"c.json")
   c1=ref(d,1);r.register_initial(d,c1);c2=ref(d,2);r.rotate(d,c2)
   s2=derive_session(d,generation=2,challenge=b"fedcba9876543210");b2=bind_session_credential(s2,d,c2)
   require_registry_current_credential_session(b2,s2,d,c2,r)
