# Architecture and governance

Status: operator-approved repository organization, implemented in Work Package 2.
This document does not approve a runtime architecture or host deployment.

## Repository responsibilities
| Path | Responsibility |
| --- | --- |
| `AGENTS.md` | Operator authority, scope, evidence contexts, stop conditions |
| `docs/architecture/` | Component boundaries, data flows, decision records |
| `docs/inventory/` | Context-labeled observations and unknowns |
| `docs/plans/` | Work packages, approval gates, acceptance criteria |
| `docs/runbooks/` | Future verification, operation, recovery, rollback procedures |
| `config/` | Reviewed desired-state configuration; no implicit deployment |
| `scripts/discovery/` | Future read-only inspection tools with documented effects |
| `scripts/verify/` | Future verification tools with documented effects |
| `scripts/changes/` | Future separately approved change procedures |
| `tests/` | Offline checks and sanitized fixtures |
| `evidence/manifests/` | Provenance and references to evidence retained externally |

Empty reserved directories contain `.gitkeep` so future Git commits can preserve
the layout. No executable change scripts or host configuration are introduced.

## State and approval model
Observed state must identify execution context, collector, provenance, and time
when known. Proposed desired state is a proposal until the operator approves its
application. Verified applied state requires evidence of execution and checks in
the appropriate context. A Git commit establishes neither approval nor deployment.

Approval-required proposals must specify scope, affected resources, expected
effects, verification, stop conditions, and rollback. Preserve historical evidence
and rollback paths. Stop affected work on unexplained state. Never weaken a
control to pass a check or autonomously alter an AIDE trust anchor.

## Boundaries and unresolved architecture
Codex sandbox state is separate from both Forge host execution contexts. Explicit
provenance must survive any later comparison across contexts. AIDE databases and
trusted history remain in their established host locations; this repository holds
references, not copies of those databases.

Forge interfaces, data flows, external dependencies, access model, monitoring,
recovery objectives, and operational acceptance criteria remain unknown. No
choices about these runtime boundaries are implied by the repository layout.
