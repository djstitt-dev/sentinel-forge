# Forge/Courier/Scribe logical contract

Status: WP6.1 DRAFT — repository-only implementation preparation.

This document prepares the logical contract for the first bounded
Forge/Courier/Scribe capability. It is derived from the operator-approved WP5
architecture at repository revision:

`0ce6457b31c7d798bf00626aeaeaeb963a103e52`

It does not authorize runtime implementation, network connectivity, transport,
credentials, host mutation, privileged execution, deployment, Conduit execution,
AIDE action or operational-readiness claims.

## 1. Purpose

Define implementation-ready logical objects, authority boundaries, state
semantics and receiver-validation obligations for the first bounded flow:

Forge prepares candidate
→ Forge proposes transfer
→ Courier independently validates and controls transfer
→ Courier returns attributable receipt/disposition
→ Scribe independently evaluates controlled release/evidence state
→ attributable Scribe disposition returns as evidence.

This contract describes logical meaning only.

It does not select:

- programming language;
- serialization format;
- schema technology;
- transport protocol;
- port;
- listener;
- daemon;
- push versus pull;
- session-initiation direction;
- credential technology;
- certificate technology;
- key algorithm;
- storage engine;
- database;
- queue;
- filesystem handoff mechanism;
- trusted time source;
- production retry interval;
- timeout;
- concurrency;
- capacity;
- retention;
- RTO;
- RPO.

Any such selection remains separately gated where applicable.

## 2. Governing authority model

The following authority domains remain distinct:

| Domain | Authority |
| --- | --- |
| Forge | Candidate creation, engineering, build, planning and bounded request preparation within exact authorized scope |
| Courier | Independent controlled-transfer authorization, verification and transfer disposition |
| Scribe | Independent controlled release/evidence acceptance |
| Operator | Sole authority for architecture/security approval and separately gated consequential actions |
| Conduit | Separate management/deployment enforcement boundary; outside this contract |
| Reaper | Separate bounded security-analysis execution authority; outside this contract |
| Watchtower | Separate observation/monitoring/alerting authority; outside this contract |

Communication does not transfer authority.

A caller's authenticated identity does not itself establish authorization.

A successful Forge build does not authorize transfer.

A successful Courier transfer does not establish Scribe acceptance.

A Scribe ACCEPT disposition does not authorize deployment.

Model or AI output does not establish any of these authorities.

## 3. Contract-wide invariants

Every implementation derived from this contract shall preserve these invariants.

### FCS-INV-001 — exact work-package binding

Every consequential logical object shall bind to the exact authorized
`WorkPackageRevision` applicable to the operation.

A broad mission, earlier revision, repository branch name, successful test,
model statement or prior approval shall not substitute for the exact authorized
revision.

### FCS-INV-002 — independent receiver validation

Each receiving authority boundary independently validates the caller/source,
authorization reference, target, operation, work-package revision, object
identity, integrity and applicable policy before using the object or performing
an effect.

Sender assertion alone is insufficient.

### FCS-INV-003 — immutable candidate identity

Artifact/evidence identity shall be bound to immutable content identity suitable
for integrity comparison.

A name, path, filename, staging location or mutable reference alone shall not
establish artifact identity.

The exact digest algorithm and representation remain implementation decisions.

### FCS-INV-004 — authority separation

Forge cannot mark Scribe-controlled release/evidence state.

Courier cannot mark Scribe-controlled release/evidence state.

Courier cannot create deployment authority.

Scribe controlled release/evidence acceptance cannot create deployment authority.

### FCS-INV-005 — no wildcard authority

Targets, operations, resources and authority scopes shall be explicit.

Wildcard component authority, unspecified destinations and implicit cross-role
authority are invalid.

### FCS-INV-006 — unknown remains unknown

An unresolved sensitive outcome remains `UNKNOWN`.

Missing acknowledgement, missing receiver disposition, interrupted processing,
ambiguous completion or unresolved prior effect shall not be normalized into
success.

### FCS-INV-007 — incomplete is not accepted

`PARTIAL` and `INCOMPLETE` objects or operations cannot become accepted merely
because some constituent step succeeded.

Completeness must be independently established by the responsible receiver.

### FCS-INV-008 — replay and duplicate reconciliation

An operation identity shall permit detection and reconciliation of duplicate,
replayed or uncertain prior operations.

A sensitive operation with unresolved prior outcome shall not be blindly
repeated.

Numeric freshness windows and trusted-time guarantees remain deferred under
DEC-08.

### FCS-INV-009 — provenance is not fabricated

Unavailable provenance shall remain explicitly unknown.

The contract may preserve safe references, digests or redacted identifiers where
raw sensitive data is prohibited.

### FCS-INV-010 — secrets remain outside ordinary payloads

Secrets, private keys, raw credentials and authentication artifacts shall not be
embedded in ordinary candidate packages, model prompts, repository content,
general logs or transfer evidence.

Credential technology and custody implementation remain separately gated.

## 4. Logical state vocabulary

This contract distinguishes logical outcomes from authority decisions.

### 4.1 Transfer-related disposition vocabulary

Courier-facing transfer state may include:

- `PROPOSED`
- `REJECT`
- `INCOMPLETE`
- `PARTIAL`
- `UNKNOWN`
- `TRANSFERRED`

`TRANSFERRED` means only that Courier has independently determined that the
authorized controlled-transfer operation completed according to the applicable
transfer contract.

`TRANSFERRED` is not Scribe acceptance and is not deployment authorization.

### 4.2 Scribe disposition vocabulary

Scribe-controlled release/evidence evaluation shall produce one of:

- `ACCEPT`
- `REJECT`
- `UNKNOWN`

`ACCEPT` means only that Scribe's independently approved controlled
release/evidence decision path accepted the submitted package under applicable
policy.

`REJECT` means Scribe independently determined that acceptance requirements were
not satisfied.

`UNKNOWN` means Scribe's controlled disposition cannot currently be established.

No other component may manufacture or reinterpret these states.

### 4.3 State preservation rule

`UNKNOWN`, `PARTIAL` and `INCOMPLETE` shall survive cross-component handoff until
the authority responsible for reconciliation establishes a different state under
approved policy.

Omission of a field or missing result shall not collapse such a state into
success.

## 5. Logical object: WorkPackageRevision

### 5.1 Purpose

`WorkPackageRevision` identifies the exact authorized work-package revision to
which proposed actions and resulting evidence are bound.

### 5.2 Required logical fields

The logical object shall preserve:

- work-package identity;
- exact revision identity;
- authorization state;
- authorization reference;
- applicable scope;
- applicable resources/targets;
- allowed action classes;
- applicable policy reference;
- cancellation/revocation state;
- supersession/amendment relationship where applicable;
- canonical integrity-binding identity or reference.

### 5.3 Validation requirements

A receiver shall reject dependent effects when:

- the revision is not exact;
- the revision is unapproved;
- the revision is cancelled or revoked;
- the action is outside its scope;
- the target/resource is outside its scope;
- the authorization reference does not bind to it;
- integrity or canonical identity cannot be established where required.

### 5.4 Deferred implementation details

This definition does not select:

- record encoding;
- signing mechanism;
- hash algorithm;
- approval-record storage;
- key custody;
- transport;
- database representation.

## 6. Logical object: ArtifactIdentity

### 6.1 Purpose

`ArtifactIdentity` identifies candidate artifact/evidence bytes or an immutable
artifact set without relying on mutable names or locations.

### 6.2 Required logical fields

The logical object shall preserve:

- artifact identifier;
- artifact type/class;
- immutable content digest or immutable integrity reference;
- digest/reference provenance;
- source work-package revision;
- source candidate/build/workspace identity where applicable;
- source component;
- classification/data-handling designation;
- completeness state;
- lineage/provenance references where available.

### 6.3 Validation requirements

The receiver shall refuse dependent use when:

- artifact identity is missing;
- content integrity does not match the bound identity;
- the artifact is substituted;
- the artifact belongs to a different work-package revision;
- classification or handling requirements are unsupported;
- completeness cannot be established;
- required provenance is missing and applicable policy requires it.

Unknown provenance shall be represented as unknown rather than invented.

## 7. Logical object: AuthorizationReference

### 7.1 Purpose

`AuthorizationReference` binds an operation to applicable authorization without
embedding raw credentials or secret material.

### 7.2 Required logical fields

The logical object shall preserve:

- authorization identifier/reference;
- authorizing authority identity;
- authorized principal or principal class;
- exact authorized work-package revision;
- permitted action;
- permitted target/resource;
- applicable policy reference;
- authorization state;
- revocation/cancellation state;
- expiry or other validity information when such information exists and is
  supported by approved mechanisms.

### 7.3 Validation requirements

A receiver independently determines whether the authorization permits the exact
requested operation against the exact requested target.

Authentication alone does not satisfy this check.

### 7.4 DEC-08 limitation

No trusted-time-based validity, expiry or freshness behavior may be assumed until
the applicable DEC-08 dependency is resolved.

Where time-dependent validation is required but approved time guarantees are not
available, dependent execution remains blocked rather than silently accepted.

## 8. Logical object: CorrelationIdentity

### 8.1 Purpose

`CorrelationIdentity` binds related requests, receipts, dispositions and evidence
into one attributable operation history and supports duplicate/replay/unknown
reconciliation.

### 8.2 Required logical fields

The logical object shall preserve:

- operation/correlation identifier;
- originating component/principal;
- exact work-package revision;
- target component;
- requested operation;
- artifact/evidence identity where applicable;
- predecessor/retry relationship where applicable;
- known ordering relationship where available.

### 8.3 Required semantics

A correlation identity shall:

- distinguish independent operations;
- permit duplicate detection;
- permit replay detection under approved policy;
- link retries to the prior attempt;
- preserve prior `UNKNOWN`, `PARTIAL` or `INCOMPLETE` outcomes;
- prevent retry from appearing to be an unrelated clean operation.

### 8.4 DEC-08 limitation

Correlation identity may establish operation relationship and explicit logical
ordering where available.

It does not by itself establish trusted chronological freshness.

Trusted time source, skew tolerance, numeric freshness and timestamp-based replay
windows remain unresolved under DEC-08.

## 9. Logical object: TransferRequest

### 9.1 Creator

Forge may prepare a `TransferRequest` only within an exact authorized
work-package revision.

Preparing a request does not authorize transfer.

### 9.2 Receiver

Courier is the independent receiving transfer authority.

### 9.3 Required logical fields

`TransferRequest` shall bind:

- requesting/source principal or component;
- exact target component/destination;
- exact requested transfer operation;
- exact `WorkPackageRevision`;
- `AuthorizationReference`;
- `ArtifactIdentity`;
- applicable policy;
- classification/data-handling designation;
- `CorrelationIdentity`;
- intended purpose/disposition;
- expected transfer effect class;
- available provenance;
- known prior-attempt/reconciliation state.

### 9.4 Courier validation

Before performing a transfer effect, Courier independently validates:

- requester/source identity;
- transfer authorization;
- exact work-package revision;
- target/destination;
- permitted transfer operation;
- artifact identity and integrity;
- policy;
- classification/data handling;
- completeness;
- duplicate/replay/prior-outcome state;
- any required release/evidence prerequisites applicable to transfer.

If a required check cannot be established, Courier fails closed for the affected
transfer.

### 9.5 Explicit invalid cases

Courier shall reject or stop a request involving:

- anonymous or wrong-role caller;
- wildcard/unspecified destination;
- wildcard/unspecified operation;
- mismatched work-package revision;
- revoked/cancelled authority;
- missing authorization reference;
- artifact substitution;
- integrity mismatch;
- incomplete artifact presented as complete;
- unsupported classification/handling;
- unresolved sensitive prior outcome where repeat effects could occur;
- an attempt to use Courier as management, release or deployment authority.

## 10. Logical object: TransferReceipt

### 10.1 Creator

Courier creates the authoritative transfer receipt/disposition for Courier's
controlled-transfer operation.

Forge cannot self-issue a Courier receipt.

### 10.2 Required logical fields

`TransferReceipt` shall bind:

- Courier identity;
- source/requester identity;
- exact destination;
- exact transfer operation;
- exact `WorkPackageRevision`;
- `AuthorizationReference`;
- `ArtifactIdentity`;
- `CorrelationIdentity`;
- applicable policy/classification;
- transfer disposition;
- validation outcome;
- destination acknowledgement state where applicable;
- completeness state;
- failure information where applicable;
- explicit `INCOMPLETE`/`PARTIAL`/`UNKNOWN` state where applicable;
- available start/end time information with uncertainty and/or explicit ordered-event
  references, without implying trusted chronological freshness;
- retry/reconciliation state;
- available provenance.

### 10.3 Meaning

Receipt time or event-order information is attributable evidence only. It shall
not establish trusted chronological freshness unless the applicable DEC-08
requirements have been separately resolved and approved.

Forge consumes `TransferReceipt` as evidence only.

A receipt shall not:

- declare Scribe `ACCEPT`;
- create release authority;
- create deployment authority;
- create management authority;
- grant Forge ambient downstream write rights.

### 10.4 Interrupted transfer rule

If transfer completion cannot be established:

- the receipt/outcome shall remain `UNKNOWN`, `PARTIAL` or `INCOMPLETE` as
  appropriate;
- prior evidence shall be preserved;
- the artifact shall not be represented as accepted output;
- retry shall reconcile the prior operation identity before another sensitive
  effect is attempted.

## 11. Logical object: ScribeDisposition

### 11.1 Creator

Only Scribe's approved controlled release/evidence decision path may create the
authoritative `ScribeDisposition`.

Forge, Courier, Reaper, Watchtower, Conduit and models cannot create or override
this authority state.

### 11.2 Required logical fields

`ScribeDisposition` shall bind:

- Scribe authority identity;
- source/requester context where applicable;
- exact `WorkPackageRevision`;
- `ArtifactIdentity`;
- applicable transfer/correlation identity;
- applicable authorization/policy reference;
- release/evidence policy identity;
- controlled disposition: `ACCEPT`, `REJECT` or `UNKNOWN`;
- validation/evaluation references;
- reason/reference appropriate to policy;
- available provenance;
- explicit unknown fields where required information is unavailable.

### 11.3 Meaning

`ACCEPT` establishes only Scribe-controlled release/evidence acceptance.

It does not authorize:

- deployment;
- Conduit execution;
- direct Forge administration;
- host mutation;
- privileged execution;
- AIDE trust transition;
- any authority outside Scribe's approved release/evidence boundary.

### 11.4 Failure semantics

If Scribe cannot establish identity, integrity, applicable policy, exact revision
binding or another required prerequisite, it shall not return `ACCEPT`.

The result remains `REJECT` or `UNKNOWN` according to the approved policy and
whether the outcome is known.

## 12. Logical processing sequence

The intended logical sequence is:

1. An exact authorized `WorkPackageRevision` exists.
2. Forge produces an attributable candidate with `ArtifactIdentity`.
3. Forge prepares a `TransferRequest` bound to:
   - the exact work-package revision;
   - artifact identity;
   - transfer authorization;
   - explicit Courier/destination target;
   - operation/correlation identity.
4. Courier independently validates the request.
5. Courier either:
   - rejects without authorized transfer effect;
   - stops with `UNKNOWN`/`INCOMPLETE`;
   - performs the controlled transfer and records its disposition.
6. Courier creates `TransferReceipt`.
7. Receipt evidence may accompany or reference the candidate presented to Scribe.
8. Scribe independently validates its own required inputs and policy.
9. Scribe creates `ScribeDisposition`.
10. Forge may retain the resulting disposition as attributable evidence.
11. No deployment action follows from this contract.

## 13. Replay, duplicate and retry semantics

A repeated operation with the same or related correlation identity shall not
automatically repeat a sensitive effect.

Implementations shall be able to distinguish:

- exact duplicate;
- detected replay;
- explicit authorized retry;
- retry following known rejection;
- retry following known incomplete/partial transfer;
- retry following unresolved unknown outcome.

A retry following `UNKNOWN` shall first reconcile the prior operation sufficiently
to determine whether repeating the effect is safe under approved policy.

Where such reconciliation depends on a deferred mechanism, dependent execution
remains blocked.

## 14. Cancellation, revocation and amendment

A cancelled or revoked work-package revision shall not authorize new dependent
effects.

Queued or pending work bound to stale authority shall not be dispatched as if
still authorized.

In-flight sensitive work whose outcome becomes uncertain during cancellation or
revocation shall preserve its actual/unknown disposition and enter reconciliation.

An amendment creates a new/amended work-package revision requiring applicable
authorization.

Old evidence remains historically attributable to the revision under which it
occurred and shall not be rewritten as though it occurred under the amended
revision.

## 15. Requirement admission matrix

The following classifications apply only to WP6.1 logical preparation.

| Requirement | Classification | WP6.1 treatment / stop boundary |
| --- | --- | --- |
| FORGE-AUTH-001 | ADMITTED_FOR_PREPARATION | Candidate/Scribe authority separation can be fully defined logically. |
| FORGE-AUTH-002 | PARTIAL_PREPARATION_ONLY | Authorization structure and stop semantics can be prepared; execution/recovery mechanisms remain separately gated. |
| FORGE-AUTH-003 | ADMITTED_FOR_PREPARATION | Courier/Conduit authority separation is architecturally approved; Conduit execution remains excluded. |
| FORGE-AUTH-004 | ADMITTED_FOR_PREPARATION | Cross-component authority separation is fully expressible as invariant. |
| FORGE-AUTH-006 | ADMITTED_FOR_PREPARATION | Scribe-only controlled release/evidence authority is fully expressible. |
| FORGE-IF-001 | PARTIAL_PREPARATION_ONLY | Logical schema/principal/action/classification semantics may be prepared; numeric size/rate/concurrency/timeout values and transport remain unresolved. |
| FORGE-IF-002 | PARTIAL_PREPARATION_ONLY | Identity/integrity/target/version checks can be prepared; trusted freshness behavior depends on DEC-08. |
| FORGE-IF-003 | PARTIAL_PREPARATION_ONLY | Operation identity/reconciliation semantics can be prepared; numeric/time-based freshness remains deferred. |
| FORGE-IF-004 | PARTIAL_PREPARATION_ONLY | Incomplete/receipt semantics can be prepared; production recovery/storage assumptions remain unresolved under DEC-09/13. |
| FORGE-IF-006 | ADMITTED_FOR_PREPARATION | Required cross-component identity/authority/outcome bindings are fully expressible logically. |
| FORGE-IAM-001 | PARTIAL_PREPARATION_ONLY | Principal/action/resource semantics may be prepared; credential/authentication technology remains unresolved. |
| FORGE-IAM-002 | PARTIAL_PREPARATION_ONLY | Separation requirement may be prepared; workload-isolation implementation depends on DEC-13. |
| FORGE-IAM-003 | PARTIAL_PREPARATION_ONLY | Custody/audit obligations may be prepared; issuance/storage/rotation technology and some audit dependencies remain unresolved. |
| FORGE-FAIL-001 | PARTIAL_PREPARATION_ONLY | Fail-closed dependency semantics may be prepared; specific runtime dependencies are not yet selected. |
| FORGE-FAIL-002 | PARTIAL_PREPARATION_ONLY | Unknown/incomplete stop semantics may be prepared; recovery objectives/mechanisms remain deferred. |
| FORGE-ACC-001 | ADMITTED_FOR_PREPARATION | WP6.1 traceability/admission review directly supports this requirement. |
| FORGE-ACC-002 | ADMITTED_FOR_PREPARATION | Preparation artifacts can maintain state/context distinctions without host-readiness claims. |
| FORGE-ACC-003 | PARTIAL_PREPARATION_ONLY | Future acceptance cases may be planned, but operational acceptance is outside WP6.1. |
| FORGE-AI-001 | ADMITTED_FOR_PREPARATION | Model output is untrusted input and carries no authority. |
| FORGE-AI-002 | PARTIAL_PREPARATION_ONLY | Provenance fields can be prepared; time/provider/export mechanisms include deferred dependencies. |
| FORGE-AI-003 | ADMITTED_FOR_PREPARATION | No authority/scope expansion is a logical invariant. |
| FORGE-AI-004 | BLOCKED_PENDING_OPERATOR_DECISION | Executable isolation depends on unresolved DEC-13. Documentation of the boundary may continue; implementation may not. |
| FORGE-AI-005 | PARTIAL_PREPARATION_ONLY | Mandatory stop categories can be prepared; numeric resource envelope is unresolved. |
| FORGE-AI-006 | PARTIAL_PREPARATION_ONLY | Policy-broker semantics can be prepared; executable tool classes/bounds belong to later bounded design. |
| FORGE-AI-007 | BLOCKED_PENDING_OPERATOR_DECISION | External provider execution depends on DEC-06 and provider-specific implementation choices. |
| FORGE-AI-008 | ADMITTED_FOR_PREPARATION | AI cannot approve consequential work. |
| FORGE-AI-009 | ADMITTED_FOR_PREPARATION | Untrusted content cannot become control-plane authority. |
| FORGE-AI-010 | BLOCKED_PENDING_OPERATOR_DECISION | Numeric iteration/resource/timeout/concurrency/workspace/cancellation values are unresolved. |
| FORGE-AI-011 | PARTIAL_PREPARATION_ONLY | Exact revision binding and cancellation semantics can be prepared; cryptographic/signing mechanism remains later. |

`BLOCKED_PENDING_OPERATOR_DECISION` blocks dependent executable preparation.
It does not prevent documentation of the unresolved requirement or stop boundary.

## 16. Deferred-dependency register

### DEC-06 — egress/external providers

No general Internet, registry, DNS, mirror or external-provider destination is
authorized by this contract.

The logical Forge/Courier/Scribe contract must remain useful without assuming
such egress.

### DEC-07 — Watchtower export/retention

Watchtower integration is outside the first capability.

Local attributable evidence obligations remain, but export/retention technology
is not selected here.

### DEC-08 — time/freshness

No trusted time source, skew bound or numeric freshness interval is selected.

Therefore:

- timestamps alone shall not establish authorization or freshness;
- logical correlation and ordering may still be preserved;
- time-dependent validation remains blocked where required;
- no implementation may invent a freshness window.

### DEC-09 — backup/recovery

No production backup boundary, retention interval or restore cadence is selected.

This contract shall not assume recovery from unavailable state.

### DEC-10 — RTO/RPO/outage

No RTO, RPO or maximum-outage value is selected.

No availability or recovery-readiness claim follows from this contract.

### DEC-11 — Cerberus administration

No direct or emergency administrative path is authorized.

### DEC-12 — deployment

Deployment authority is unavailable.

The first capability stops at Scribe controlled release/evidence disposition.

### DEC-13 — workload/isolation/capacity

General workload classes, isolation technology, capacity, quotas, concurrency,
timeouts and Reaper-gate policy remain unresolved.

No executable worker/isolation architecture is selected by this contract.

## 17. Required offline test cases for WP6.1

The future WP6.1 document tests shall verify at least:

1. Every required logical object is present exactly once.
2. Forge cannot declare Scribe `ACCEPT`.
3. Courier cannot declare Scribe `ACCEPT`.
4. Courier transfer cannot create deployment authority.
5. Scribe `ACCEPT` cannot create deployment authority.
6. Transfer requests require explicit source, target, operation, work-package,
   authorization, artifact and correlation bindings.
7. Transfer receipts preserve `UNKNOWN`, `PARTIAL` and `INCOMPLETE`.
8. Scribe dispositions are limited to `ACCEPT`, `REJECT` and `UNKNOWN`.
9. Missing authority fails closed.
10. Wildcard targets/operations are invalid.
11. Artifact substitution/integrity mismatch is rejected.
12. Stale/cancelled/revoked work-package authority cannot authorize new effects.
13. Duplicate/replay/unknown-prior operations require reconciliation.
14. DEC-06 through DEC-13 remain explicitly deferred.
15. No runtime transport/protocol/port/listener is selected.
16. No credential/certificate/key technology is selected.
17. No trusted-time source or freshness interval is invented.
18. No timeout, concurrency, capacity, retention, RTO or RPO value is invented.
19. No host, privileged, AIDE or deployment action is authorized.
20. Passing document tests cannot be represented as operational acceptance.

## 18. Evidence expectations for later implementation

Future implementation verification, if separately authorized, shall produce
evidence sufficient to attribute:

- exact work-package revision;
- exact caller/source principal;
- exact target;
- exact operation;
- authorization reference;
- artifact identity;
- correlation/operation identity;
- receiver validation disposition;
- actual transfer disposition;
- Scribe disposition where applicable;
- explicit failure/partial/unknown state;
- retry/reconciliation relationship;
- execution context;
- collector/method;
- available time information with uncertainty;
- available provenance;
- operator decisions where applicable.

This section defines evidence expectations only. It does not authorize creation
of production evidence stores or runtime audit pipelines.

## 19. WP6.1 stop boundary

Preparation stops and returns to the operator before dependent work if:

- runtime transport must be selected;
- credential technology or secrets must be created;
- trusted-time behavior is required;
- numeric resource or retry bounds become required for executable behavior;
- workload isolation must be selected;
- network egress or inbound connectivity becomes required;
- deployment or Conduit execution becomes required;
- Cerberus administration becomes required;
- backup/recovery/RTO/RPO becomes an active acceptance dependency;
- a proposed design changes an approved WP5 authority boundary;
- host, privileged or AIDE action would be required;
- repository identity/integrity becomes unexplained.

## 20. Readiness statement

This document is an implementation-preparation artifact only.

It does not establish:

- runtime correctness;
- runtime security;
- host state;
- network readiness;
- credential readiness;
- Courier operational readiness;
- Scribe operational readiness;
- release approval;
- deployment approval;
- production readiness.

A future implementation, verification and operational acceptance path remains
separately gated.
