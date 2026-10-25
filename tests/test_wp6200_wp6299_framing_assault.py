import hashlib,os,random,struct,unittest
from sentinel_forge.enrollment import EnrollmentError
from sentinel_forge.framing import *

class FramingAssault(unittest.TestCase):
 def test_roundtrip_matrix(self):
  for n in (1,2,3,7,31,32,33,255,256,257,1024,4096,65535):
   with self.subTest(n=n):
    p=bytes((i%251 for i in range(n)));f=frame(p);r=unframe(f);self.assertEqual(p,r.protected_payload);self.assertEqual("sha256:"+hashlib.sha256(p).hexdigest(),r.payload_digest)
 def test_deterministic(self):
  p=b"x"*100;self.assertEqual(frame(p),frame(p))
 def test_empty_rejected(self):
  with self.assertRaises(EnrollmentError):frame(b"")
 def test_nonbytes_rejected_matrix(self):
  for x in (None,"x",bytearray(b"x"),memoryview(b"x"),1,True,[],{}):
   with self.subTest(t=type(x).__name__):
    with self.assertRaises(EnrollmentError):frame(x)
 def test_bad_version_type_matrix(self):
  for v in (0,2,-1,True,False,"1",None):
   with self.subTest(v=v):
    with self.assertRaises(EnrollmentError):frame(b"x",version=v)
  for t in (0,2,-1,True,False,"1",None):
   with self.subTest(t=t):
    with self.assertRaises(EnrollmentError):frame(b"x",frame_type=t)
 def test_every_header_byte_mutation_fails_or_changes_only_digest_checked_content(self):
  good=frame(b"protected-payload")
  for i in range(HEADER.size):
   m=bytearray(good);m[i]^=1
   with self.subTest(i=i):
    with self.assertRaises(EnrollmentError):unframe(bytes(m))
 def test_every_payload_byte_mutation_rejected(self):
  good=frame(bytes(range(128)))
  for i in range(HEADER.size,len(good)):
   m=bytearray(good);m[i]^=1
   with self.subTest(i=i):
    with self.assertRaises(EnrollmentError):unframe(bytes(m))
 def test_all_truncations_rejected(self):
  good=frame(b"x"*128)
  for n in range(len(good)):
   with self.subTest(n=n):
    with self.assertRaises(EnrollmentError):unframe(good[:n])
 def test_all_small_extensions_rejected(self):
  good=frame(b"x"*32)
  for n in range(1,65):
   with self.subTest(n=n):
    with self.assertRaises(EnrollmentError):unframe(good+b"z"*n)
 def test_concatenated_frames_rejected(self):
  a=frame(b"a");b=frame(b"b")
  with self.assertRaises(EnrollmentError):unframe(a+b)
 def test_declared_length_mutation_matrix(self):
  good=bytearray(frame(b"x"*20))
  for n in (0,1,19,21,100,MAX_PROTECTED_BYTES,MAX_PROTECTED_BYTES+1,2**32-1):
   m=bytearray(good);m[6:10]=struct.pack(">I",n)
   with self.subTest(n=n):
    with self.assertRaises(EnrollmentError):unframe(bytes(m))
 def test_random_hostile_inputs_fail_closed(self):
  rng=random.Random(0x5E17)
  accepted=0
  for _ in range(500):
   raw=bytes(rng.randrange(256) for _ in range(rng.randrange(0,256)))
   try:unframe(raw);accepted+=1
   except EnrollmentError:pass
  self.assertEqual(0,accepted)
 def test_oversize_input_rejected_before_payload_processing(self):
  with self.assertRaises(EnrollmentError):unframe(b"x"*(MAX_FRAME_BYTES+1))
 def test_exact_max_roundtrip(self):
  p=b"x"*MAX_PROTECTED_BYTES;self.assertEqual(len(p),len(unframe(frame(p)).protected_payload))
 def test_frame_has_no_plaintext_semantic_fields(self):
  names=set(ProtectedFrame.__dataclass_fields__);self.assertEqual({"version","frame_type","protected_payload","payload_digest"},names)
  for bad in ("artifact","operation","relationship","credential","key","plaintext","authorization"):self.assertFalse(any(bad in n for n in names))
