"""Offline compiler for Forge-controlled peer enrollment/configuration plans.

Produces reviewable plans only. No credentials, network connections, files on peers,
services, or host configuration are created here.
"""
from __future__ import annotations
from dataclasses import dataclass,asdict
import hashlib,json,re
from .enrollment import EnrollmentError,build_bundle
from .child_bootstrap import build_child_bootstrap,bootstrap_digest

FORMAT="sentinel-forge-peer-configuration-plan-v1"
FORGE_IDENTITY="sentinel-forge"
ALLOWED_ROLES=frozenset({"scribe","watchtower","reaper","managed-peer"})
ALLOWED_ACTIONS=frozenset({
    "courier.receive","courier.send","health.report","evidence.submit",
    "configuration.receive","notification.receive",
})
FORBIDDEN_ACTION_FRAGMENTS=("shell","root","sudo","arbitrary","execute-any","credential.export","key.export")

@dataclass(frozen=True)
class PeerProfile:
    peer_identity:str
    role:str
    host:str
    ssh_user:str
    ssh_port:int
    ssh_host_key_sha256:str
    requested_actions:tuple[str,...]

@dataclass(frozen=True)
class PeerConfigurationPlan:
    format:str
    forge_identity:str
    peer_identity:str
    role:str
    endpoint:str
    ssh_user:str
    ssh_port:int
    ssh_host_key_sha256:str
    enrollment_id:str
    challenge_id:str
    permitted_actions:tuple[str,...]
    trust_topology:str
    transport_authentication:str
    payload_protection:str
    relationship_key_policy:str
    callback_policy:str
    child_notification:str
    activation_policy:str
    plan_digest:str

    def as_dict(self): return asdict(self)

def _required(value,name):
    if not isinstance(value,str) or not value.strip(): raise EnrollmentError(f"{name} required")
    return value.strip()

def validate_profile(p:PeerProfile)->None:
    if not isinstance(p,PeerProfile): raise EnrollmentError("peer profile required")
    identity=_required(p.peer_identity,"peer identity")
    _required(p.host,"peer host"); _required(p.ssh_user,"SSH user")
    if identity==FORGE_IDENTITY: raise EnrollmentError("peer identity cannot be Forge")
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{1,126}",identity):
        raise EnrollmentError("peer identity must be canonical and bounded")
    if p.role not in ALLOWED_ROLES: raise EnrollmentError("peer role is not allowlisted")
    if type(p.ssh_port) is not int or not 1<=p.ssh_port<=65535: raise EnrollmentError("SSH port invalid")
    fp=_required(p.ssh_host_key_sha256,"SSH host-key fingerprint")
    if not re.fullmatch(r"SHA256:[A-Za-z0-9+/]{20,100}={0,2}",fp):
        raise EnrollmentError("SSH host-key fingerprint format invalid")
    if not isinstance(p.requested_actions,tuple) or not p.requested_actions:
        raise EnrollmentError("explicit requested actions required")
    if len(set(p.requested_actions))!=len(p.requested_actions):
        raise EnrollmentError("duplicate requested actions prohibited")
    for action in p.requested_actions:
        if action not in ALLOWED_ACTIONS: raise EnrollmentError("requested action is not allowlisted")
        if any(x in action for x in FORBIDDEN_ACTION_FRAGMENTS):
            raise EnrollmentError("broad execution authority prohibited")

def compile_peer_configuration(p:PeerProfile)->PeerConfigurationPlan:
    validate_profile(p)
    actions=tuple(sorted(p.requested_actions))
    endpoint=f"{p.host}:{p.ssh_port}"
    policy_ref="policy:forge-peer:"+hashlib.sha256(
        json.dumps({"peer":p.peer_identity,"role":p.role,"actions":actions},sort_keys=True).encode()
    ).hexdigest()
    bundle=build_bundle(
        forge_identity=FORGE_IDENTITY,remote_identity=p.peer_identity,remote_role=p.role,
        permitted_actions=actions,permitted_target=p.peer_identity,policy_reference=policy_ref,
    )
    challenge_id="challenge:"+hashlib.sha256(
        (bundle.enrollment_id+"|"+p.ssh_host_key_sha256).encode()
    ).hexdigest()
    bootstrap=build_child_bootstrap(
        child_identity=p.peer_identity,endpoint=endpoint,enrollment_id=bundle.enrollment_id,
        challenge_id=challenge_id,artifact_digest=bundle.payload_digest,
    )
    core={
        "format":FORMAT,"forge_identity":FORGE_IDENTITY,"peer_identity":p.peer_identity,
        "role":p.role,"endpoint":endpoint,"ssh_user":p.ssh_user,"ssh_port":p.ssh_port,
        "ssh_host_key_sha256":p.ssh_host_key_sha256,"enrollment_id":bundle.enrollment_id,
        "challenge_id":challenge_id,"permitted_actions":actions,
        "trust_topology":"hub-and-spoke; Forge is enrollment/relationship authority; no implicit peer-to-peer trust",
        "transport_authentication":"mutual authenticated relationship after target-bound enrollment; SSH bootstrap requires pinned host key",
        "payload_protection":"AES-256-GCM authenticated encryption with relationship/session/operation/artifact/sequence associated data",
        "relationship_key_policy":"unique per Forge<->peer relationship; Forge-held authority; no fleet-wide symmetric key; non-exportable by policy",
        "callback_policy":"callback grants no trust by arrival; exact peer/enrollment/challenge/key-reference binding plus authentication required",
        "child_notification":"Sentinel Courier connected to Forge.",
        "activation_policy":"operator approval + verified enrollment proof + current credential + protected session required",
        "bootstrap_digest":bootstrap_digest(bootstrap),
    }
    digest="sha256:"+hashlib.sha256(
        (json.dumps(core,sort_keys=True,separators=(",",":"))+"\n").encode()
    ).hexdigest()
    core.pop("bootstrap_digest")
    return PeerConfigurationPlan(**core,plan_digest=digest)

def render_remote_script_template(plan:PeerConfigurationPlan)->str:
    if not isinstance(plan,PeerConfigurationPlan): raise EnrollmentError("peer configuration plan required")
    # Intentionally non-operational until the enrollment artifact and Forge trust anchor
    # are supplied by a separately authorized credential/provisioning boundary.
    return f"""#!/bin/sh
set -eu
# Sentinel peer bootstrap template — REVIEW REQUIRED
# peer={plan.peer_identity}
# role={plan.role}
# plan={plan.plan_digest}
# This template intentionally contains NO secret material and performs NO enrollment
# until separately supplied, target-bound artifacts are verified.
echo 'Sentinel enrollment package required; no configuration changes performed.'
exit 78
"""
