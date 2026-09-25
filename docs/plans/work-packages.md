# Work packages and approval gates

Repository history documents Work Packages 2 and 4A as committed and the WP4B
host preflight as stopped at a stale OS gate. Its prior reconciliation/commit
authorization is historical. WP5 architecture/security review was subsequently
approved by the operator and committed at revision
`0ce6457b31c7d798bf00626aeaeaeb963a103e52`.

Current authorization is **bounded repository-only WP6.1 Forge/Courier/Scribe
implementation preparation and offline validation**. Runtime implementation,
host discovery or mutation, network connectivity, credentials, privileged
execution, deployment, Conduit execution and AIDE actions remain unauthorized.
Operational readiness remains unverified.

The operator's 2026-09-25 FORGE PRIVILEGED HOST CONTEXT observation establishes
K42 record existence. See the [dated provenance and format reconciliation](../inventory/execution-contexts.md#k42-reconciliation-supplied-2026-09-25).
Preserve the historical record; do not regenerate/replace/overwrite it. The current
writer's provenance is not established and its output format differs. Historical
PASS is not a current live AIDE-clean assertion; candidate lifecycle remains deferred.

| Package | Deliverable and acceptance condition | Approval gate |
| --- | --- | --- |
| 1. Context identity | Preserve the operator's sandbox/host distinction; establish actual host execution context before future host observations. | Explicit scope for renewed host discovery; privilege requires separate approval. |
| 2. Repository governance | Governance, layout, context inventory, evidence manifest, ignore rules, and repository-local validation. | Operator approved finalization and the initial governance commit; stop after the commit. |
| 3. Baseline discovery | Context-labeled control inventory and authorized anchor checks; inaccessible state recorded as unknown. | Authorize discovery scope; separately approve privileged inspection or accept operator-provided results. |
| 4. K42 review | Historical existence uncertainty superseded by the 2026-09-25 supplied observation; preserve the record and provenance limitations. | No recreation of the existing record; any further evidence action needs separate scope/approval. |
| 4A. K42 procedure preparation | [Proposed closure specification](f117k42-closure.md), host script, and synthetic offline tests. | Repository-only finalization and commit approved; stop after commit and verification without host execution. |
| 4B. Host preflight reconciliation | Preserve the superseded OS assertion, record operator-verified host identity, and correct preflight expectations. | Repository-only finalization and commit approved; stop after commit and verification without host preflight or K42 execution. |
| 5. Operational requirements | [Approved architecture](../architecture/forge-operational-architecture.md) and [requirements/decision register](wp5-operational-requirements.md): responsibilities, interfaces, authority, audit, failure, recovery and measurable acceptance. | Operator architecture/security approval completed; committed at `0ce6457b31c7d798bf00626aeaeaeb963a103e52`. This approval does not authorize runtime implementation, host action or deployment. |
| 6. Implementation preparation | [WP6.1 preparation plan](wp6-forge-courier-scribe-preparation.md), [Forge/Courier/Scribe logical contract](../architecture/forge-courier-scribe-contract.md), offline checks, exact change plans, stop conditions, verification and rollback. | Bounded repository-only WP6.1 preparation authorized; no implicit runtime, host, network, credential, privileged, deployment, Conduit or AIDE action. |
| 7. Host changes | Bounded approved changes with before/after evidence in the correct context. | Explicit host/security approval; any AIDE trust transition separately approved. |
| 8. Operational acceptance | Verify required functionality, controls, monitoring, recovery, and runbooks. | Operator accepts readiness and separately authorizes deployment as applicable. |

Unresolved: original collection times and privilege contexts of earlier supplied
host evidence; current live anchor state; actual K42 creator/procedure; effective
host controls and recovery readiness; and capability-scoped decisions DEC-06
through DEC-13 where they become active dependencies.

WP5 approval does not authorize host checks or K42 closure work. Entry into
bounded repository-only WP6.1 preparation was separately authorized by the
operator; that authorization does not extend to runtime implementation, host
changes, network connectivity, credentials, privileged execution, deployment,
Conduit execution or AIDE actions.
