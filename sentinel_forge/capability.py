"""Offline peer capability and downgrade-protection contract."""
from dataclasses import dataclass
from .enrollment import EnrollmentError

FORMAT="sentinel-courier-capabilities-v1"

@dataclass(frozen=True)
class PeerCapabilities:
 format:str
 peer_identity:str
 protocol_versions:tuple[int,...]
 schema_versions:tuple[int,...]
 features:tuple[str,...]

@dataclass(frozen=True)
class NegotiatedCapabilities:
 peer_identity:str
 protocol_version:int
 schema_version:int
 features:tuple[str,...]

def capabilities(*,peer_identity:str,protocol_versions, schema_versions,features=())->PeerCapabilities:
 if not isinstance(peer_identity,str) or not peer_identity.strip():raise EnrollmentError("peer identity required")
 pv=_versions(protocol_versions,"protocol");sv=_versions(schema_versions,"schema")
 fs=tuple(sorted(set(features)))
 if any(not isinstance(x,str) or not x.strip() for x in fs):raise EnrollmentError("feature invalid")
 return PeerCapabilities(FORMAT,peer_identity,pv,sv,fs)

def negotiate(local:PeerCapabilities,remote:PeerCapabilities,*,expected_peer:str,minimum_protocol:int,minimum_schema:int,required_features=())->NegotiatedCapabilities:
 if not isinstance(expected_peer,str) or not expected_peer.strip():raise EnrollmentError("expected peer required")
 if any(not isinstance(x,int) or isinstance(x,bool) or x<1 for x in (minimum_protocol,minimum_schema)):raise EnrollmentError("capability minimum version invalid")
 if any(not isinstance(x,str) or not x.strip() for x in required_features):raise EnrollmentError("required capability invalid")
 if local.format!=FORMAT or remote.format!=FORMAT:raise EnrollmentError("capability format invalid")
 if remote.peer_identity!=expected_peer:raise EnrollmentError("capability peer identity mismatch")
 common_p=sorted(set(local.protocol_versions)&set(remote.protocol_versions),reverse=True)
 common_s=sorted(set(local.schema_versions)&set(remote.schema_versions),reverse=True)
 if not common_p or common_p[0]<minimum_protocol:raise EnrollmentError("no acceptable protocol version")
 if not common_s or common_s[0]<minimum_schema:raise EnrollmentError("no acceptable schema version")
 req=set(required_features);common_f=set(local.features)&set(remote.features)
 if not req<=common_f:raise EnrollmentError("required capability unavailable")
 return NegotiatedCapabilities(expected_peer,common_p[0],common_s[0],tuple(sorted(common_f)))

def require_no_downgrade(previous:NegotiatedCapabilities,current:NegotiatedCapabilities)->None:
 if previous.peer_identity!=current.peer_identity:raise EnrollmentError("negotiated peer changed")
 if current.protocol_version<previous.protocol_version:raise EnrollmentError("protocol downgrade rejected")
 if current.schema_version<previous.schema_version:raise EnrollmentError("schema downgrade rejected")
 if not set(previous.features)<=set(current.features):raise EnrollmentError("capability downgrade rejected")

def _versions(values,label):
 try:v=tuple(sorted(set(values)))
 except TypeError as exc:raise EnrollmentError(f"{label} versions invalid") from exc
 if not v or any(not isinstance(x,int) or isinstance(x,bool) or x<1 for x in v):raise EnrollmentError(f"{label} versions invalid")
 return v
