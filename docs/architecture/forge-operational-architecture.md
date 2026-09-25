# Forge operational architecture

Status: WP5 DRAFT — proposed desired state; OPERATOR REVIEW REQUIRED.
Prepared 2026-09-25 in CODEX SANDBOX CONTEXT. DEC-01 through DEC-05 and DEC-14 through DEC-16 have
operator architectural approval dated 2026-09-25; DEC-06 through DEC-13 have
explicit capability-scoped deferral dispositions for the initial bounded
Forge/Courier/Scribe capability where they are not active dependencies. WP5 itself
remains pending review. No runtime implementation, deployment, verified application
or operational readiness is asserted.

## Scope and non-goals

Forge's intended purpose is a hardened build/development environment. This draft
specifies responsibilities and requirements for future implementation planning.
The [requirements and decision register](../plans/wp5-operational-requirements.md)
is the normative proposal for acceptance tests and unresolved choices.

WP5 authorizes repository documentation and offline validation only. Host
discovery, runtime implementation, deployment, connectivity, privilege escalation,
package/service changes, AIDE execution or trust transitions, closure creation,
and Git commits/branch changes are excluded. Named components imply no approved
connection, credential, protocol, port, or trust relationship.

## Basis and state distinctions

Repository facts were read by Codex in CODEX SANDBOX CONTEXT on 2026-09-25 using
`cat`, `rg`, and read-only Git commands; exact observation times were not captured.
Sources: [governance](governance.md), [work packages](../plans/work-packages.md),
[contexts](../inventory/execution-contexts.md), and [evidence rules](../../evidence/README.md).
These establish repository rules and historical assertions, not current host controls.
The seven component meanings below come from the operator's WP5 instruction;
the repository previously did not independently establish their runtime roles.

| State class | Treatment in this package |
| --- | --- |
| Observed state | Codex repository observations only, labeled CODEX SANDBOX CONTEXT. |
| Operator-supplied state | Ecosystem meanings and dated host observations retain source and context. |
| Proposed desired state | Interfaces, flows and operational requirements remain draft except for the explicitly approved DEC-01 through DEC-05 and DEC-14 through DEC-16 architectural dispositions and the explicit capability-scoped deferrals for DEC-06 through DEC-13. Deferral does not create an executable default. |
| Approved desired state | Operator approved DEC-01 through DEC-05 and DEC-14 through DEC-16 architectural dispositions on 2026-09-25 and explicitly deferred DEC-06 through DEC-13 for the initial bounded Forge/Courier/Scribe capability where they are not active dependencies; see the decision register for source and exact scope. Deferral creates no executable default. This does not approve WP5 as a whole or runtime execution. |
| Verified applied state | Requires separately authorized execution and verification in the actual target context; unavailable here. |

FORGE USER HOST CONTEXT and FORGE PRIVILEGED HOST CONTEXT must remain distinct
from CODEX SANDBOX CONTEXT. Account names and matching OS values cannot establish
context. The [2026-09-25 K42 reconciliation](../inventory/execution-contexts.md#k42-reconciliation-supplied-2026-09-25)
records supplied historical existence and format mismatch; it grants no new trust
and makes no current live AIDE-clean assertion. Candidate lifecycle remains deferred.

## Component responsibilities and authority boundaries

The operator's “SENTINEL COMPONENT ROLE BOUNDARIES” instruction supplies the
role constraints below, recorded by Codex in CODEX SANDBOX CONTEXT on 2026-09-25.
These are architectural boundaries, not verified runtime controls or approval
of WP5 as a whole. Detailed acceptance requirements remain part of the draft.

| Component | Intended responsibility | Boundary and excluded authority |
| --- | --- | --- |
| Forge | Engineering, build, planning and AI-assisted orchestration inside authorized development/work-package boundaries. | May edit authorized source/configuration, run approved build/test/security validation, prepare proposed artifacts/evidence and bounded Courier/Conduit requests, and coordinate AI development. Not release, monitoring, unrestricted security-analysis, deployment or evidence trust-anchor authority. |
| Scribe | Controlled release and evidence authority; determines whether packages satisfy applicable release/evidence policy. | Forge, Reaper, Courier, Conduit and models cannot declare Scribe-controlled release state. Build/test/scan/transfer/Conduit success is not release approval. Protected evidence and trust anchors remain outside Forge/AI workload modification rights unless separately and explicitly authorized. |
| Courier | Independent controlled-transfer authority under approved DEC-03. | Independently verifies transfer authorization and integrity; receipts record disposition, including partial/unknown state, and confer no release/deployment authority or ambient downstream write rights for Forge. |
| Conduit | Independent policy-enforced management/deployment boundary for bounded Forge logical requests under approved DEC-01. | Distinct from Courier, Scribe, Forge and AI reasoning authority. Conduit independently verifies exact operation authorization; reachability grants no general administration. Network/session initiation remains undecided. |
| Reaper | Dedicated security-analysis execution boundary; defensive-by-default, bounded fuzzing, vulnerability scanning, artifact inspection, static/dynamic analysis, Trivy or equivalent approved scanners, and other explicitly authorized defensive tasks. | Forge/AI requests need an approved interface and independent Reaper execution authorization. Offensive, exploitative, active-adversary, interception or other elevated testing needs separate explicit operator authorization and applicable policy. Findings cannot authorize changes, exceptions, release or deployment. |
| Watchtower | Observation, monitoring and alerting authority: approved telemetry collection/receipt, status and health observation, alert generation and authorized audit/event correlation. | Observation grants no management/deployment channel. Inbound query/pull requires an approved contract. Findings may notify the operator or propose work, investigation or remediation; they cannot independently authorize host changes, Forge work, Reaper execution, release or deployment. |
| Cerberus | Administrative workstation. | Workstation identity is not operator approval; administration requires scoped identity and authorization. |
| Operator | Sole architecture/security approval authority. | Approves exact actions and boundaries; automation cannot broaden this authority. |

Forge owns proposed local build execution records and candidate lineage. Scribe
owns controlled release/evidence decisions; the operator governs authority changes.
An evidence copy or monitoring acknowledgement cannot become an authority transfer.

### Separate component authority domains

Forge, Reaper, Scribe and Watchtower are separate trust/authority domains, regardless
of future placement or connectivity. Forge's approved local engineering validation
does not grant unrestricted analysis authority or replace Reaper's dedicated
execution boundary. Naming Trivy describes a possible approved analysis workload;
it does not select, install or authorize any scanner execution in WP5.

Courier moves only explicitly authorized artifacts/evidence between approved
boundaries; creation, analysis, transfer, release and deployment authority remain
separate. Conduit executes only exact authorized operations against exact authorized
targets; it enforces authorization and cannot create it. Reachability grants no
administration. Scribe release state alone grants no deployment authority.

Communication never transfers another component's authority. Forge may prepare a
Reaper request but cannot grant Reaper new rights; a Reaper finding cannot approve
a fix. Watchtower may propose investigation/remediation, but execution requires a
separate authorized work package/action, including any Forge or Reaper work. AI
output grants authority to none of these components. Findings and receipts remain
evidence; approval comes from the applicable independent authority boundary.

Every cross-component operation must preserve caller/source identity, exact target
component, exact operation, applicable work-package revision, authorization reference,
artifact/evidence identity where applicable, policy/classification, correlation
identity, outcome/disposition and unknown/partial state where applicable. No wildcard
component authority may be inferred. FORGE-AUTH-004 through FORGE-AUTH-006 and
FORGE-IF-006 define future acceptance evidence for these constraints. No protocol,
port, API, credential, topology or runtime technology is selected here.

## Trust-boundary model

| Boundary | Trust decision and proposed enforcement responsibility |
| --- | --- |
| Operator intent → action | Receiving action boundary checks explicit scope, affected resources, authorization validity, verification, stop conditions, and recovery plan. |
| Human administration → Forge management | Forge management boundary verifies approved identity/role and target before any action; administrative path is unresolved. |
| Source/dependency → build workload | Forge intake verifies approved origin, identity, integrity, version/freshness and provenance before use; executing source remains untrusted. |
| Build workload → management/evidence | Forge must isolate workload rights from privileged control, credentials and protected evidence; isolation mechanism is unresolved. |
| Forge → Reaper analysis | Reaper independently checks approved interface, exact defensive task/target and execution authorization; Forge/AI planning grants no Reaper authority. Elevated testing requires separate explicit operator authorization/policy. |
| Candidate/findings → Scribe decision | Scribe applies its release/evidence policy independently; successful work in any other domain cannot declare release state or modify protected Scribe evidence/anchors. |
| Telemetry/findings → Watchtower → proposed response | Collection/query is independently scoped; observations may generate alerts/proposals but cannot authorize management, Forge/Reaper work or deployment. |
| Forge → external component | Each receiver independently validates identity, object, policy and scoped permission. Transport success does not establish trust. |
| Live state → recovery state | Recovery authority verifies provenance, completeness and freshness before use; restore does not establish trust in historical anchors. |
| Sandbox → host evidence | Collector/context/time/command and verification status remain attached; sandbox findings cannot attest host state. |

No architecture diagram here represents deployed connectivity. Logical submission
and decision flow, contingent on approved interface choices:

```text
Approved source/dependency intake -> Forge build -> candidate + build evidence
Forge -> controlled staging -> Courier independent transfer checks
Courier -> explicit authorized destination (e.g. Scribe review)
Courier -> Forge: attributable transfer receipt/disposition
Scribe review -> controlled release/evidence decision (separate from transfer)
Forge -> Reaper -> analysis findings -> Forge and/or Scribe (routing unresolved)
Forge -> Watchtower observation boundary (export model unresolved)
Cerberus -> approved administrative path -> Forge (path unresolved)
Forge -> Conduit: bounded logical operation request (DEC-01)
Conduit -> exact authorized target: independently permitted operation
Target/Conduit -> Forge: correlated disposition/outcome (transport undecided)
```

The arrows represent payload intent, not who opens a connection. Direct versus
mediated acknowledgements, return routes and network sessions remain decisions.
No Scribe-to-deployment flow is implicitly approved by this diagram.

### Approved default-deny inbound boundary

DEC-02 is OPERATOR ARCHITECTURE DECISION — APPROVED 2026-09-25. Its source is the
operator's DEC-02 decision update; the [full disposition](../plans/wp5-operational-requirements.md#approved-inbound-architectural-disposition--2026-09-25)
records the approved boundary and future acceptance cases. Forge shall default-deny
inbound connectivity. No listener, management path, callback, peer-initiated session
or remote operation is authorized by reachability or technical capability.

Only an explicitly approved purpose-specific inbound interface contract may admit
a path. It must define purpose, initiator/principal, receiver/service role, logical
request direction, authentication, authorization, action/resource scope, data
classification, work-package/policy binding, freshness/replay, rate/resource bounds,
timeout/failure, audit/evidence and revocation/disable behavior. Unspecified inbound
traffic and operations remain denied. This applies across all logical interfaces.

The receiving Forge boundary independently establishes identity, authorization,
target/action scope and policy before security-sensitive effects. Address/hostname
knowledge, listening services, transport connectivity, successful TLS/session
establishment, source network/location, component naming, prior communication and
reachability alone confer no authority.

Deny before consequential effect for a non-enabled interface, unknown caller,
absent/expired/revoked/mismatched authorization, out-of-scope target/action,
missing/stale required work-package/policy binding, failed replay/freshness checks,
unavailable required validation/audit, unresolved request or prior sensitive outcome,
or an observation/transfer interface being used as a management channel. An
available interface cannot relax these checks.

Cerberus inbound administration remains conditional on DEC-11 and its approved
contract; no direct or Conduit-mediated route or SSH is chosen. DEC-01 permits a
Forge-originated logical request but requires no inbound Conduit connection; any
Conduit-initiated inbound path needs its own contract. Watchtower pull/query needs
explicit inbound approval and cannot grant general management authority. DEC-14
provider approval permits no implicit inbound management, callback, webhook or
provider-initiated session; each inbound behavior needs explicit interface approval.

IP addressing, topology, firewall technology, ports, SSH, TLS/mTLS, VPN, Conduit
transport, APIs, services/daemons, certificates/keys, user/service accounts,
authentication technology, network zones/VLANs and callback/webhook mechanisms
remain later bounded choices. No network/firewall/service configuration or host
connectivity is enabled or authorized by this architectural decision.

## Proposed logical interfaces and data flows

Every interface below is disabled for implementation purposes until its decisions
are approved. Each requires an interface contract covering both request and
response, principal, target, payload schema/version, classification, authorization,
freshness, limits/timeouts, acknowledgement, retries, audit and failure behavior.
No protocol, address, port, account, certificate or key is selected.

| Interface | Proposed payload direction and objects | Receiver's trust decision / authority limit | Decisions |
| --- | --- | --- | --- |
| IF-01 Intake | Approved source/dependency provider → Forge; source revisions, toolchain/dependency objects, manifests; Forge → provider request if allowed. | Forge verifies approved origin and pinned identity/integrity; source cannot grant itself execution privileges. | DEC-04, DEC-05, DEC-06, DEC-13 |
| IF-02 Artifact handoff | Forge → controlled staging → Courier → explicit authorized destination; candidates/evidence and bound metadata. Courier → Forge receipt/disposition; Scribe decisions use separately approved routes. Logical directions do not select transport/session initiation. | Approved DEC-03: Courier independently verifies authority, identity/integrity, destination and policy/prerequisites. Staging grants no transfer authority; receipts confer no release/deployment approval. See boundary below. | DEC-03, DEC-04, DEC-05, DEC-12 |
| IF-03 Management/deployment | Forge → Conduit bounded logical request → exact authorized target operation; correlated disposition/outcome returns to Forge. Network/session initiation and transport remain undecided; inbound Conduit paths require a DEC-02 contract. | Approved DEC-01: Conduit independently verifies revision-bound operation authority, exact target/input identity, freshness and evidence; Forge acquires no general administrative authority. See contract below. | DEC-01, DEC-02, DEC-04, DEC-05, DEC-11, DEC-12 |
| IF-04 Analysis | Forge → Reaper candidate/test inputs; Reaper → approved recipient findings and job status. | Reaper independently checks interface and execution authority for the exact bounded defensive task; elevated testing needs separate explicit operator authorization/policy. Recipient binds findings to input/job; findings authorize no source/trust-anchor change, security exception, release or deployment. | DEC-04, DEC-06, DEC-13 |
| IF-05 Observation | Forge → Watchtower events/health; delivery acknowledgements if selected. Pull/query requires an explicit DEC-02 inbound contract, without general management authority. | Watchtower authenticates origin and correlates approved telemetry/alerts; Forge limits disclosure. Observation/query creates no command channel; findings may notify or propose work, never authorize Forge/Reaper execution, host changes, release or deployment. | DEC-02, DEC-04, DEC-07, DEC-08 |
| IF-06 Administration | Cerberus → approved path → Forge scoped administrative intent; Forge → approved path → Cerberus outcome. Inbound access requires DEC-11 disposition and a DEC-02 contract; direct versus Conduit mediation unresolved. | Forge checks human/workload identity, operator authorization and permitted privilege; workstation trust is insufficient. | DEC-02, DEC-04, DEC-05, DEC-11 |
| IF-07 Recovery | Forge → approved backup custodian selected state; custodian → isolated recovery target for approved restore. | Custodian enforces custody/access; recovery authority validates origin, completeness and restore scope before resumption. | DEC-04, DEC-05, DEC-09, DEC-10 |
| IF-08 Time | Approved time source → Forge time observations; queries from Forge only if approved. | Forge assesses source trust and uncertainty; a timestamp alone proves neither freshness nor order. | DEC-06, DEC-08 |
| IF-09 Operator Mission / AI Orchestration | Operator → intake → planner → policy evaluation; approved bounded task → adapter ↔ approved model/provider; generated proposal via tool broker → isolated workspace → validation → evidence/result → operator review. | Independent policy and authorization govern model/tool execution; output confers no authority. Detailed stages below; result approval cannot authorize release/deployment implicitly. DEC-14 grants no inbound callback/session authority; DEC-02 requires explicit approval. | DEC-02, DEC-04, DEC-05, DEC-06, DEC-07, DEC-13, DEC-14, DEC-15, DEC-16 |

### IF-02 approved Courier boundary

DEC-03 is OPERATOR ARCHITECTURE DECISION — APPROVED 2026-09-25, sourced to the
operator's DEC-03 update. The [full Courier disposition](../plans/wp5-operational-requirements.md#approved-courier-architectural-disposition--2026-09-25)
defines package/receipt fields and future acceptance obligations. Forge prepares
artifacts/evidence only within authorized scope through controlled staging;
Courier independently authorizes/verifies transfer. Forge acquires no ambient write
authority over Scribe, destination hosts or downstream evidence/release stores.
Creation, transfer authorization, execution, destination acceptance, release and
deployment are distinct. A successful build cannot authorize transfer.

Packages bind applicable source identity, exact authorized revision, transfer
authorization, object identity and digest/equivalent immutable identity, type,
workspace/build, explicit destination, purpose/disposition, policy/classification,
transfer semantics and operation/correlation identity. Unavailable provenance is
not fabricated. Staged content remains distinct from transferred/accepted content;
Forge cannot declare its own transfer or release success. Unauthorized replacement
after authorization must be detectable. Wildcard/unspecified destinations are
prohibited and authority stays bound to the exact operation.

Before transfer, Courier independently checks source/requester, authorization and
revision where applicable, object identity/integrity, destination, transfer policy,
data-handling/classification, freshness/replay and applicable release/evidence
prerequisites. Required identity, integrity, authority, destination or policy that
cannot be established causes rejection/fail-closed handling. Required Scribe release
state uses an independently valid reference, never only a Forge assertion.

Courier's attributable receipt/disposition binds applicable operation/correlation,
source/destination, digest, authorization, revision, start/end time or ordered events,
disposition, destination acknowledgement, validation, failure/partial/unknown and
retry/reconciliation state. Forge consumes it as evidence only. UNKNOWN/PARTIAL
persist when delivery/acceptance cannot be proven; sensitive retries wait for
outcome reconciliation, with duplicate/replay handling at the destination and
attribution to the original or superseding authorized operation.

Scribe retains release/evidence authority. Neither transfer nor its receipt grants
release/deployment approval. AI-generated material remains untrusted pending
validation/authorization, and cannot authorize transfer; Forge's scope controls
and Courier's independent checks both apply. Courier remains distinct from Conduit.
Any inbound transfer path remains subject to DEC-02; preparation chooses no path.
Staging technology, media/layout, API/protocol, socket direction, push/pull,
encryption, keys/certificates, queue/broker, daemon, credentials, network path,
destination service, retention duration and receipt format remain later bounded
decisions. This approval creates no transfer mechanism or runtime configuration.

### IF-03 approved Conduit boundary

DEC-01 is OPERATOR ARCHITECTURE DECISION — APPROVED 2026-09-25, sourced to the
operator's DEC-01 decision update and recorded in the
[approved Conduit disposition](../plans/wp5-operational-requirements.md#approved-conduit-architectural-disposition--2026-09-25).
Forge may initiate a logical request only for an exact operation permitted by the
exact authorized work-package revision and applicable operator/security policy.
Conduit independently verifies it; Forge's assertion is insufficient.

The request binds principal, exact authorized revision, authorization reference,
exact target and operation, required input/artifact identity, freshness/replay
identity, applicable policy, expected outcome/effect class and evidence/correlation
identity. Conduit rejects wildcard/unspecified targets, out-of-scope operations,
stale/replayed authority, target/artifact mismatch, missing authorization/evidence,
unestablished authority and reachability-based administrative claims.

Successful Forge builds, Courier transfers and model reasoning confer no execution
authority. Scribe release authority remains separate: deployment requires separately
applicable authorization/policy explicitly permitting the operation. AI-originated
requests must pass Forge's work-package/policy/tool-broker controls and Conduit's
independent validation; approval of an AI workflow cannot bypass either boundary.

Operation identity must detect replay, duplicates and uncertain outcomes. UNKNOWN
sensitive outcomes remain UNKNOWN; automatic sensitive/privileged retries are
prohibited until prior outcome reconciliation under approved policy. Both Forge
and Conduit preserve correlated request, requester, authorized revision, target,
policy/authorization decision, execution disposition and validation/outcome evidence,
including unknown, partial and failure states.

Network/session initiator, protocol, API, port, certificate/key technology,
credentials, target agents/daemons, push/pull transport and deployment technology
remain later decisions. This architectural approval enables no connectivity,
Conduit execution, credentials, target agents, deployment or WP6 work.

## AI orchestration trust boundary

The operator's WP5 review amendment supplies the intended AI-assisted engineering
model. DEC-14 through DEC-16 now have operator architectural approval; the
[decision register](../plans/wp5-operational-requirements.md#operator-decision-register)
records the source and full dispositions. This is not an implemented engine. AI may
infer tasks; AI must not infer additional authority. Natural-language operator
intent is not unrestricted executable authorization. Model output is untrusted
proposed input until independently validated under the applicable policy and
approval boundary. Policy/authorization remains authoritative over models and tools.

### Mission representation and controlled self-development

| Representation | Meaning and authority limit |
| --- | --- |
| Operator intent | Requested outcome and constraints; does not authorize every useful planner action. |
| Proposed work package | Versioned plan with scope, resources, tool classes, validation, stop conditions and recovery expectations; no execution grant. |
| Authorized work package | Exact revision bound to applicable operator authorization and policy, including expiry/cancellation and permitted autonomy. |
| Individual execution actions | Each action is checked against that revision, current authorization, role, target and remaining resource envelope before dispatch. |
| Resulting evidence/disposition | Attributable actions, changes, validation and operator decisions; failed, cancelled and unknown outcomes remain distinct from success. |

Scope changes produce a new/amended proposal and applicable approval, never silent
mission expansion. Approved DEC-16 requires canonical identity suitable for
cryptographic integrity binding/hash referencing, with actions and evidence bound
to the exact authorized revision. Cancellation/revocation removes authority from
affected pending work and requires reconciliation of in-flight sensitive actions.
Final signing, key custody implementation, encoding, database and transport remain
later implementation decisions; no mechanism is selected here.

“Forge builds itself out” means controlled self-development of Forge and other
Sentinel capabilities inside an approved work package. Many ordinary source edits,
compiles, tests and failed-test repairs may proceed autonomously inside that
package without repeated human approval. The agent cannot enlarge scope or
permissions, grant privileges, change its governing approval policy or trust
boundaries, approve its own work, weaken controls, suppress failures, reinterpret
unknown outcomes as success, alter protected evidence/trust anchors or deploy
because tests passed. Proposals affecting the governing policy may be documented,
but cannot take effect for the same work package; they require separate operator
review and authorization. The authoritative policy, validator and evidence custody
must remain outside the generated workload's modification rights.

### Logical stages and enforcement responsibilities

| Stage / boundary | Proposed responsibility and enforced limit |
| --- | --- |
| Human/operator → mission intake | Attribute mission identity and distinguish intent from scoped authorization; reject approval claims embedded in untrusted content. |
| Mission intake → planner/work-package generation | Convert intent to a versioned proposal; retain constraints and unknowns without granting authority. |
| Planner → policy/authorization evaluation | Evaluate scope, resources and mandatory approvals independently of model output; refer missing/new authority to the operator. |
| Operator approval boundary → authorized task | Bind approval to exact work-package revision; cancellation/amendment invalidates affected pending actions under approved rules. |
| Authorized task → AI/model adapter | Supply only permitted task/context within approved data and resource bounds; adapter cannot widen authority. |
| Adapter ↔ approved model/provider | Separate trust boundary even when using a local model; external disclosure needs approved data classification, provider identity/version and retention/privacy policy. Returned content remains untrusted. |
| Model reasoning → tool broker | Policy-enforced broker or equivalent checks every requested action independently of the model, including arguments, target, role, work-package revision and current authorization. Deny unspecified actions. |
| Broker → isolated development workspace | Apply generated proposals and execute only authorized work within approved isolation; no direct model-to-consequential-tool bypass. |
| Workspace → validation subsystem | Independently assess build/test/security results against approved criteria; model-authored tests or success claims cannot replace mandatory validation. |
| Validation → evidence/provenance subsystem | Preserve changes, actual tool actions, results, failures and unknowns across iterations; workload cannot rewrite authoritative records. |
| Evidence/result → operator review | Present proposed result and unresolved outcomes; model cannot issue operator approval, release status or deployment authorization. |

### IF-09 logical flows

```text
Operator mission -> mission intake -> planner/work-package proposal
Proposal -> independent policy/authority evaluation
Evaluation -> operator authorization where required -> authorized bounded task
Authorized bounded task -> model adapter <-> approved model/provider
Model proposal/tool request -> independent policy-enforced tool broker
Broker -> isolated workspace -> build/test/security validation
Validation -> evidence and proposed result -> operator review/approval
Approved result -> separately authorized release/deployment path
```

These are logical payload directions, not network connection initiation. They
select no protocol, API, vendor, port, credential or deployment technology. Tool
results/context returned to a model remain untrusted and subject to disclosure
policy. Iteration feeds validated failure information back into planning within
the same authorized revision; expanding the package returns to proposal/approval.
Release remains with Scribe, transfer with Courier, and management/deployment
path with Conduit under separately approved contracts. IF-09 creates no bypass.

### Tool classes and bounded iteration

The broker must distinguish read-only repository operations, repository mutation,
test/build execution, network access, secret access, host inspection, privilege
escalation, host mutation, release actions and deployment actions. Each class
requires explicit role/work-package allowance plus action-specific scope checks;
a tool's existence or a model's ability to describe/request it grants nothing.
Compound actions and subprocesses cannot evade these checks. Allowed source edits
are not permission to modify the authoritative policy controlling the same work.

Approved DEC-15 permits bounded unattended engineering inside the exact authorized
revision and explicitly allowed tool classes: authorized reads; isolated workspace
file creation/edits; builds; approved tests/static/security analysis; artifact
inspection; failed-test repairs; explicitly approved model calls and network access;
and workspace recreation/discard where evidence and required recoverability survive.
These ordinary in-scope actions need no repeated approval. Mandatory stops include
unapproved escalation, host mutation outside the boundary, unauthorized secret
access, activation of governing policy/approval/validation changes, protected
evidence/trust-anchor changes, new network destinations, operator-gated architecture
or trust changes, release, deployment, scope expansion, unresolved sensitive retry,
unexplained identity/integrity/state, and bypass/weakening of required controls.

Maximum resource/iteration/concurrency limits, timeouts, workspace lifetime and
cancellation deadlines remain numerical WP6 implementation-preparation decisions.
Retry rules, cancellation and repeated unsuccessful repair-loop detection remain
required. No numeric limits are chosen or executable defaults implied.
The envelope is cumulative across retries and concurrent workers; restart cannot
reset it. Cancellation stops new dispatch and safely stops or reconciles in-flight
actions within approved deadlines; uncertain sensitive outcomes prohibit retry
until reconciled. Evidence persists across retries and workspace retirement.
Additional authority, new architecture/security decisions, exhausted resources,
prohibited actions, unapproved escalation, unexplained identity/integrity/state,
unknown sensitive outcomes or required-control bypass all stop affected iteration.

### Untrusted content and provider risks

Source code, repositories, documentation, issue text, build artifacts, external
content, model responses and retrieved context may contain instructions hostile
to operator intent. Reading them must never promote them to control-plane authority.
FORGE-AI-001 through FORGE-AI-011 and the AI threat matrix specify future acceptance
cases; this document does not claim the threats are currently mitigated.

Approved DEC-14 selects a hybrid architecture supporting local models and explicitly
approved external providers, each provider/model allowlisted by workload and data
classification. No provider is implicitly trusted and no automatic substitution is
permitted on outage, missing model or unavailable model/version. Provider/model
identity and version are recorded when available; unavailable provenance is unknown
and handled under approved admissibility policy. Secrets, authentication material,
protected evidence, release credentials and other prohibited data cannot be sent
externally merely because a model requests context. Disclosure must satisfy the
authorized work package, provider policy and classification/data-handling rules.
No vendor, API, model, protocol, credential mechanism or destination is selected;
these remain bounded WP6/later implementation decisions.

Future design under DEC-14 must still address local/external model trust,
permitted workloads/data, model and provider identity/version changes, prompt/context injection and poisoning, unsafe
code, hallucinated commands, suggested compromised dependencies, secret/sensitive
data disclosure, tool misuse, response tampering where applicable, outages,
retention/privacy and unavailable provenance. Missing identity or required
provenance cannot be invented; policy must decide admissibility and fail closed
where required information is unavailable. No automatic provider substitution or
model-version acceptance follows from failure. FORGE-AI-002 requires attributable,
redacted provenance or safe references without retaining secrets/sensitive prompts.

## External dependencies

Potential dependencies are approved source/toolchain providers, Courier, Scribe,
Conduit, Reaper, Watchtower, identity/custody facilities, backup storage, and time
sources, plus any separately approved local/external model provider and model
supply chain (DEC-14). DNS, registries, identity services, Internet access and external storage
are not assumed available or authorized. DEC-06 and DEC-13 must identify exact
providers, versions/pinning, supply-chain acceptance, ownership, availability and
failure impact. Dependency health and authenticity are separate checks.

Builds may be proposed to continue offline only when all required approved inputs,
authorizations and audit capacity remain valid. No network fallback, alternate
provider, bypass of required analysis, or local release decision is implied by an
outage. The operator must classify mandatory versus optional dependencies by operation.

## Identity and access requirements

FORGE-IAM-001 through FORGE-IAM-003 require a principal/action/resource matrix,
separation of human, workload and component roles, and explicit credential custody.
Proposed roles are operator approver, administrator, build worker, intake verifier,
transfer worker, analysis worker, observation publisher and recovery custodian;
these are logical roles, not accounts to create. Workload separation, credential
lifetimes, revocation, emergency access and authentication technologies remain
DEC-04, DEC-05, DEC-11 and DEC-13 decisions. Build code must not inherit human
sessions or credentials with management, release, or evidence alteration rights.

## Monitoring and audit requirements

FORGE-MON-001 through FORGE-MON-003 specify attributable allow/deny decisions,
job and object lineage, transfer progress and receipts, validation failures,
privilege attempts, dependency/clock health, recovery actions and export gaps.
Events must contain a correlation/operation ID, actor and target identifiers,
authorization reference, input/output identity where applicable, outcome/reason,
source context, collector/method, timestamp and uncertainty. Unknown fields must
be explicitly unknown rather than fabricated. Sensitive payloads and credentials
must be excluded; event classification, retention, redaction, custody and access
are operator decisions. Local audit and remote observation serve different roles.
Neither Watchtower availability nor a successful log write proves operation success.

## Failure and fail-closed requirements

The threat matrix in the plan applies to every interface, including responses.
Reject unauthorized, mismatched, tampered, stale or ambiguous requests before
security-sensitive effects. Partial results remain incomplete and unavailable for
release acceptance; preserve diagnostic evidence. Interrupted or duplicate work
must reconcile by operation identity before a retry; an unknown outcome is not a
successful outcome. No automatic retry may repeat a privileged effect whose prior
result is unknown. Dependency or required audit failure blocks affected actions.

Proposed local buffering of monitoring events must never silently drop required
evidence or overwrite historical evidence. DEC-07 must specify bounded capacity,
alert destination, detection/delivery deadlines, and stop/resume rules. Until those
are approved there is no authority to continue affected operations through an
outage. Clock ambiguity blocks time-dependent trust decisions and requires an
explicitly approved reconciliation path; no automatic acceptance by timestamp alone.

## Recovery requirements and objectives

Recoverable classes proposed for operator review: reviewed source/configuration,
build recipes and dependency manifests, irreplaceable work, operation journals,
artifact lineage, audit records, mission/work-package revisions, AI action and
iteration journals, redacted provenance and approved custody references. Reproducible
caches/build outputs may be rebuilt only after their dispensability is accepted.
Secrets require a separate approved custody/reissue scheme and never enter Git.
AIDE anchors/configuration/databases and trusted history remain protected evidence;
WP5 does not authorize copying, restoring, regenerating or replacing them.

DEC-09 chooses backup scope, custodian, storage boundary, confidentiality/integrity,
retention, verification and restore exercises; DEC-10 sets RTO/RPO per recoverable
class, maximum tolerable outage and recovery priorities. Numeric values remain
unknown. RTO measurement should span declared disruption to verified resumption;
RPO should measure the gap from the last validated recoverable state to disruption.
The operator must approve these definitions and treatment of uncertain timestamps.

Proposed recovery sequence: stop affected operations and preserve evidence;
authorize recovery scope; establish isolated target and trustworthy inputs; restore
or rebuild approved classes; verify integrity, identity, permissions, lineage and
audit continuity; reconcile incomplete operations; obtain operator resumption
approval. Recovery must not restore revoked authority, replay deployment actions,
or silently promote a candidate. Runbooks must define rollback to a preserved
state or safe halt where rollback would destroy evidence. FORGE-REC-001 through
FORGE-REC-003 define future demonstrations; none occurred in WP5.

## Security invariants

- The operator alone approves architecture/security boundaries and specific sensitive actions.
- AI may infer tasks but cannot infer authority; autonomy stays within the authorized work-package revision and resource envelope.
- Untrusted content/model output cannot govern policy, tools, validation or approval; cancellation and unknown outcomes retain their meaning.
- Forge produces candidates; Scribe retains controlled release/evidence authority.
- Courier transfer and Conduit management/deployment remain separate contracts and roles.
- Inbound connectivity is default-deny; each admitted path requires an explicit contract and independent receiver authorization, including callbacks and queries.
- Least privilege, explicit authorization, deterministic outcomes and fail-closed handling apply at every receiver.
- Reachability, names, locations, account names, transport success and equal hashes alone confer no trust or authority.
- Evidence retains provenance and state classification; historical evidence is preserved.
- Sandbox observations cannot establish either Forge host execution context.
- No AIDE trust transition, candidate lifecycle change, historical record replacement or live-clean assertion follows from this draft.
- Unknown identity, integrity, state or outcome triggers a stop for affected work and operator review, not autonomous normalization.

## Decision state and capability-scoped deferrals

DEC-01 through DEC-05 and DEC-14 through DEC-16 have operator architectural
approval dated 2026-09-25. DEC-06 through DEC-13 have explicit operator
capability-scoped deferral dispositions for the first bounded
Forge/Courier/Scribe capability where their unresolved mechanisms are not active
dependencies.

DEC-04 establishes distinct human/workload principals, authentication separate
from authorization, least-privilege/default-deny receiver-side authorization,
exact work-package binding where applicable, and explicit expiry/revocation.
Authentication technology remains deferred.

DEC-05 establishes component- and purpose-scoped credential custody. Forge
engineering/build/AI workloads do not acquire Scribe release/evidence-trust
credentials or Conduit deployment/privileged-management credentials merely
through their Forge role. Courier transfer credentials do not confer Scribe
release or Conduit deployment authority. Credential technology and storage
mechanisms remain deferred.

DEC-06 through DEC-13 are not silently resolved. Their unknown values shall not
become executable defaults. The initial Forge/Courier/Scribe capability may enter
later bounded preparation only where those deferred mechanisms are not active
dependencies. If preparation discovers a dependency on a deferred decision,
affected work stops at that dependency for operator disposition before dependent
execution.

The admitted initial capability is limited to the architecture in which Forge
prepares a revision-bound candidate/artifact/evidence package, Courier
independently verifies and controls transfer, Scribe independently evaluates
controlled release/evidence state, and attributable receipt/result information
returns as evidence.

That capability grants no Forge administrative access to Scribe, no Forge/AI or
Courier release authority, no automatic deployment, no Conduit execution
authority, no general-purpose inbound access, no general Internet egress, no
Watchtower command authority, no Cerberus administration and no production
readiness claim.

WP5 itself remains pending operator architecture/security review. These decision
dispositions do not authorize WP6, runtime implementation, host changes,
connectivity, credential creation, deployment or any AIDE operation.
