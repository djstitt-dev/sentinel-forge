# WP5 operational requirements

Status: WP5 DRAFT — proposed desired state; OPERATOR REVIEW REQUIRED.
Prepared 2026-09-25 in CODEX SANDBOX CONTEXT. WP5 is not marked complete or
approved. DEC-01 through DEC-05 and DEC-14 through DEC-16 have operator architectural
approval dated 2026-09-25. DEC-06 through DEC-13 have explicit capability-scoped
deferral dispositions for the initial bounded Forge/Courier/Scribe capability
where they are not active dependencies. Deferral creates no executable default.
This is not runtime, deployment or verified-applied approval.

## WP5 scope and explicit non-goals

Authorized: repository reading, documentation, optional repository-only offline
validation, and a reviewable diff. Deliverables are this plan, the
[architecture draft](../architecture/forge-operational-architecture.md), and
careful historical reconciliation. Runtime requirements below specify future
acceptance obligations; they do not authorize their implementation or host tests.

Excluded: host discovery/configuration, runtime code/configuration, installation,
services, networking/firewall, SSH/authentication, external permissions/users,
sudo/escalation, AIDE checks or trust transitions, host evidence changes, closure
creation, deployment, commits/merges/rebases/pushes/branch changes, and WP6 work.
No existing authorization carries across a work-package boundary.

## Assumptions and known facts

| Classification | Fact or assumption | Source and verification |
| --- | --- | --- |
| Observed repository fact | Governance reserves host/security approval to the operator; existing scripts and synthetic offline tests concern K42. | Codex, CODEX SANDBOX CONTEXT, 2026-09-25; repository reads (`cat`, `rg`, Git), exact time not captured. Independently observed repository content only. |
| Operator-supplied architecture context | Forge, Scribe, Courier, Conduit, Reaper, Watchtower and Cerberus have the meanings reproduced in the architecture draft. | Operator WP5 instruction; no independent runtime verification. |
| Operator-supplied historical host fact | K42 record exists as observed 2026-09-25; historical PASS is not current live cleanliness; current writer did not produce the supplied exact format. | Operator, FORGE PRIVILEGED HOST CONTEXT; collection command/exact time unknown; [full provenance](../inventory/execution-contexts.md#k42-reconciliation-supplied-2026-09-25). No Codex host verification. |
| Historical repository fact | Prior WP4B preflight stopped at the OS gate; older existence uncertainty predates the supplied reconciliation. | Repository narrative and operator report; no inference of later successful preflight. |
| Operator-supplied AI intent | Future bounded AI-assisted engineering/orchestration and controlled self-development; model output grants no authority. | Operator WP5 review amendment; proposed architecture only, no implemented engine or independently verified runtime controls. |
| Planning assumption | Components are logical responsibilities; placement, installed services, connectivity and availability are unknown. | Proposal for structuring review, not observed host state. |
| Unknown | Operational readiness, effective controls, live anchors, candidate disposition, identities, endpoints, required capacity and recovery targets. | No host discovery authorized or performed. Candidate lifecycle remains deferred. |

Observed state, operator-supplied state, proposed desired state, approved desired
state and verified applied state must remain separate in all future records.
FORGE USER HOST CONTEXT, FORGE PRIVILEGED HOST CONTEXT and CODEX SANDBOX CONTEXT
are distinct; no host facts are derived from this session's sandbox commands.

## Component authority constraints

Source: operator's “SENTINEL COMPONENT ROLE BOUNDARIES” instruction, recorded by
Codex in CODEX SANDBOX CONTEXT on 2026-09-25. These architectural constraints
preserve separate Forge engineering/orchestration, Reaper security-analysis,
Scribe release/evidence and Watchtower observation/monitoring/alerting domains.
Courier transfer and Conduit management/deployment enforcement remain distinct.
This instruction selects no runtime technology and changes no DEC status; WP5
remains pending review. See the [component authority domains](../architecture/forge-operational-architecture.md#separate-component-authority-domains).

## Operator decision register

DEC-04 and DEC-05 were approved by the operator on 2026-09-25 for the
initial bounded Forge/Courier/Scribe capability. DEC-06 through DEC-13 received
explicit capability-scoped deferral dispositions on 2026-09-25; those deferrals
do not resolve the decisions for capabilities that later depend on them and do
not create executable defaults. DEC-01 was approved on
2026-09-25 in “WP5 OPERATOR DECISION UPDATE — DEC-01”, the approval
source/reference for its disposition below. DEC-02 was approved on 2026-09-25
in “WP5 OPERATOR DECISION UPDATE — DEC-02”, the approval source/reference
for the inbound disposition below. DEC-03 was approved on 2026-09-25 in
“WP5 OPERATOR DECISION UPDATE — DEC-03”, the approval source/reference for
the Courier disposition below. DEC-14 through DEC-16 were
approved by the operator on 2026-09-25 in “WP5 OPERATOR DECISION UPDATE — DEC-14
THROUGH DEC-16”; that instruction is the approval source/reference. Codex records
this supplied decision in CODEX SANDBOX CONTEXT; it is not host verification.
Earlier options below remain review history; the recorded dispositions govern.
Architectural approval does not authorize WP6, runtime implementation or deployment.
Options are illustrative viable models subject to requirements, not
an exhaustive technology shortlist. No evidence supports a particular protocol,
port, credential system, numerical service target or vendor.

| ID | Question / why it matters | Known constraints | Viable options and tradeoffs | Recommendation / recorded disposition | Status |
| --- | --- | --- | --- | --- | --- |
| DEC-01 | How does Forge interact with Conduit, and which side initiates which management/deployment operation? Determines authority and exposure. | Conduit is separate from Courier; no implicit deployment permission. | Forge submits bounded requests; Conduit initiates separately approved target actions; no interface in initial scope. Submission limits inbound exposure but still needs destination authority; initiated actions enlarge attack surface; exclusion limits capability. | APPROVED: Forge may initiate bounded logical requests only for exact operations permitted by an authorized work-package revision and applicable policy. Conduit independently enforces authorization, target/artifact identity, freshness and evidence requirements; no general administrative authority transfers to Forge. Network/session initiation and implementation choices remain undecided. See approved Conduit disposition below. | OPERATOR ARCHITECTURE DECISION — APPROVED 2026-09-25 |
| DEC-02 | Is any inbound connectivity to Forge permitted? Defines attack surface. | Reachability grants no authority; protocols/ports unapproved. | No inbound with outbound retrieval/export; narrow inbound from approved peers. First limits remote workflows; second needs independently enforced access and isolation. | APPROVED: DEFAULT-DENY inbound connectivity; only an explicitly approved purpose-specific interface contract may admit an inbound path. Forge independently checks identity, authorization, scope and policy before effects. No listener, connectivity, administration technology or callback is enabled by this decision. See approved inbound disposition below. | OPERATOR ARCHITECTURE DECISION — APPROVED 2026-09-25 |
| DEC-03 | How are artifacts handed to Courier and receipts returned? Affects custody and partial-transfer safety. | Transport cannot approve release; artifacts must bind to lineage. | Approved offline handoff; Forge push to controlled intake; Courier pull from bounded staging. Offline adds manual custody steps; push needs egress credentials; pull adds inbound/staging exposure. | APPROVED: controlled staging/handoff with independent Courier transfer authorization and verification; no ambient downstream write authority for Forge. Attributable receipts preserve UNKNOWN/PARTIAL and reconciliation state and confer no release/deployment authority. Staging/transport/receipt implementation remains deferred. See approved Courier disposition below. | OPERATOR ARCHITECTURE DECISION — APPROVED 2026-09-25 |
| DEC-04 | Which authentication, authorization and revocation model applies to each human and workload? Establishes accountable callers. | Least privilege, distinct roles and explicit authorization; identity alone is insufficient. | Managed short-lived workload identities; narrowly scoped managed credentials; operator-mediated offline authentication. Short-lived models depend on issuer/time; static credentials need rotation/revocation controls; offline mediation limits automation. | APPROVED: Sentinel uses distinct human and workload principals, least-privilege action/resource authorization, exact work-package binding where applicable, independent receiver-side authorization and explicit expiration/revocation. Authentication establishes identity only and does not itself confer authority. No shared universal Sentinel administrative identity is permitted. Authentication technology remains a later bounded implementation decision. See approved identity/authorization disposition below. | OPERATOR ARCHITECTURE DECISION — APPROVED 2026-09-25 |
| DEC-05 | Who holds, issues, rotates and recovers keys/credentials? Defines compromise scope. | No secrets in Git or build payloads; Forge cannot acquire release authority. | External custody with scoped issuance; protected local per-role custody; operator-mediated issuance. External custody adds dependency; local custody raises host compromise impact; mediation raises recovery latency. | APPROVED: credentials and keys are scoped by component role and purpose. Scribe release/evidence-trust credentials, Conduit deployment/privileged-management credentials and other consequential authority credentials remain outside Forge build-worker and AI workload rights. Secrets are excluded from Git, ordinary build artifacts, prompts/logs/evidence except approved redacted or safe references. Issuance, storage, rotation, expiry, revocation and recovery require attributable custody. Exact credential technology/storage remains a later bounded implementation decision. See approved credential-custody disposition below. | OPERATOR ARCHITECTURE DECISION — APPROVED 2026-09-25 |
| DEC-06 | What egress and external providers are allowed? Controls supply chain and data disclosure. | No implicit Internet, registry, DNS or alternative-provider permission. | Offline curated inputs; approved internal mirrors/services; narrowly listed external providers. Curation costs freshness/effort; mirrors add maintenance; external access expands exposure and outage risk. | DEFERRED FOR INITIAL CAPABILITY: no general network egress, Internet, registry, DNS, mirror or external-provider destination is authorized by this disposition. The first bounded Forge/Courier/Scribe capability may proceed only without depending on unapproved egress. Any capability requiring a network destination must resolve DEC-06 before dependent execution. | OPERATOR ARCHITECTURE DISPOSITION — DEFERRED FOR INITIAL FORGE/COURIER/SCRIBE CAPABILITY — 2026-09-25 |
| DEC-07 | How are events exported to Watchtower, retained and handled during failure? Determines evidence continuity and detection. | Observation is not command authority; required evidence cannot silently disappear. | Outbound export with bounded local journal; approved pull; operator-mediated export. Journals need capacity/custody, pull needs inbound authority, mediation adds detection delay. Select retention, redaction, capacity, recipients and alert/delivery/stop deadlines. | DEFERRED FOR INITIAL CAPABILITY: Watchtower export/retention/failure technology is not required to prepare the first bounded Forge/Courier/Scribe capability. Required local audit/evidence obligations remain mandatory and must not silently disappear. Any capability requiring Watchtower export must resolve DEC-07 before dependent execution. | OPERATOR ARCHITECTURE DISPOSITION — DEFERRED FOR INITIAL FORGE/COURIER/SCRIBE CAPABILITY — 2026-09-25 |
| DEC-08 | What time source, uncertainty tolerance and ordering model are required? Affects replay, expiry and forensic ordering. | Timestamp alone establishes neither trust nor freshness. | Approved authenticated source with uncertainty tracking; isolated time discipline plus operation sequencing. Online source adds dependency; isolation limits freshness guarantees. Set skew bounds, detection time and outage policy. | DEFERRED FOR INITIAL CAPABILITY: no trusted time source, skew tolerance or numeric freshness bound is selected. Operation/correlation identity, explicit ordering where available and UNKNOWN handling remain mandatory. No time-dependent authorization or replay control may assume guarantees not yet approved. Capabilities depending on such guarantees must resolve DEC-08 before execution. | OPERATOR ARCHITECTURE DISPOSITION — DEFERRED FOR INITIAL FORGE/COURIER/SCRIBE CAPABILITY — 2026-09-25 |
| DEC-09 | What is backed up, by whom, where and for how long? Defines recoverable scope and disclosure risk. | Protected AIDE evidence cannot be modified under WP5; secrets need separate custody. | Rebuild reproducible classes and back up irreplaceable state; broader approved encrypted backups. Minimal backups demand reproducibility; broad backups retain sensitive/stale state and need more custody control. Set retention and restore-exercise cadence. | DEFERRED FOR INITIAL CAPABILITY: no production backup scope, storage boundary, retention period or restore cadence is selected. The first capability must not depend on unapproved recovery assumptions. Protected AIDE evidence remains separately gated. Any admitted recovery dependency must resolve DEC-09 before execution. | OPERATOR ARCHITECTURE DISPOSITION — DEFERRED FOR INITIAL FORGE/COURIER/SCRIBE CAPABILITY — 2026-09-25 |
| DEC-10 | What RTO/RPO and maximum outage apply to each class/operation? Determines acceptable loss and recovery cost. | No fabricated numeric targets; recovery must preserve evidence. | Rebuild-first with longer recovery; prepositioned approved recovery copies with lower delay and greater custody cost. Decide priorities, measurement boundaries and data-loss acceptance per class. | DEFERRED FOR INITIAL CAPABILITY: no RTO, RPO or maximum-outage value is selected and no operational availability claim is authorized. Any capability whose acceptance depends on recovery or outage objectives must resolve DEC-10 before execution or operational acceptance. | OPERATOR ARCHITECTURE DISPOSITION — DEFERRED FOR INITIAL FORGE/COURIER/SCRIBE CAPABILITY — 2026-09-25 |
| DEC-11 | How does Cerberus administer Forge, including emergency access? Defines privileged path and accountability. | Workstation identity is not authority; no implicit direct SSH or bypass. | Approved Conduit-mediated administration; separately scoped direct path; controlled local administration. Mediation centralizes policy but adds dependency; direct path expands surface; local path increases response time. | DEFERRED FOR INITIAL CAPABILITY: Cerberus administration and emergency-access paths remain unapproved. The initial Forge/Courier/Scribe capability receives no SSH, direct-administration or implicit privileged path from this deferral. Any capability requiring Cerberus administration must resolve DEC-11 first. | OPERATOR ARCHITECTURE DISPOSITION — DEFERRED FOR INITIAL FORGE/COURIER/SCRIBE CAPABILITY — 2026-09-25 |
| DEC-12 | Who may request, approve and execute deployment, and how is Scribe's release decision verified? Prevents authority drift. | Operator is sole architecture/security authority; Scribe retains controlled release/evidence authority. | Operator-approved per-action execution through Conduit; later explicitly approved policy-bounded automation; defer deployment capability. Manual gates cost latency; automation needs precise delegation limits; deferral limits delivery. | DEFERRED FOR INITIAL CAPABILITY: deployment authority remains unavailable. Scribe release/evidence acceptance does not authorize deployment, and the first Forge/Courier/Scribe capability shall stop at controlled release/evidence disposition. Any deployment-capable scope must resolve DEC-12 before preparation of executable deployment behavior. | OPERATOR ARCHITECTURE DISPOSITION — DEFERRED FOR INITIAL FORGE/COURIER/SCRIBE CAPABILITY — 2026-09-25 |
| DEC-13 | Which build workloads, isolation model, required analysis and capacity limits are in scope? Defines safe input handling and reproducibility. | Untrusted build/test input gets no management, release or evidence-alteration rights. | Disposable isolated workers; dedicated separated build environment; narrow operator-driven workloads. Isolation costs resources; dedicated environments need lifecycle control; manual scope limits throughput. Set supported inputs, quotas, concurrency, timeouts, providers and required Reaper gates. | DEFERRED FOR INITIAL CAPABILITY: only the narrowly bounded workload needed to prepare the first Forge/Courier/Scribe capability may enter WP6 preparation. General workload classes, isolation technology, capacity, quotas, concurrency, timeouts and Reaper-gate policy remain unresolved. No executable default may be inferred; dependent workload execution must resolve the applicable DEC-13 choices first. | OPERATOR ARCHITECTURE DISPOSITION — DEFERRED FOR INITIAL FORGE/COURIER/SCRIBE CAPABILITY — 2026-09-25 |
| DEC-14 | Which local/external AI/model providers may serve which workloads, and what data may cross each boundary? Determines privacy, availability and supply-chain exposure. | Output remains untrusted; no provider choice or general egress grant; required identity/provenance cannot be fabricated. | Local models limit external disclosure but require model supply-chain/capacity controls; approved external providers add disclosure, retention/privacy and outage dependencies; hybrid use needs per-workload routing and substitution rules. Specify provider/model identity, version provenance/change review, permitted data, unavailable-provenance handling and availability policy. | APPROVED: hybrid local/external architecture; every provider/model allowlisted by workload and data classification, no implicit trust or automatic substitution. Record available identity/version and explicit unknowns under admissibility policy. Disclosure is bounded by work-package and data/provider policy. No vendor/API/model/protocol/credential/destination selected. See approved dispositions below. | OPERATOR ARCHITECTURE DECISION — APPROVED 2026-09-25 |
| DEC-15 | What autonomy envelope governs AI implementation/repair? Determines useful independence and reliable stopping. | No authority expansion; tool access independently enforced; isolation appropriate to workload; no numeric limits invented. | Bounded unattended iteration permits repeated edits/tests/repairs with aggregate limits; checkpoints at approved milestones reduce unattended duration but increase operator workload; exclude consequential tool classes where unnecessary. Define allowed classes, isolation, maximum iterations/resources, timeouts, concurrency, workspace lifetime, retries, loop detection, cancellation deadlines and mandatory stops. | APPROVED: bounded unattended engineering within an exact authorized revision and explicitly allowed tool classes, without repeated approval for ordinary in-scope iteration; mandatory stops at unauthorized consequential boundaries. Numerical envelope values remain WP6 implementation-preparation decisions. See approved dispositions below. | OPERATOR ARCHITECTURE DECISION — APPROVED 2026-09-25 |
| DEC-16 | How are intent, proposed/authorized work packages, revisions, amendments and cancellations unambiguously bound to actions and evidence? Prevents stale or spoofed authority. | Execution binds to exact authorized revision and current policy; changes require applicable approval; evidence preserves history. | Controlled versioned records with authenticated approval references; cryptographically bound authorization records. Both need cancellation propagation, revision conflict handling and independent verification; cryptographic binding adds key custody/recovery obligations. | APPROVED: distinguish intent, proposed revision, authorized revision, actions and evidence/disposition; bind actions/evidence to the exact revision using canonical identity suitable for cryptographic integrity/hash referencing. Amendment requires applicable authorization; cancellation/revocation invalidates pending authority and reconciles in-flight sensitive actions. Mechanism details remain later decisions. | OPERATOR ARCHITECTURE DECISION — APPROVED 2026-09-25 |

### Approved identity, authorization and revocation disposition — 2026-09-25

DEC-04 is an OPERATOR ARCHITECTURE DECISION — APPROVED 2026-09-25.

Sentinel shall distinguish human identities from workload/component identities
and shall preserve distinct principals for roles such as the operator, Forge
orchestration, Forge build/test workloads, AI/tool-broker activity, Courier,
Reaper, Scribe, Watchtower and Conduit as applicable to an admitted capability.

Authentication establishes identity only. It does not by itself establish
authorization.

Each receiving authority boundary shall independently determine whether the
authenticated principal may perform the exact requested action against the exact
resource/target under the applicable authorized work-package revision and policy.

Authorization shall be least-privilege and default-deny. Unspecified actions,
resources, targets and cross-component authority are denied.

Authorization shall support explicit expiry and revocation. A credential that
remains technically valid shall not override a current revocation, cancellation,
scope reduction or superseding work-package state.

No shared universal Sentinel administrative identity is approved.

This decision does not select SSH certificates, X.509, mTLS, OAuth/OIDC, SPIFFE,
hardware-backed identity, PAM implementation, account layout, issuer technology,
token format or other authentication mechanism. Those remain later bounded
implementation decisions.

### Approved credential and key custody disposition — 2026-09-25

DEC-05 is an OPERATOR ARCHITECTURE DECISION — APPROVED 2026-09-25.

Keys and credentials shall be scoped to component role, purpose and authorized
operation so compromise of one role does not automatically confer another
component's authority.

Forge engineering, build/test and AI/model workloads shall not possess Scribe
release/evidence-trust credentials merely because they create or analyze an
artifact.

Forge engineering, build/test and AI/model workloads shall not possess Conduit
deployment or privileged-management credentials merely because they may prepare
a bounded request.

Courier shall receive only the authority required for its controlled-transfer
role and shall not acquire Scribe release or Conduit deployment authority through
credential reuse.

Release/evidence-trust, privileged-management, deployment and other consequential
credentials shall remain outside ordinary build-worker and AI workload rights
unless a later explicit operator authorization creates a narrower exception.

Secrets and raw authentication material shall not be placed in Git, ordinary
build artifacts, model prompts, general logs or evidence payloads. Where evidence
must refer to sensitive authentication state, it shall use an approved safe
reference, identifier, digest or redacted representation appropriate to policy.

Credential issuance, storage, rotation, expiry, revocation, recovery and custody
shall be attributable to defined roles and auditable under the applicable
capability.

This decision does not select final key algorithms, certificate technology,
secret-store technology, HSM/TPM use, filesystem/keyring storage, issuer, rotation
intervals or recovery mechanism. Those remain later bounded implementation
decisions.

### Capability-scoped deferral disposition — DEC-06 through DEC-13 — 2026-09-25

DEC-06 through DEC-13 are explicitly deferred for the first bounded
Forge/Courier/Scribe capability where their unresolved mechanisms are not active
dependencies.

A deferral is not an architectural approval of an unknown value and does not
permit a missing choice to become an executable default.

If WP6 preparation discovers that the admitted capability depends on any deferred
decision, affected work shall stop at preparation and the applicable decision
shall be brought back for operator disposition before dependent execution.

The initial capability remains bounded to:

Forge prepares a revision-bound candidate/artifact/evidence package;
Courier independently verifies and controls transfer;
Scribe independently evaluates controlled release/evidence state;
attributable receipt/result information returns as evidence.

This capability does not imply Forge administrative access to Scribe, Forge or AI
release authority, Courier release authority, automatic deployment, Conduit
execution authority, general-purpose inbound access, general Internet egress,
Watchtower command authority, Cerberus administration or production readiness.

### Approved Conduit architectural disposition — 2026-09-25

DEC-01 approves the architectural relationship only. Forge may submit bounded
management/deployment requests to Conduit only when the exact operation is
permitted by the exact authorized work-package revision and applicable
operator/security policy. Conduit is the independent management/deployment
enforcement boundary; it must verify requests independently of Forge's assertion
of authority. Interaction grants Forge no general-purpose administration of targets.

Each request must bind requester/principal identity, exact authorized work-package
revision, authorization reference, exact target identity, exact requested operation,
required input/artifact identity, freshness/replay identity, applicable policy,
expected outcome/effect class and evidence/correlation identity.

Conduit shall reject unspecified/wildcard targets, out-of-revision operations,
stale/replayed authorization, mismatched target/artifact identity, missing required
authorization/evidence, unestablished authority and attempts to convert reachability
into administrative authority.

Forge may initiate the logical request. Network/session connection initiation,
transport protocol, API, port, certificate/key technology, credential mechanism,
target-side agent/daemon, push versus pull implementation and deployment technology
remain later implementation/interface decisions. None is selected or enabled here.

Conduit execution authority remains distinct from Scribe release/evidence authority,
Courier transfer authority, Forge build/development authority and AI/model reasoning.
Successful builds or transfers do not authorize execution. A Scribe release decision
does not automatically authorize deployment: separately applicable deployment
authorization/policy must explicitly permit the operation. Reachability grants nothing.
AI requests must pass Forge's existing work-package, policy and tool-broker controls;
model output grants no Conduit authority, even within an approved AI workflow.
Conduit must still independently validate the operation authorization.

Operation identity must detect replay, duplicates and uncertain prior outcomes.
An unknown sensitive outcome remains UNKNOWN. No automatic retry may repeat a
sensitive or privileged effect until prior outcome reconciliation under approved
policy. Forge and Conduit must preserve correlated evidence of the operation,
requester, authorized revision, target, authorization/policy decision, execution
disposition, validation/outcome and any unknown/partial/failure state.

Future acceptance of IF-03 must exercise each rejection case above, build/transfer/
release-only and AI-generated authority claims, duplicate requests and interrupted
sensitive outcomes. Verify denial before unauthorized effects, no sensitive retry
before reconciliation and correlated evidence on both sides. This specializes
FORGE-AUTH-002, FORGE-AUTH-003, FORGE-IF-001 through FORGE-IF-003,
FORGE-MON-001, FORGE-FAIL-002 and FORGE-AI-006; no runtime verification is claimed.

This decision does not enable Conduit, authorize host connectivity/deployment or a
protocol/port, create credentials/target agents, or begin WP6. DEC-04 and DEC-05
retain architectural approval; DEC-06 through DEC-13 retain their capability-scoped
deferral dispositions and create no executable defaults; DEC-02, DEC-03 and
DEC-14 through DEC-16 retain architectural approval. WP5 itself remains pending
review.

### Approved inbound architectural disposition — 2026-09-25

DEC-02 establishes DEFAULT-DENY inbound connectivity. Inbound network traffic,
listeners, management paths, callbacks, peer-initiated sessions and remotely
initiated operations acquire no authorization from reachability or technical
capability. Only an explicitly approved interface contract for a defined purpose
may admit an inbound interface; unspecified traffic and operations remain denied.

Each admitted contract must define exact purpose, permitted initiator/principal,
Forge receiver/service role, permitted logical request direction, authentication
and authorization requirements, allowed action/resource scope, data classification,
applicable work-package/policy binding, freshness/replay handling, rate/resource
limits, timeout/failure behavior, audit/evidence and revocation/disable behavior.

Reachability, address/hostname knowledge, an open/listening service, transport
connectivity, successful TLS/session establishment, source network/location,
component naming and prior successful communication do not establish authority.
The receiving Forge boundary must independently establish identity, authorization,
target/action scope and applicable policy before any security-sensitive effect.

Interface consequences:

- Cerberus administration may have a future approved inbound path only if DEC-11 and its interface contract authorize it. DEC-02 approves neither SSH nor direct/Conduit-mediated administration, ports, protocols, accounts, credentials or firewall rules.
- DEC-01's Forge-initiated logical request does not require Conduit-initiated inbound network connections. Any such path needs its own explicitly approved inbound contract.
- Watchtower observation/export creates no inbound command authority. Pull/query behavior requires explicit inbound approval and separation from general management.
- External provider approval under DEC-14 creates no inbound management interface. Callbacks, webhooks, provider-initiated sessions or equivalent behavior need explicit inbound-interface authorization.

Deny before consequential effect if the interface is not explicitly enabled;
caller identity is unestablished; authorization is absent, expired, revoked or
mismatched; target/action exceeds scope; required work-package/policy binding is
missing or stale; freshness/replay checks fail; required validation/audit capability
is unavailable; request state or prior sensitive outcome is unresolved; or an
observation/transfer interface is used as a management channel. Interface
availability cannot weaken these checks.

This decision chooses or authorizes no IP addressing, topology, firewall
implementation, listening port, SSH, TLS/mTLS, VPN, Conduit transport, API,
service/daemon implementation, certificate/key, user/service account,
authentication technology, network zone/VLAN or callback/webhook mechanism.
Those require later bounded decisions and applicable authorization. No host
connectivity, configuration or WP6 work is authorized by this record.

Future IF-03, IF-05, IF-06 and IF-09 acceptance (and any other admitted inbound
contract) must exercise every denial condition above and each listed false-authority
claim. Verify denial before effects, including revoked/disabled interfaces and
observation/transfer-to-management attempts; also demonstrate a request with an
explicit contract succeeds only within its independently validated scope. Review
each contract for every required field. This specializes FORGE-IF-001,
FORGE-IF-002, FORGE-IAM-001, FORGE-MON-001 and FORGE-FAIL-001; these are future
acceptance obligations, not deployed mitigations or verified host controls.

### Approved Courier architectural disposition — 2026-09-25

DEC-03 requires Forge artifact/evidence handoff through a controlled transfer
boundary. Courier is the independent controlled-transfer authority. Preparation
for Courier grants Forge no ambient write authority to Scribe, destination hosts
or downstream evidence/release stores. Creation, transfer authorization, transfer
execution, destination acceptance, release authority and deployment authority
remain separate. Build success does not authorize transfer; transfer success
establishes neither release nor deployment authorization.

Each proposed transfer package binds, as applicable: source principal/component,
exact authorized work-package revision, transfer authorization reference,
artifact/evidence identity and cryptographic digest or equivalent immutable identity,
artifact type, source workspace/build identity, destination identity, intended
purpose/disposition, policy/classification, expected transfer semantics and
correlation/operation identity. Unavailable provenance must not be fabricated.

Forge may prepare a package in a controlled staging boundary appropriate to its
authorized operation; staging itself grants no transfer authority. Staged content
must remain distinguishable from transferred/accepted content. Forge cannot mark
its own material successfully transferred or released. Unauthorized replacement
after authorization must be detectable; destination remains explicit, with wildcard
or unspecified destinations prohibited. Authority binds to the exact operation.
No staging implementation is selected.

Before transfer, Courier independently verifies requester/source identity,
authorization reference, exact authorized revision where applicable, object
identity/integrity, intended destination, transfer policy, classification and
data-handling constraints, freshness/replay state and required release/evidence
prerequisites where applicable. Missing required identity, integrity, authorization,
destination or policy causes rejection/fail-closed handling.

Courier produces an attributable transfer receipt or disposition binding, as
applicable: transfer/correlation identity, source, destination, artifact/evidence
digest, authorization reference, work-package revision, start/end timestamps or
equivalent ordered events, disposition, destination acknowledgement, validation
result, failure/partial/unknown state and retry/reconciliation state. Forge consumes
receipts as evidence only, never as Scribe release or deployment approval.

When delivery/acceptance cannot be proven, retain UNKNOWN or PARTIAL. Unresolved
sensitive transfers must not be blindly retried. Retry policy must address duplicate/
replay detection and destination-side reconciliation; every retry remains attributable
to the original or superseding authorized operation.

Scribe retains release/evidence authority. If transfer requires Scribe-controlled
release state, Courier verifies it under an independently valid reference rather
than a Forge assertion. Transport cannot create release authority. AI-generated
artifacts remain untrusted proposals until validated and authorized under the
applicable work package. Forge/AI preparation stays within scope; model output
cannot authorize transfer or bypass independent Courier policy/authorization checks.

Shared directory technology, removable media, filesystem layout, API/protocol,
socket direction, push/pull, encryption, certificate/key technology, queue/broker,
transfer daemon, Courier credentials, network path, destination service, retention
duration and receipt serialization remain later bounded implementation decisions.
None is selected or authorized by this record; no transfer mechanism or WP6 work
is authorized.

Future IF-02 acceptance must demonstrate independent authorization before transfer;
reject missing required fields/authority, wildcard/unspecified destinations,
identity/digest mismatch, replay and unauthorized staged replacement. Verify that
Forge cannot assert transfer/release success, Scribe prerequisites use independent
references, and receipts distinguish completion from PARTIAL/UNKNOWN without
conferring release/deployment rights. Interrupt transfer/acknowledgement, attempt
sensitive retry and reconcile at the destination; verify attributable retry history
and all applicable package/receipt fields. These specialize FORGE-AUTH-001 through
FORGE-AUTH-003, FORGE-IF-001 through FORGE-IF-004, FORGE-MON-001,
FORGE-FAIL-002 and FORGE-AI-001; no runtime verification is claimed.

### Approved AI architectural dispositions — 2026-09-25

The operator decision update supersedes the earlier pending recommendations for
DEC-14 through DEC-16 only. WP5 itself remains pending review.

**DEC-14:** Forge shall support hybrid local models and explicitly approved
external providers. Every provider/model must be allowlisted for defined workload
and data classifications; none is implicitly trusted. No automatic provider
substitution is permitted: outage, missing model or unavailable model/version
must not silently route work elsewhere. Record provider/model identity and version
when available; represent unavailable provenance as unknown and handle it under
approved admissibility policy. Secrets, authentication material, protected evidence,
release credentials and other policy-prohibited data cannot cross an external
boundary merely because a model requests context. External disclosure is bounded
by the authorized work package, provider policy and applicable classification and
data-handling rules. Vendor, API, model, protocol, credential mechanism and network
destination remain bounded WP6/later implementation decisions; none is selected.

**DEC-15:** Forge shall support bounded unattended engineering autonomy within an
exact authorized work-package revision. Only explicitly permitted tool classes
may be used. Ordinary in-scope actions need no repeated operator approval:

- Read authorized repository/workspace content and create/edit files in the authorized isolated workspace.
- Compile/build, run approved tests and static/security analysis, inspect generated artifacts and iterate after validation/test failures.
- Invoke explicitly approved providers and access explicitly approved network destinations.
- Recreate/discard isolated workspace state while preserving evidence and required recoverability.

Forge must stop before unauthorized consequential boundaries:

- Privilege escalation not already explicitly authorized; host mutation outside the execution boundary; secret access not explicitly authorized.
- Activation of changes to governing policy/approval/validation mechanisms; protected evidence or trust-anchor modification.
- New/unapproved network destinations; architecture/trust-boundary changes requiring operator approval; release or deployment; scope expansion.
- Retry of unresolved sensitive actions; unexplained identity/integrity/state; bypass or weakening of mandatory validation/security controls.

Resource limits, maximum iterations, concurrency, timeouts, workspace lifetime and
cancellation deadlines remain numerical WP6 implementation-preparation decisions.
This approval establishes bounded behavior, not numeric values or execution authority.

**DEC-16:** Forge shall distinguish operator mission/intent, proposed work-package
revision, authorized revision, individual actions and evidence/results/disposition.
Authorization applies to an exact versioned revision; actions and resulting evidence
must unambiguously bind to it. A broad mission does not authorize every useful
planner action. Additional scope/authority requires stopping affected work and a
new/amended proposal, with applicable operator authorization before exercising new
authority. Cancellation/revocation prevents affected pending work from being treated
as authorized and requires reconciliation of in-flight sensitive actions. Canonical
identity must be suitable for cryptographic integrity binding/hash referencing.
Signing mechanism, key custody implementation, record encoding, database technology
and transport remain later implementation decisions; none is chosen in WP5.

## Measurable operational requirements

Requirement definitions occur only in the tables below. References elsewhere do
not create new requirements. “Shall” specifies a future obligation. Requirements
remain part of the WP5 draft, incorporating the approved architectural dispositions
above; all are unverified in runtime. Draft tests cannot satisfy
runtime criteria. The future verifier is the role named in the approved WP6 plan,
with final acceptance reserved to the operator. Each test must record its input,
expected/actual result, context, collector, time/method and evidence reference.

### Purpose and authority

| ID | Proposed requirement | Acceptance evidence | Decisions |
| --- | --- | --- | --- |
| FORGE-AUTH-001 | Forge shall produce attributable candidates without granting release/evidence authority; only Scribe's approved decision path may confer controlled release status. | Demonstrate build success and transfer receipt cannot mark release approved; trace candidate to distinct Scribe decision. | DEC-12 |
| FORGE-AUTH-002 | Every sensitive action shall reference exact scope/resources, authorization, effects, verification, stop and recovery/rollback plan before execution. | For each allowed action, review complete authorization record; missing/expired/out-of-scope authorization produces denial before effects. | DEC-01, DEC-11, DEC-12 |
| FORGE-AUTH-003 | Courier and Conduit shall have distinct transfer and management contracts with no implicit cross-role authority. | A Courier principal/request attempting management is denied; Conduit reachability alone cannot accept/release an artifact. | DEC-01, DEC-03, DEC-04 |
| FORGE-AUTH-004 | Forge, Reaper, Scribe and Watchtower shall remain separate authority domains; communication, tool availability and AI output shall confer no cross-component authority. Courier transfer and Conduit enforcement shall neither create authorization nor confer creation, analysis, release or deployment rights. | Exercise cross-role requests: Forge grants Reaper scope, findings approve fixes, Courier marks release/deployment, Conduit creates authorization and AI claims component authority; deny each without independent applicable authorization. | DEC-01, DEC-03, DEC-04, DEC-12, DEC-13 |
| FORGE-AUTH-005 | Reaper shall execute only bounded authorized analysis through an approved interface, defensive by default. Offensive, exploitative, active-adversary, interception and other elevated testing shall require separate explicit operator authorization and applicable policy. Findings shall not independently authorize source/trust-anchor changes, security exceptions, release or deployment. | Verify approved defensive analysis stays within task/target; inject every elevated category without separate authorization and refuse execution. A valid finding alone cannot authorize a fix, exception or consequential operation. | DEC-04, DEC-13 |
| FORGE-AUTH-006 | Scribe alone shall determine Scribe-controlled release/evidence acceptance under applicable policy. Other components/models shall not declare that state; protected Scribe evidence/anchors shall remain outside Forge/AI workload modification rights unless separately explicitly authorized. Watchtower telemetry/query/alerts shall confer no command/deployment authority or independent authorization of host, Forge or Reaper work. | Build/test/scan/transfer/Conduit success cannot set Scribe release state; unauthorized workload writes to protected Scribe evidence/anchors fail. Watchtower alerts may produce notifications/proposals, but attempts to execute remediation or Forge/Reaper work without separate authorization fail. | DEC-04, DEC-05, DEC-07, DEC-12 |

### Interfaces and input integrity

| ID | Proposed requirement | Acceptance evidence | Decisions |
| --- | --- | --- | --- |
| FORGE-IF-001 | Each enabled IF-01 through IF-09 shall have an approved contract covering each permitted request/response direction and identifying initiator, receiver, schema, principal, allowed actions, classification, size/rate/concurrency bounds, timeout and ack semantics. | Every enabled direction maps to an approved contract and decision; unspecified direction/action and over-limit input are refused. | DEC-01, DEC-02, DEC-03, DEC-06, DEC-13, DEC-14, DEC-15, DEC-16 |
| FORGE-IF-002 | Each receiver shall validate origin, identity, integrity, target, version and approved freshness before using an object or effecting a request. | Inject wrong identity/target, tampering, substitution, stale revision and unsupported schema; each is refused before use with recorded reason. | DEC-04, DEC-08, DEC-13 |
| FORGE-IF-003 | Every operation shall carry an identity binding its authorization and input; replay/duplicate or uncertain prior outcomes shall be reconciled before repeating effects. | Replay and restart tests show no duplicate sensitive effect and explicit unresolved status when outcome cannot be established. | DEC-01, DEC-03, DEC-08, DEC-12 |
| FORGE-IF-004 | Incomplete transfers/jobs shall never become accepted outputs; completion requires bound object identity, completeness validation and attributable receipt/outcome. | Interrupt at transfer and completion boundaries; partial objects remain unusable, evidence persists and retry reconciles prior state. | DEC-03, DEC-09, DEC-13 |
| FORGE-IF-005 | Intake and analysis shall bind source revision, dependencies/toolchain, recipe, test policy and results to each candidate. | Reconstruct lineage for every sample; substituted result or missing mandatory Reaper result blocks acceptance; reproducibility expectation is specified per workload. | DEC-06, DEC-12, DEC-13 |
| FORGE-IF-006 | Every cross-component operation shall preserve caller/source identity, exact target component and operation, applicable work-package revision, authorization reference, artifact/evidence identity where applicable, policy/classification, correlation identity, outcome/disposition and applicable unknown/partial state. No wildcard component authority shall be inferred. | Review request/result traces across each enabled component boundary for all applicable fields; missing required authority/identity or wildcard target claims fail closed. Interrupt operations and verify UNKNOWN/PARTIAL survives handoff and cannot become success or approval. | DEC-01, DEC-02, DEC-03, DEC-04, DEC-07, DEC-16 |

### Identity and access

| ID | Proposed requirement | Acceptance evidence | Decisions |
| --- | --- | --- | --- |
| FORGE-IAM-001 | Human/workload identities shall have an approved principal/action/resource matrix; default unspecified access is denied at each receiver. | Exercise every allowed matrix entry and denied cross-role, wrong-resource, anonymous and revoked identity cases. | DEC-04, DEC-11 |
| FORGE-IAM-002 | Build/test code shall not possess management/release credentials or rights to alter protected evidence; role separation shall survive child processes and retries. | Adversarial workload attempts cross-boundary reads/writes/actions and fails without secret disclosure or protected-state change. | DEC-05, DEC-13 |
| FORGE-IAM-003 | Credential issuance, storage, rotation, expiry, revocation and recovery shall have named custodians and scoped audit; secrets shall be excluded from repo, events and artifacts. | Review custody map; exercise revoked/expired credentials and approved rotation/recovery; inspect sanitized outputs for leakage. | DEC-04, DEC-05, DEC-07 |

### Monitoring and evidence

| ID | Proposed requirement | Acceptance evidence | Decisions |
| --- | --- | --- | --- |
| FORGE-MON-001 | Each allow/deny, job transition, handoff, validation failure, privilege attempt and recovery action shall emit the architecture's minimum event fields with explicit unknowns and redaction. | Correlate each test operation and denial to complete events; confirm no secret payloads and provenance survives export. | DEC-07, DEC-08 |
| FORGE-MON-002 | Audit/export shall detect missing/duplicate events, delivery failure and storage exhaustion within approved deadlines; required evidence loss shall stop affected actions. | Disconnect sink, fill allocated buffer, drop/duplicate events; observe alert and stop within DEC-07 bounds, with no silent loss or overwrite. | DEC-07 |
| FORGE-MON-003 | Time health shall record uncertainty and ordering; time-dependent authorization/freshness shall fail closed outside approved bounds. | Inject clock jump, skew and unavailable source; observe flagged uncertainty and denied dependent action within approved detection bound. | DEC-08 |

### Failure and dependency behavior

| ID | Proposed requirement | Acceptance evidence | Decisions |
| --- | --- | --- | --- |
| FORGE-FAIL-001 | Each operation shall classify required dependencies and safe continuation conditions; unavailable required validation, identity or audit shall block affected effects without fallback authority. | Remove each required dependency; no acceptance/release bypass occurs; any continued local work meets explicitly approved offline conditions. | DEC-06, DEC-07, DEC-13 |
| FORGE-FAIL-002 | Interruptions or unexplained identity/integrity/state shall preserve existing evidence, mark outcome unknown/incomplete, stop affected work and require scoped recovery authorization. | Interrupt or mismatch each interface; records show stop, preserved prior state and no automatic repair, trust transition or uncertain privileged retry. | DEC-09, DEC-10, DEC-12 |

### Recovery and backup

| ID | Proposed requirement | Acceptance evidence | Decisions |
| --- | --- | --- | --- |
| FORGE-REC-001 | Every state class shall have an approved backup/rebuild/exclusion disposition, custodian, integrity/confidentiality controls, retention, recovery dependency and restore-test cadence. | Coverage review has no unclassified class; exercise missing, corrupt and unauthorized recovery inputs and refuse them; protected evidence changes remain separately gated. | DEC-05, DEC-09 |
| FORGE-REC-002 | Each accepted recoverable class shall meet operator-set RTO/RPO with explicit measurement start/end and uncertainty handling. | Isolated approved recovery exercise records elapsed recovery and recoverable-data gap against numeric targets; absent targets block acceptance. | DEC-08, DEC-10 |
| FORGE-REC-003 | Restore/rebuild shall verify identity, integrity, privileges, lineage and audit continuity, reconcile pending jobs, exclude revoked authority and require operator resumption approval. | Exercise interrupted restore and stale credentials; show safe halt/rollback preserving evidence and no automatic replay of management/deployment. | DEC-05, DEC-09, DEC-10, DEC-11 |

### Acceptance and invariants

| ID | Proposed requirement | Acceptance evidence | Decisions |
| --- | --- | --- | --- |
| FORGE-ACC-001 | Every admitted requirement/interface shall trace to approved decisions, a responsible verifier, test cases and required evidence before WP6 implementation preparation. | Operator reviews coverage matrix with no unresolved active dependencies or unowned tests. | DEC-01 through DEC-16 |
| FORGE-ACC-002 | Records shall distinguish all five state classes and all three execution contexts; no draft/test/commit shall assert host readiness or approval. | Review documentation and future test evidence; every host claim has host provenance and applied-state verification, or remains explicitly unknown. | None; enduring governance constraint |
| FORGE-ACC-003 | Future operational acceptance shall demonstrate all admitted requirements and invariants, including denial/failure/recovery cases, and require a separate operator readiness decision. | Reviewed requirement-by-requirement results and approved runbooks; any untested/failed criterion blocks acceptance of affected capability. | DEC-01 through DEC-16 |

### AI-assisted engineering and orchestration

These are future acceptance obligations, not claims of implemented AI security.
Ordinary edits, compiles, tests and repairs already inside an authorized package
may iterate without new human approval. Additional authority and consequential
boundaries remain subject to policy and operator approval.

| ID | Proposed requirement | Acceptance evidence | Decisions |
| --- | --- | --- | --- |
| FORGE-AI-001 | AI/model output shall be treated as untrusted proposed input and confer no authority by itself; its use requires independent validation under applicable policy and approval boundaries. | Inject model instructions claiming policy exemptions, validation success, release or deployment permission; all attempts fail to bypass the independent gates. | DEC-14, DEC-15, DEC-16 |
| FORGE-AI-002 | Every AI operation shall preserve attributable provenance binding applicable mission/work-package identity and revision, authorization reference, provider/model identity and available version, relevant prompt/instruction identity or safe cryptographic reference, source commit/workspace, inputs/dependencies, generated changes, requested/executed tool actions, validation results, evidence/artifacts, timestamps/context, operator decisions and final disposition. Unavailable fields shall be explicitly unknown; secrets/sensitive prompts shall use safe references or appropriately redacted evidence rather than compulsory raw retention. | Trace sample successful, denied, cancelled, retried and failed operations end-to-end; remove provider/version metadata and verify explicit unknowns plus approved admissibility handling; inspect outputs for secret/sensitive prompt leakage. | DEC-07, DEC-08, DEC-14, DEC-16 |
| FORGE-AI-003 | Agents shall not enlarge scope/permissions, grant privileges, alter governing approval policy, redefine trust boundaries or convert failed/unknown actions into authorized/successful actions. | Submit scope/role/policy mutations and forged success for unknown outcomes; deny effects, preserve original status and record the stop. | DEC-15, DEC-16 |
| FORGE-AI-004 | AI-generated code/configuration shall execute only within an approved isolated development boundary appropriate to the workload until separately authorized for later application. | Attempt execution outside the approved workspace and access to governing policy, credentials or protected evidence; deny before effects. Isolation technology remains unresolved. | DEC-05, DEC-13, DEC-15 |
| FORGE-AI-005 | Implementation/test/repair loops shall stay within the original authorized work package and approved resource envelope; stop for additional authority, new architecture/security decisions, expanded resources, prohibited tools/actions, unapproved escalation, unexplained identity/integrity/state, unresolved sensitive outcomes or required-control bypass/weakening. | Demonstrate multiple ordinary edits/tests/repairs without repeated approval, then inject each stop trigger and verify no dependent action occurs until appropriately resolved/authorized. | DEC-15, DEC-16 |
| FORGE-AI-006 | Tool access shall be explicitly allowlisted by role/work package and independently enforced by a policy tool broker or equivalent; tool availability/model requests confer no authorization. Checks shall cover arguments, targets, compound actions and subprocess effects. | Exercise allowed actions and denials for every tool class defined in the architecture, including mixed allowed/prohibited compound requests; no model or child process bypasses policy enforcement. | DEC-04, DEC-15, DEC-16 |
| FORGE-AI-007 | External providers shall form a separate trust boundary with approved workload/data, identity/version, privacy/retention, availability and supply-chain policy addressing injection, poisoning, unsafe code, hallucinated commands, disclosure, compromised suggested dependencies, identity ambiguity, version drift, tampering where applicable, tool misuse and unavailable provenance. Local models remain untrusted as well. | Execute each AI threat case below, simulate outage and missing provenance; deny disallowed disclosure/use, automatic provider substitution and unapproved provider/version change; record unknowns and block actions requiring unavailable information. | DEC-06, DEC-14, DEC-15 |
| FORGE-AI-008 | Models shall not independently approve their work, security exceptions, operator-gated architecture changes, release, deployment, trust-anchor changes or authority expansion. Successful tests shall not constitute approval. | Present model-generated approval and passing tests for each category; no approval state or consequential action occurs without independently verified applicable authority. | DEC-12, DEC-15, DEC-16 |
| FORGE-AI-009 | Instructions in source code, repositories, documentation, issue text, build artifacts, external content, model responses and retrieved context shall never acquire control-plane authority through model consumption. | Seed each content class with hostile instruction/approval claims; validate denial of policy changes, unauthorized tools and disclosure while preserving permitted task processing and attribution. | DEC-14, DEC-15, DEC-16 |
| FORGE-AI-010 | Iteration shall enforce approved cumulative iteration/resource bounds, timeouts, concurrency, workspace lifetime, retry/loop-detection and cancellation rules across workers/restarts; preserve evidence across retries/retirement and reconcile unknown sensitive outcomes before retry. | Exhaust each bound, repeat unsuccessful repairs and cancel queued/in-flight work; verify dispatch stops and in-flight actions safely stop/reconcile within approved deadlines, no counter reset on retry/restart, and retained evidence links every attempt. | DEC-07, DEC-09, DEC-15, DEC-16 |
| FORGE-AI-011 | Execution and resulting evidence shall unambiguously bind to the exact authorized work-package revision using canonical identity suitable for cryptographic integrity binding/hash referencing and current cancellation/revocation/approval state; scope amendments shall create a new/amended proposal with applicable approval. Generated changes shall not modify the authoritative policy/approval/validation mechanism governing the same work package. | Replay an old revision or spoof approval, cancel/amend during queued dispatch, and propose a policy/validator self-modification; reject stale/unauthorized effects and preserve proposals for separate review without activating them. | DEC-15, DEC-16 |

## Threat and failure coverage

This matrix applies to **every IF-01 through IF-09**, requests and responses,
including offline handoffs and time observations. WP6 must instantiate each row
per enabled interface. Any claimed non-applicability requires operator-reviewed
reasoning; it cannot be inferred from a transport choice. Test inputs remain
synthetic until host execution is separately approved.

| Concern | Measurable requirement references | Per-interface fault case and required result |
| --- | --- | --- |
| Unauthorized caller | FORGE-IAM-001, FORGE-AUTH-002 | Anonymous/wrong-role request refused before effects. |
| Replay | FORGE-IF-003, FORGE-MON-003 | Previously accepted request cannot repeat a sensitive effect. |
| Substitution/tampering | FORGE-IF-002, FORGE-IF-005 | Alter object/result or binding; reject before use. |
| Stale artifact/state | FORGE-IF-002, FORGE-REC-003 | Old revision, expired authority or stale recovery state rejected under approved policy. |
| Identity mismatch | FORGE-IAM-001, FORGE-IF-002 | Valid credential for wrong peer/target cannot cross boundary. |
| Partial transfer | FORGE-IF-004 | Truncated object or missing receipt remains incomplete. |
| Interrupted operation | FORGE-FAIL-002, FORGE-IF-003 | Stop at effect/ack boundaries; preserve and reconcile uncertain outcome. |
| Unavailable dependency | FORGE-FAIL-001 | Remove required service/input; affected action stops without bypass. |
| Duplicate operation | FORGE-IF-003 | Concurrent duplicate IDs cannot yield duplicate sensitive effects. |
| Evidence loss | FORGE-MON-001, FORGE-MON-002 | Remove/drop required event; detect gap and halt affected operation. |
| Monitoring failure | FORGE-MON-002 | Sink outage/full buffer produces alert and approved stop behavior. |
| Clock/time ambiguity | FORGE-MON-003 | Rollback/jump/uncertain time blocks dependent trust decisions. |
| Privilege-boundary violation | FORGE-IAM-002, FORGE-AUTH-003 | Payload/caller attempts management or evidence writes outside role; deny and audit. |

### AI orchestration threat cases

These cases apply to IF-09 and any other interface carrying AI-consumed content
or AI-directed actions. They are future tests, not currently verified mitigations.

| Concern | Measurable requirement references | Fault case and required result |
| --- | --- | --- |
| Prompt injection | FORGE-AI-009 | Hostile instructions in each enumerated content class cannot change authority or cause prohibited action. |
| Malicious model output | FORGE-AI-001, FORGE-AI-004 | Generated code attempts escape/protected-state mutation; deny outside isolation and withhold acceptance. |
| Hallucinated tool request | FORGE-AI-006 | Invented tool, argument or target has no allowlist authority; refuse and record. |
| Scope expansion | FORGE-AI-003, FORGE-AI-011 | Helpful extra task outside authorized revision stops at a new proposal without execution. |
| Approval spoofing | FORGE-AI-008, FORGE-AI-011 | Model/content claims operator approval or successful tests as approval; independently reject the claim. |
| Poisoned model context | FORGE-AI-002, FORGE-AI-009 | Retrieved context changes claimed scope/source provenance; retain original authority and reject unsupported bindings. |
| Sensitive provider disclosure | FORGE-AI-002, FORGE-AI-007 | Prompt/tool-result includes synthetic secret or disallowed data; block outbound disclosure and retain only approved redacted/reference evidence. |
| Model/provider substitution | FORGE-AI-007 | Wrong/ambiguous provider identity or tampered response cannot become accepted input under the approved contract. |
| Model version drift | FORGE-AI-007 | Unapproved version change or unavailable required version identifier blocks dependent use; no fabricated provenance. |
| Runaway/repeated repair loop | FORGE-AI-005, FORGE-AI-010 | Repeated failures, concurrent budget exhaustion or restart cannot bypass limits; stop with retained attempts. |
| Tool outside work-package authority | FORGE-AI-006 | Available tool requests network, secret, host, privilege, release or deployment access outside the package; deny before effects. |
| Governing policy self-modification | FORGE-AI-003, FORGE-AI-011 | Generated change edits its active policy/approval/validator; no activation within that work package; preserve proposal for separate review. |
| Provider failure or missing provenance | FORGE-AI-002, FORGE-AI-007 | Timeout/outage/missing metadata yields explicit failed/unknown state, no unauthorized fallback and no sensitive retry before reconciliation. |
| Cancellation or stale work-package revision | FORGE-AI-010, FORGE-AI-011 | Cancel/amend during concurrency; stale queued actions cannot dispatch, in-flight outcomes are reconciled within approved bounds. |
| Suggested compromised dependency | FORGE-AI-007, FORGE-IF-005 | Model suggests an unapproved/tampered dependency; intake refuses use despite plausible generated justification. |

## Acceptance criteria

Draft quality requires complete responsibility/interface coverage, no implicit
connectivity or authority, a decision register exposing every unknown, measurable
positive/negative test expectations, recovery and audit objectives explicitly
awaiting operator values, and dated K42 reconciliation preserving history. The AI
amendment additionally requires IF-09, FORGE-AI acceptance coverage, independent
policy/tool enforcement, explicit revision binding and meaningful autonomy inside
the approved envelope, consistent with the approved DEC-14 through DEC-16
dispositions and their explicitly deferred implementation choices.

Operational acceptance is a later phase governed by FORGE-ACC-003: required
functionality, isolation, custody, monitoring, dependency failures, denial cases,
backup/recovery and runbooks must be demonstrated in the appropriate authorized
context. Passing repository tests proves neither operational compliance nor readiness.

## Validation approach

In CODEX SANDBOX CONTEXT, inspect tracked diff and new-file contents, run
`git diff --check`, then `python3 -B -m unittest discover -s tests -p 'test_*.py' -v`.
Existing K42 tests use synthetic repository-local fixtures and mocked host paths;
do not execute the host preflight/writer CLI. New WP5 tests check document
structure, unique definitions, valid decision/requirement references, approved
and capability-scoped deferred architectural statuses and interface coverage,
including AI requirement/decision references.
Text presence establishes structural consistency only, not semantic security.
Manual review is required for security meaning,
provenance, no secret/database additions and no approval/deployment claims.

Side effects: edited documentation and test source; existing tests temporarily
create and remove synthetic `tests/.k42-test-*/` files, including fixture metadata.
`-B` suppresses bytecode; tests print to captured terminal output and create no
persistent validation log. Ordinary repository reads may update access metadata;
Git status may refresh index metadata. No host-discovery command or real AIDE
operation is part of validation. Record exact results in the operator handoff.

## Stop conditions

Stop affected work and report unexplained identity/integrity/state, conflicting
authority, sensitive content, a validation attempt reaching host paths, or need
for runtime/privileged/host action. Preserve evidence; do not repair or normalize.
Missing architecture decisions block their dependent implementation preparation,
not documentation of the unknown. Test failure blocks a successful validation
claim. Finish this draft and validation, then stop for operator review without
committing or entering WP6.

## WP5 exit criteria

The draft handoff requires all requested topics and traceability present, historical
claims reconciled with provenance, offline validation results disclosed, diff
reviewed, and no out-of-scope action. This is draft preparation only; WP5 remains
pending review. Formal WP5 exit requires the operator's architecture/security
review, preservation of approved DEC-01 through DEC-05 and DEC-14 through
DEC-16 dispositions, preservation of the explicit capability-scoped deferrals
for DEC-06 through DEC-13, agreed acceptance criteria and
explicit identification of the approved revision and any excluded capabilities.

## Requirements for entering WP6

1. Operator explicitly approves the architecture and requirements revision and
   records decisions with rationale, scope and approval reference.
2. Every capability admitted to WP6 has resolved architectural dependencies
   required for that capability. DEC-04 identity/authorization/revocation and
   DEC-05 credential/key-custody architecture are approved. DEC-06 through DEC-13
   are capability-scoped deferrals for the initial Forge/Courier/Scribe preparation
   only where their unresolved mechanisms are not active dependencies. If an
   admitted design depends on a deferred choice, preparation must identify and stop
   at that dependency until operator disposition. No interface, placeholder runtime
   behavior, executable default or implied trust may fill the unknown.
3. Active requirements have measurable bounds (including relevant retention,
   timeouts, capacity, time uncertainty and RTO/RPO), verifier ownership and
   positive/negative/failure test mapping. Numerical AI envelope values explicitly
   deferred by DEC-15 may be determined during separately authorized WP6 preparation
   under item 6 and must be approved before dependent execution. No invented
   targets fill unknowns.
4. Operator separately authorizes a bounded repository-only WP6 work package
   specifying allowed preparation artifacts and stop boundary. WP5 approval
   alone is not that authorization.
5. WP6 proposals must specify exact affected resources, expected effects,
   verification, stop conditions and rollback/recovery before any later host
   approval request. Host execution, deployment and AIDE trust transitions stay
   separately gated; K42 history must be preserved and never regenerated.
6. DEC-14, DEC-15 and DEC-16 are architecturally approved. Any separately authorized
   WP6 preparation must preserve hybrid provider allowlisting/data boundaries,
   bounded autonomy and exact-revision canonical identity binding. Its bounded
   scope must identify the deferred provider/implementation choices, numerical
   resource/iteration/concurrency/time/workspace/cancellation values and binding
   mechanism details to resolve before dependent execution. Those choices may be
   prepared in WP6; missing values cannot become executable defaults. This decision
   record does not authorize entering WP6 or implementing the engine.

No WP6 work begins as part of this handoff.
