"""Generate inert, reviewable cross-platform Sentinel enrollment packages."""
from __future__ import annotations
from dataclasses import dataclass,asdict
import hashlib,json
from .peer_configuration import PeerProfile,PeerConfigurationPlan,compile_peer_configuration
from .endpoint_platform import PlatformFamily,PlatformProfile,build_platform_profile
FORMAT="sentinel-endpoint-enrollment-package-v1"
@dataclass(frozen=True)
class EndpointEnrollmentPackage:
 format:str;platform:PlatformProfile;peer_plan:PeerConfigurationPlan
 preflight_script:str;install_script:str;rollback_script:str;manifest_json:str;package_digest:str
def _sha(s):return "sha256:"+hashlib.sha256(s.encode()).hexdigest()
def _linux_preflight(p,plan):
 distro="ubuntu" if p.family in {PlatformFamily.UBUNTU_DESKTOP,PlatformFamily.UBUNTU_SERVER} else "debian"
 return """#!/bin/sh
set -eu
# READ-ONLY Sentinel enrollment preflight. Makes no changes.
test -r /etc/os-release || { echo 'BLOCKED: os-release unavailable'; exit 20; }
. /etc/os-release
test "$ID" = "__DISTRO__" || { echo "BLOCKED: expected __DISTRO__, observed $ID"; exit 21; }
command -v systemctl >/dev/null 2>&1 || { echo 'BLOCKED: systemd unavailable'; exit 22; }
command -v ssh >/dev/null 2>&1 || { echo 'BLOCKED: OpenSSH client unavailable'; exit 23; }
command -v sha256sum >/dev/null 2>&1 || { echo 'BLOCKED: SHA-256 utility unavailable'; exit 24; }
test "$(id -u)" -eq 0 || { echo 'BLOCKED: root required for installation'; exit 25; }
printf '%s\\n' "PLATFORM=$ID" "VERSION=$VERSION_ID" "ARCH=$(uname -m)" "PEER=__PEER__" "PLAN=__PLAN__"
""".replace("__DISTRO__",distro).replace("__PEER__",plan.peer_identity).replace("__PLAN__",plan.plan_digest)
def _windows_preflight(p,plan):
 expected="Windows 10" if p.family==PlatformFamily.WINDOWS_10 else "Windows 11"
 return """# READ-ONLY Sentinel enrollment preflight. Makes no changes.
$ErrorActionPreference = 'Stop'
$os = Get-CimInstance Win32_OperatingSystem
if ($os.Caption -notmatch '__EXPECTED__') { throw ('BLOCKED: expected __EXPECTED__; observed ' + $os.Caption) }
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'BLOCKED: Administrator required for installation' }
if (-not (Get-Command ssh.exe -ErrorAction SilentlyContinue)) { throw 'BLOCKED: OpenSSH client unavailable' }
Write-Output ('PLATFORM=' + $os.Caption)
Write-Output ('VERSION=' + $os.Version)
Write-Output ('ARCH=' + $env:PROCESSOR_ARCHITECTURE)
Write-Output 'PEER=__PEER__'
Write-Output 'PLAN=__PLAN__'
""".replace("__EXPECTED__",expected).replace("__PEER__",plan.peer_identity).replace("__PLAN__",plan.plan_digest)
def _linux_install(plan):
 return """#!/bin/sh
set -eu
# REVIEW GATE: no production credential material is embedded.
test "$SENTINEL_OPERATOR_APPROVED" = YES || { echo 'BLOCKED: explicit operator approval required'; exit 70; }
test -n "$SENTINEL_ENROLLMENT_ARTIFACT" || { echo 'BLOCKED: target-bound enrollment artifact required'; exit 71; }
test -n "$SENTINEL_FORGE_TRUST_ANCHOR" || { echo 'BLOCKED: Forge trust anchor required'; exit 72; }
echo 'READY: prerequisites supplied; operational installer boundary is not activated by this package.'
exit 78
"""
def _windows_install(plan):
 return """$ErrorActionPreference = 'Stop'
# REVIEW GATE: no production credential material is embedded.
if ($env:SENTINEL_OPERATOR_APPROVED -ne 'YES') { throw 'BLOCKED: explicit operator approval required' }
if (-not $env:SENTINEL_ENROLLMENT_ARTIFACT) { throw 'BLOCKED: target-bound enrollment artifact required' }
if (-not $env:SENTINEL_FORGE_TRUST_ANCHOR) { throw 'BLOCKED: Forge trust anchor required' }
Write-Output 'READY: prerequisites supplied; operational installer boundary is not activated by this package.'
exit 78
"""
def _rollback(platform,plan):
 if platform.family in {PlatformFamily.WINDOWS_10,PlatformFamily.WINDOWS_11}:return "# Sentinel rollback\\nWrite-Output 'NO-OP: package did not activate endpoint changes.'\\n"
 return "#!/bin/sh\\nset -eu\\necho 'NO-OP: package did not activate endpoint changes.'\\n"
def generate_endpoint_package(profile:PeerProfile,*,family:PlatformFamily,version="auto",architecture="auto"):
 plan=compile_peer_configuration(profile);platform=build_platform_profile(family,version=version,architecture=architecture)
 windows=family in {PlatformFamily.WINDOWS_10,PlatformFamily.WINDOWS_11}
 preflight=_windows_preflight(platform,plan) if windows else _linux_preflight(platform,plan)
 install=_windows_install(plan) if windows else _linux_install(plan);rollback=_rollback(platform,plan)
 manifest={"format":FORMAT,"peer_plan_digest":plan.plan_digest,"peer_identity":plan.peer_identity,"platform":asdict(platform),"scripts":{"preflight_sha256":_sha(preflight),"install_sha256":_sha(install),"rollback_sha256":_sha(rollback)},"operational_effects_enabled":False,"contains_secret_material":False,"requires_explicit_operator_approval":True}
 mj=json.dumps(manifest,indent=2,sort_keys=True)+"\n";digest="sha256:"+hashlib.sha256((json.dumps(manifest,sort_keys=True,separators=(",",":"))+"\n").encode()).hexdigest()
 return EndpointEnrollmentPackage(FORMAT,platform,plan,preflight,install,rollback,mj,digest)

def materialize_endpoint_package(package:EndpointEnrollmentPackage,directory):
 from pathlib import Path
 import os
 if not isinstance(package,EndpointEnrollmentPackage):raise TypeError("endpoint package required")
 root=Path(directory)
 root.mkdir(parents=True,exist_ok=False)
 windows=package.platform.family in {PlatformFamily.WINDOWS_10,PlatformFamily.WINDOWS_11}
 names=("preflight.ps1","install.ps1","rollback.ps1") if windows else ("preflight.sh","install.sh","rollback.sh")
 files={
  "manifest.json":package.manifest_json,
  names[0]:package.preflight_script,
  names[1]:package.install_script,
  names[2]:package.rollback_script,
 }
 for name,data in files.items():
  path=root/name
  flags=os.O_WRONLY|os.O_CREAT|os.O_EXCL
  fd=os.open(path,flags,0o600)
  try:
   os.write(fd,data.encode());os.fsync(fd)
  finally:os.close(fd)
 return tuple(root/name for name in files)

def operational_artifacts(package:EndpointEnrollmentPackage):
 from .endpoint_service import build_endpoint_service_artifacts
 return build_endpoint_service_artifacts(package.platform,package.peer_plan)

def render_operational_linux_installer(package:EndpointEnrollmentPackage)->str:
 return '''#!/bin/sh
set -eu
if test "$(id -u)" -ne 0; then echo 'BLOCKED: root required'; exit 70; fi
if test "${SENTINEL_OPERATOR_APPROVED:-}" != YES; then echo 'BLOCKED: operator approval required'; exit 71; fi
if ! test -f ./endpoint.json -a -f ./sentinel-courier.service -a -f ./launch; then echo 'BLOCKED: package incomplete'; exit 72; fi
if test -z "${SENTINEL_RUNTIME_PATH:-}"; then echo 'BLOCKED: verified endpoint runtime path required'; exit 73; fi
if ! test -x "$SENTINEL_RUNTIME_PATH"; then echo 'BLOCKED: endpoint runtime not executable'; exit 74; fi
if ! id sentinel-courier >/dev/null 2>&1; then echo 'BLOCKED: dedicated sentinel-courier service account must be provisioned by approved host policy'; exit 75; fi
install -d -o root -g sentinel-courier -m 0750 /etc/sentinel-courier /var/lib/sentinel-courier /usr/libexec/sentinel-courier
install -o root -g sentinel-courier -m 0640 ./endpoint.json /etc/sentinel-courier/endpoint.json
install -o root -g root -m 0755 ./launch /usr/libexec/sentinel-courier/launch
install -o root -g root -m 0755 "$SENTINEL_RUNTIME_PATH" /usr/libexec/sentinel-courier/sentinel-courier-endpoint
install -o root -g root -m 0644 ./sentinel-courier.service /etc/systemd/system/sentinel-courier.service
systemctl daemon-reload
systemctl enable sentinel-courier.service
echo 'STAGED: service installed and enabled but not started; enrollment activation still required.'
'''
def render_operational_linux_rollback(package:EndpointEnrollmentPackage)->str:
 return '''#!/bin/sh
set -eu
if test "$(id -u)" -ne 0; then echo 'BLOCKED: root required'; exit 70; fi
systemctl stop sentinel-courier.service 2>/dev/null || true
systemctl disable sentinel-courier.service 2>/dev/null || true
rm -f /etc/systemd/system/sentinel-courier.service
systemctl daemon-reload
rm -f /usr/libexec/sentinel-courier/launch /usr/libexec/sentinel-courier/sentinel-courier-endpoint
echo 'ROLLED BACK: service/runtime removed; state/config retained for evidence.'
'''

def render_operational_windows_installer(package:EndpointEnrollmentPackage)->str:
 return r'''$ErrorActionPreference='Stop'
$identity=[Security.Principal.WindowsIdentity]::GetCurrent()
$principal=New-Object Security.Principal.WindowsPrincipal($identity)
if(-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'BLOCKED: Administrator required'}
if($env:SENTINEL_OPERATOR_APPROVED -ne 'YES'){throw 'BLOCKED: operator approval required'}
if(-not $env:SENTINEL_RUNTIME_PATH){throw 'BLOCKED: verified endpoint runtime path required'}
$root=Join-Path $env:ProgramData 'Sentinel\Courier'
$config=Join-Path $root 'config'
$bin=Join-Path $env:ProgramFiles 'Sentinel\Courier'
New-Item -ItemType Directory -Force -Path $root,$config,$bin | Out-Null
Copy-Item -LiteralPath '.\endpoint.json' -Destination (Join-Path $config 'endpoint.json')
Copy-Item -LiteralPath '.\launch.ps1' -Destination (Join-Path $bin 'launch.ps1')
Copy-Item -LiteralPath $env:SENTINEL_RUNTIME_PATH -Destination (Join-Path $bin 'sentinel-courier-endpoint.exe')
if(Get-Service -Name SentinelCourier -ErrorAction SilentlyContinue){throw 'BLOCKED: SentinelCourier already exists; reconcile explicitly'}
$launcher=Join-Path $bin 'launch.ps1'
$cmd='powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy AllSigned -File "'+$launcher+'"'
New-Service -Name SentinelCourier -BinaryPathName $cmd -DisplayName 'Sentinel Courier Endpoint' -StartupType Automatic | Out-Null
sc.exe sidtype SentinelCourier unrestricted | Out-Null
Write-Output 'STAGED: service installed but not started; enrollment activation still required.'
'''
def render_operational_windows_rollback(package:EndpointEnrollmentPackage)->str:
 return r'''$ErrorActionPreference='Stop'
$svc=Get-Service -Name SentinelCourier -ErrorAction SilentlyContinue
if($svc){if($svc.Status -ne 'Stopped'){Stop-Service SentinelCourier -Force};sc.exe delete SentinelCourier | Out-Null}
$bin=Join-Path $env:ProgramFiles 'Sentinel\Courier'
if(Test-Path $bin){Remove-Item -LiteralPath $bin -Recurse -Force}
Write-Output 'ROLLED BACK: service/runtime removed; ProgramData state/config retained for evidence.'
'''

def render_activation_script(package:EndpointEnrollmentPackage)->str:
 windows=package.platform.family in {PlatformFamily.WINDOWS_10,PlatformFamily.WINDOWS_11}
 if windows:
  return r'''$ErrorActionPreference='Stop'
if($env:SENTINEL_OPERATOR_APPROVED -ne 'YES'){throw 'BLOCKED: operator approval required'}
$receipt=Join-Path $env:ProgramData 'Sentinel\Courier\activation-receipt.json'
if(-not (Test-Path -LiteralPath $receipt -PathType Leaf)){throw 'BLOCKED: verified activation receipt missing'}
$record=Get-Content -LiteralPath $receipt -Raw | ConvertFrom-Json
if($record.verified -ne $true){throw 'BLOCKED: activation receipt not verified'}
if($record.peer_identity -ne '__PEER__'){throw 'BLOCKED: activation receipt peer mismatch'}
if($record.plan_digest -ne '__PLAN__'){throw 'BLOCKED: activation receipt plan mismatch'}
Start-Service SentinelCourier
Write-Output 'ACTIVE: Sentinel Courier service started from verified activation receipt.'
'''.replace('__PEER__',package.peer_plan.peer_identity).replace('__PLAN__',package.peer_plan.plan_digest)
 return '''#!/bin/sh
set -eu
if test "$(id -u)" -ne 0; then echo 'BLOCKED: root required'; exit 70; fi
if test "${SENTINEL_OPERATOR_APPROVED:-}" != YES; then echo 'BLOCKED: operator approval required'; exit 71; fi
RECEIPT=/var/lib/sentinel-courier/activation-receipt.json
if ! test -f "$RECEIPT"; then echo 'BLOCKED: verified activation receipt missing'; exit 72; fi
python3 - "$RECEIPT" '__PEER__' '__PLAN__' <<'VERIFY'
import json,sys
p=json.load(open(sys.argv[1],encoding='utf-8'))
if p.get('verified') is not True: raise SystemExit('BLOCKED: activation receipt not verified')
if p.get('peer_identity') != sys.argv[2]: raise SystemExit('BLOCKED: activation receipt peer mismatch')
if p.get('plan_digest') != sys.argv[3]: raise SystemExit('BLOCKED: activation receipt plan mismatch')
VERIFY
systemctl start sentinel-courier.service
echo 'ACTIVE: Sentinel Courier service started from verified activation receipt.'
'''.replace('__PEER__',package.peer_plan.peer_identity).replace('__PLAN__',package.peer_plan.plan_digest)

def materialize_operational_endpoint_package(package:EndpointEnrollmentPackage,directory):
 from pathlib import Path
 import os
 root=Path(directory);root.mkdir(parents=True,exist_ok=False)
 a=operational_artifacts(package)
 windows=package.platform.family in {PlatformFamily.WINDOWS_10,PlatformFamily.WINDOWS_11}
 files={"manifest.json":package.manifest_json,"endpoint.json":a.config_json}
 if windows:
  files.update({"preflight.ps1":package.preflight_script,"install.ps1":render_operational_windows_installer(package),"activate.ps1":render_activation_script(package),"rollback.ps1":render_operational_windows_rollback(package),"launch.ps1":a.launcher,"service.contract.txt":a.service_definition})
 else:
  files.update({"preflight.sh":package.preflight_script,"install.sh":render_operational_linux_installer(package),"activate.sh":render_activation_script(package),"rollback.sh":render_operational_linux_rollback(package),"launch":a.launcher,"sentinel-courier.service":a.service_definition})
 written=[]
 for name,data in files.items():
  path=root/name;fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
  try:os.write(fd,data.encode());os.fsync(fd)
  finally:os.close(fd)
  written.append(path)
 return tuple(written)
