# Endpoint Enrollment Package Generator
Status: generator foundation complete; operational deployment remains gated.

Families: Windows 10, Windows 11, Ubuntu Desktop, Ubuntu Server, Debian workstation, Debian server.

Artifacts per generated package:
- manifest.json
- platform-specific read-only preflight
- platform-specific gated installer
- platform-specific rollback
All files materialize mode 0600 with no-overwrite semantics.

Current installer is intentionally inert after validating approval/artifact/trust-anchor prerequisites. No credentials, services, firewall rules, packages, SSH sessions, or remote changes are created by generation.

Next activation stage requires separately approved operational installer implementation and credential provisioning boundary.
