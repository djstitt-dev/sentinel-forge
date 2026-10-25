# Sentinel Endpoint Operational Installer
Status: implementation complete for package generation; no endpoint deployment performed.

Supported: Windows 10/11, Ubuntu Desktop/Server, Debian workstation/server.

Each operational package contains:
- manifest and staged endpoint configuration
- read-only platform preflight
- privileged install script
- separate activation script
- rollback script
- launcher
- service definition/contract

Security lifecycle:
PRECHECK -> INSTALLED/STAGED -> VERIFIED ACTIVATION RECEIPT -> ACTIVE.
Installation never starts the Courier service. Activation requires explicit operator approval plus a verified receipt exactly bound to peer identity and plan digest.

Linux:
- dedicated sentinel-courier account must already exist under approved host policy
- root-owned configuration/runtime paths
- hardened systemd unit
- enable without start
- rollback removes service/runtime but retains state/config evidence

Windows:
- Administrator required
- SentinelCourier Windows service
- PowerShell noninteractive launcher with AllSigned execution policy
- service created but not started
- rollback removes service/runtime while retaining ProgramData evidence

Generated packages contain no production relationship secret. Runtime binary and production credential/trust artifacts are separately provisioned and verified.
