# Project Sentinel Forge

Forge is a hardened Ubuntu Sentinel component. This repository will hold its
governance, reviewed configuration, verification procedures, and operational
documentation. Significant host hardening and AIDE baseline work predates it.
Forge's detailed operational interfaces and acceptance criteria remain to be
defined with the operator.

## Current status
Work Package 2 establishes repository governance only. No host configuration is
managed or applied by these files, and operational readiness has not been
verified. No F1.17K42 closure record is created here. The operator approved
finalization and the initial governance commit. Work stops after that commit;
later work packages require their own authorization.

The operator reports an underlying Ubuntu 24.04.4 Forge host. Earlier Codex
observations of Ubuntu 26.04.1 belong to the CODEX SANDBOX CONTEXT and do not
describe the underlying host. See the context inventory below for provenance.

## Governance and entry points
The operator alone approves security-sensitive, architecture-changing,
destructive, privileged, and trust-boundary actions. Approval of repository work
does not authorize deployment or AIDE trust changes.

- [Agent rules](AGENTS.md)
- [Architecture and governance](docs/architecture/governance.md)
- [Execution contexts and initial observations](docs/inventory/execution-contexts.md)
- [Evidence handling and provenance](evidence/README.md)
- [Supplied AIDE anchor manifest](evidence/manifests/aide-anchors.json)
- [Proposed work packages](docs/plans/work-packages.md)

`config/` is reserved for reviewed desired state; `scripts/` separates discovery,
verification, and changes; `tests/` holds future offline checks. `docs/runbooks/`
will hold approved operating and recovery procedures. These directories do not
yet contain an implementation.
