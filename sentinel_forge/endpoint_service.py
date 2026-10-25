"""Portable endpoint Courier service configuration artifacts.

Generated configuration is inert until installed by an explicitly approved endpoint installer.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib,json
from .peer_configuration import PeerConfigurationPlan
from .endpoint_platform import PlatformFamily,PlatformProfile

@dataclass(frozen=True)
class EndpointServiceArtifacts:
 config_json:str
 service_definition:str
 launcher:str
 config_sha256:str
 service_sha256:str
 launcher_sha256:str

def _sha(s): return "sha256:"+hashlib.sha256(s.encode()).hexdigest()

def build_endpoint_service_artifacts(platform:PlatformProfile,plan:PeerConfigurationPlan)->EndpointServiceArtifacts:
 cfg={
  "format":"sentinel-courier-endpoint-config-v1",
  "forge_identity":plan.forge_identity,
  "peer_identity":plan.peer_identity,
  "role":plan.role,
  "enrollment_id":plan.enrollment_id,
  "challenge_id":plan.challenge_id,
  "permitted_actions":list(plan.permitted_actions),
  "payload_protection":"AES-256-GCM",
  "relationship_key_policy":"peer-specific reference only; no plaintext key in configuration",
  "callback_policy":"authenticated exact binding required before activation",
  "activation_state":"STAGED",
  "plan_digest":plan.plan_digest,
 }
 cj=json.dumps(cfg,indent=2,sort_keys=True)+"\n"
 windows=platform.family in {PlatformFamily.WINDOWS_10,PlatformFamily.WINDOWS_11}
 if windows:
  launcher=r'''$ErrorActionPreference = 'Stop'
$Config = Join-Path $env:ProgramData 'Sentinel\Courier\config\endpoint.json'
if (-not (Test-Path -LiteralPath $Config -PathType Leaf)) { throw 'Sentinel Courier config missing' }
# Endpoint runtime binary is provisioned separately and hash-verified by installer.
$Runtime = Join-Path $env:ProgramFiles 'Sentinel\Courier\sentinel-courier-endpoint.exe'
if (-not (Test-Path -LiteralPath $Runtime -PathType Leaf)) { throw 'Sentinel Courier runtime missing' }
& $Runtime '--config' $Config
exit $LASTEXITCODE
'''
  service='''SentinelCourier
DisplayName=Sentinel Courier Endpoint
StartType=Automatic
Account=NT SERVICE\\SentinelCourier
Recovery=restart-limited
NetworkAuthority=Forge relationship only
'''
 else:
  launcher='''#!/bin/sh
set -eu
CONFIG=/etc/sentinel-courier/endpoint.json
RUNTIME=/usr/libexec/sentinel-courier/sentinel-courier-endpoint
test -r "$CONFIG" || { echo "Courier config missing" >&2; exit 80; }
test -x "$RUNTIME" || { echo "Courier runtime missing" >&2; exit 81; }
exec "$RUNTIME" --config "$CONFIG"
'''
  service='''[Unit]
Description=Sentinel Courier Endpoint
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=sentinel-courier
Group=sentinel-courier
ExecStart=/usr/libexec/sentinel-courier/launch
NoNewPrivileges=yes
PrivateTmp=yes
PrivateDevices=yes
ProtectSystem=strict
ProtectHome=yes
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectControlGroups=yes
RestrictSUIDSGID=yes
LockPersonality=yes
RestrictRealtime=yes
MemoryDenyWriteExecute=yes
ReadWritePaths=/var/lib/sentinel-courier
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
'''
 return EndpointServiceArtifacts(cj,service,launcher,_sha(cj),_sha(service),_sha(launcher))
