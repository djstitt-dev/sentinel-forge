# Project Sentinel Forge

Forge is a hardened Ubuntu Sentinel component. This repository will hold its
governance, reviewed configuration, verification procedures, and operational
documentation. Significant host hardening and AIDE baseline work predates it.
Forge's operational interfaces and acceptance criteria were established in the
operator-approved WP5 architecture and requirements. Bounded repository-only
WP6.1 implementation preparation is now authorized and in progress.

## Current status
Work Package 2 establishes repository governance only. No host configuration is
managed or applied by these files, and operational readiness has not been
verified. No F1.17K42 closure record is created here. The operator approved
finalization and the initial governance commit, completing Work Package 2.
Later work packages require their own authorization.
The operator subsequently authorized Work Package 4A, repository-only preparation
of the [K42 closure procedure](docs/plans/f117k42-closure.md) and offline tests.
The operator approved finalization and committing the Work Package 4A preparation.
Work Package 4A was committed. The subsequent WP4B host preflight stopped at the
OS gate. The operator approved repository-only reconciliation finalization and
commit; that historical authorization does not authorize current work.

WP5 architecture/security review was subsequently approved by the operator and
committed at revision `0ce6457b31c7d798bf00626aeaeaeb963a103e52`.

Current scope is bounded repository-only WP6.1 Forge/Courier/Scribe
implementation preparation and offline validation. Runtime implementation, host
discovery or mutation, network connectivity, credentials, privileged execution,
deployment, Conduit execution and AIDE actions remain unauthorized.

The operator's 2026-09-25 FORGE PRIVILEGED HOST CONTEXT observation establishes
existence of the historical K42 record. Preserve it without regeneration or
replacement. Current-writer provenance is not established; supplied format
evidence indicates that the current writer did not generate the exact record.
See the [dated reconciliation](docs/inventory/execution-contexts.md#k42-reconciliation-supplied-2026-09-25).
Historical PASS is not a current live AIDE-clean assertion. Candidate lifecycle
remains deferred.

WP4B operator reconciliation in FORGE PRIVILEGED HOST CONTEXT on 2026-09-22
establishes Ubuntu 26.04.1 LTS, kernel 7.0.0-31-generic, x86-64. It supersedes
the earlier operator-reported Ubuntu 24.04.4 assertion. Earlier Codex OS/kernel
observations happened to match; they remain CODEX SANDBOX CONTEXT evidence and
did not prove host context. See the context inventory below for provenance.

## Governance and entry points
The operator alone approves security-sensitive, architecture-changing,
destructive, privileged, and trust-boundary actions. Approval of repository work
does not authorize deployment or AIDE trust changes.

- [Agent rules](AGENTS.md)
- [Approved WP5 operational architecture](docs/architecture/forge-operational-architecture.md)
- [WP5 requirements and decision register](docs/plans/wp5-operational-requirements.md)
- [WP6.1 preparation plan](docs/plans/wp6-forge-courier-scribe-preparation.md)
- [WP6.1 Forge/Courier/Scribe logical contract](docs/architecture/forge-courier-scribe-contract.md)
- [Architecture and governance](docs/architecture/governance.md)
- [Execution contexts and initial observations](docs/inventory/execution-contexts.md)
- [Evidence handling and provenance](evidence/README.md)
- [Supplied AIDE anchor manifest](evidence/manifests/aide-anchors.json)
- [Proposed work packages](docs/plans/work-packages.md)

`config/` is reserved for reviewed desired state; `scripts/` separates discovery,
verification, and changes; `tests/` holds future offline checks. `docs/runbooks/`
will hold approved operating and recovery procedures. These directories do not
yet contain an implementation.
