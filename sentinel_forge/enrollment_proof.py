"""Challenge-bound, algorithm-neutral remote enrollment proof."""

from __future__ import annotations
from dataclasses import dataclass, asdict
import hashlib, json
from typing import Any
from .authenticity import AuthenticityEnvelope, Signer, Verifier, create_envelope, verify_envelope
from .enrollment import EnrollmentBundle, EnrollmentProof, EnrollmentError, verify_proof

FORMAT="sentinel-courier-remote-proof-v1"

@dataclass(frozen=True)
class EnrollmentChallenge:
    format: str
    enrollment_id: str
    forge_identity: str
    remote_identity: str
    challenge_id: str
    challenge_digest: str
    def as_dict(self): return asdict(self)

@dataclass(frozen=True)
class AuthenticatedEnrollmentProof:
    format: str
    challenge: EnrollmentChallenge
    proof: EnrollmentProof
    authenticity: AuthenticityEnvelope

def issue_challenge(bundle:EnrollmentBundle, *, nonce:bytes)->EnrollmentChallenge:
    if not nonce or len(nonce)<16: raise EnrollmentError("challenge nonce must be at least 128 bits")
    core={"format":FORMAT,"enrollment_id":bundle.enrollment_id,"forge_identity":bundle.forge_identity,
          "remote_identity":bundle.remote_identity,"nonce_digest":"sha256:"+hashlib.sha256(nonce).hexdigest()}
    challenge_id="challenge:"+_sha(core)
    return EnrollmentChallenge(FORMAT,bundle.enrollment_id,bundle.forge_identity,bundle.remote_identity,
        challenge_id,"sha256:"+hashlib.sha256(nonce).hexdigest())

def authenticate_proof(bundle:EnrollmentBundle,challenge:EnrollmentChallenge,
                       proof:EnrollmentProof,signer:Signer)->AuthenticatedEnrollmentProof:
    _validate_binding(bundle,challenge,proof)
    subject=_subject(challenge,proof)
    envelope=create_envelope(subject,signer)
    if envelope.signer_identity!=bundle.remote_identity:
        raise EnrollmentError("proof signer is not the enrolled remote identity")
    return AuthenticatedEnrollmentProof(FORMAT,challenge,proof,envelope)

def verify_authenticated_proof(bundle:EnrollmentBundle, authenticated:AuthenticatedEnrollmentProof,
                               verifier:Verifier, *, expected_remote_key_reference:str,
                               expected_challenge_id:str)->bool:
    if authenticated.format!=FORMAT:return False
    c=authenticated.challenge; p=authenticated.proof
    if c.challenge_id!=expected_challenge_id:return False
    try:_validate_binding(bundle,c,p)
    except EnrollmentError:return False
    return verify_envelope(_subject(c,p),authenticated.authenticity,verifier,
        expected_signer_identity=bundle.remote_identity,
        expected_key_reference=expected_remote_key_reference)

def _validate_binding(bundle,challenge,proof):
    if challenge.format!=FORMAT: raise EnrollmentError("wrong challenge format")
    if challenge.enrollment_id!=bundle.enrollment_id or proof.enrollment_id!=bundle.enrollment_id:
        raise EnrollmentError("enrollment identity mismatch")
    if challenge.forge_identity!=bundle.forge_identity or proof.forge_identity!=bundle.forge_identity:
        raise EnrollmentError("Forge identity mismatch")
    if challenge.remote_identity!=bundle.remote_identity or proof.remote_identity!=bundle.remote_identity:
        raise EnrollmentError("remote identity mismatch")
    if not verify_proof(bundle,proof): raise EnrollmentError("base enrollment proof invalid")

def _subject(challenge,proof)->bytes:
    return _canonical({"challenge":challenge.as_dict(),"proof":proof.as_dict()})

def _canonical(value:Any)->bytes:
    return (json.dumps(value,sort_keys=True,separators=(",",":"))+"\n").encode()

def _sha(value:Any)->str:return hashlib.sha256(_canonical(value)).hexdigest()
