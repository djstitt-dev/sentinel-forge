"""Algorithm-neutral authenticity envelope for Sentinel enrollment artifacts.

No production signature algorithm is selected here. Concrete production signing
requires a separately approved trust-anchor and algorithm decision.
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
import hashlib, hmac, json
from typing import Protocol

class AuthenticityError(RuntimeError): pass

@dataclass(frozen=True)
class AuthenticityEnvelope:
    format: str
    signer_identity: str
    algorithm: str
    key_reference: str
    subject_digest: str
    signature: str
    def as_dict(self): return asdict(self)

class Signer(Protocol):
    @property
    def signer_identity(self)->str: ...
    @property
    def algorithm(self)->str: ...
    @property
    def key_reference(self)->str: ...
    def sign(self, subject:bytes)->bytes: ...

class Verifier(Protocol):
    def verify(self, *, signer_identity:str, algorithm:str, key_reference:str,
               subject:bytes, signature:bytes)->bool: ...

FORMAT="sentinel-authenticity-envelope-v1"

def create_envelope(subject:bytes, signer:Signer)->AuthenticityEnvelope:
    if not isinstance(subject,bytes) or not subject: raise AuthenticityError("authenticity subject must be nonempty bytes")
    try: identity=signer.signer_identity; algorithm=signer.algorithm; key_reference=signer.key_reference
    except Exception as exc: raise AuthenticityError("signer metadata unavailable") from exc
    if any(not isinstance(v,str) or not v.strip() for v in (identity,algorithm,key_reference)):
        raise AuthenticityError("signer metadata invalid")
    try: signature=signer.sign(subject)
    except Exception as exc: raise AuthenticityError("signer failed") from exc
    if not isinstance(signature,bytes) or not signature: raise AuthenticityError("signer returned invalid signature")
    return AuthenticityEnvelope(FORMAT,identity,algorithm,key_reference,
        "sha256:"+hashlib.sha256(subject).hexdigest(),signature.hex())

def verify_envelope(subject:bytes,envelope:AuthenticityEnvelope,verifier:Verifier,
                    *, expected_signer_identity:str,expected_key_reference:str)->bool:
    if not isinstance(subject,bytes) or not subject or not isinstance(envelope,AuthenticityEnvelope): return False
    if any(not isinstance(v,str) or not v.strip() for v in (expected_signer_identity,expected_key_reference,envelope.format,envelope.signer_identity,envelope.algorithm,envelope.key_reference,envelope.subject_digest,envelope.signature)): return False
    if envelope.format!=FORMAT: return False
    if envelope.signer_identity!=expected_signer_identity: return False
    if envelope.key_reference!=expected_key_reference: return False
    if envelope.subject_digest!="sha256:"+hashlib.sha256(subject).hexdigest(): return False
    try: sig=bytes.fromhex(envelope.signature)
    except (ValueError,TypeError): return False
    if not sig:return False
    try:return verifier.verify(signer_identity=envelope.signer_identity,algorithm=envelope.algorithm,
        key_reference=envelope.key_reference,subject=subject,signature=sig) is True
    except Exception:return False

class TestOnlyHMACSigner:
    """TEST ONLY. HMAC is symmetric and is not the production enrollment design."""
    algorithm="TEST-ONLY-HMAC-SHA256"
    def __init__(self,identity:str,key_reference:str,key:bytes):
        if not identity or not key_reference or not key: raise ValueError("test signer fields required")
        self._identity=identity; self._ref=key_reference; self._key=bytes(key)
    @property
    def signer_identity(self): return self._identity
    @property
    def key_reference(self): return self._ref
    def sign(self,subject:bytes)->bytes: return hmac.new(self._key,subject,hashlib.sha256).digest()

class TestOnlyHMACVerifier:
    """TEST ONLY verifier paired with TestOnlyHMACSigner."""
    def __init__(self,keys:dict[tuple[str,str],bytes]): self._keys=dict(keys)
    def verify(self,*,signer_identity,algorithm,key_reference,subject,signature):
        if algorithm!="TEST-ONLY-HMAC-SHA256": return False
        key=self._keys.get((signer_identity,key_reference))
        if key is None:return False
        expected=hmac.new(key,subject,hashlib.sha256).digest()
        return hmac.compare_digest(expected,signature)

def canonical_envelope(envelope:AuthenticityEnvelope)->bytes:
    return (json.dumps(envelope.as_dict(),sort_keys=True,separators=(",",":"))+"\n").encode()
