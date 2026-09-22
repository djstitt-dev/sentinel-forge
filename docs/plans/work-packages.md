# Work packages and approval gates

Work Packages 2 and 4A were committed. WP4B host preflight stopped safely at a
stale OS gate, according to the operator. Current authorization is repository-only
WP4B identity/provenance reconciliation finalization, validation, and commit.
Stop after commit and verification; no host preflight or execution is authorized.
This plan does not authorize other packages.
Operational readiness remains unverified.

| Package | Deliverable and acceptance condition | Approval gate |
| --- | --- | --- |
| 1. Context identity | Preserve the operator's sandbox/host distinction; establish actual host execution context before future host observations. | Explicit scope for renewed host discovery; privilege requires separate approval. |
| 2. Repository governance | Governance, layout, context inventory, evidence manifest, ignore rules, and repository-local validation. | Operator approved finalization and the initial governance commit; stop after the commit. |
| 3. Baseline discovery | Context-labeled control inventory and authorized anchor checks; inaccessible state recorded as unknown. | Authorize discovery scope; separately approve privileged inspection or accept operator-provided results. |
| 4. K42 review | Determine whether a final record exists and review what closure can attest. | Separate approval to write a closure record; no AIDE promotion implied. |
| 4A. K42 procedure preparation | [Proposed closure specification](f117k42-closure.md), host script, and synthetic offline tests. | Repository-only finalization and commit approved; stop after commit and verification without host execution. |
| 4B. Host preflight reconciliation | Preserve the superseded OS assertion, record operator-verified host identity, and correct preflight expectations. | Repository-only finalization and commit approved; stop after commit and verification without host preflight or K42 execution. |
| 5. Operational requirements | Define interfaces, trust boundaries, access, monitoring, recovery objectives, and measurable acceptance criteria. | Operator architecture and security approval. |
| 6. Implementation preparation | Reviewed configuration proposals, offline checks, exact change plans, stop conditions, verification, and rollback. | Approved repository scope; no implicit host application. |
| 7. Host changes | Bounded approved changes with before/after evidence in the correct context. | Explicit host/security approval; any AIDE trust transition separately approved. |
| 8. Operational acceptance | Verify required functionality, controls, monitoring, recovery, and runbooks. | Operator accepts readiness and separately authorizes deployment as applicable. |

Unresolved: original collection times and privilege contexts of supplied host
evidence; current anchor state; final K42 record existence; detailed operational
requirements; effective host controls and recovery readiness. No host checks or
K42 closure work are part of Work Package 2.
