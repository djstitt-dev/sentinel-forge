# WP6.2 Canonical Data Model Preparation

Status: **WP6.2 DRAFT — repository-only implementation preparation.**

WP6.2 is derived from and bound to the committed WP6.1 revision:

`1fff05aef06ef79c08a60031f93514a5c0a6b0ee`

WP6.1 in turn derives from the operator-approved WP5 architecture revision:

`0ce6457b31c7d798bf00626aeaeaeb963a103e52`

This work package does not authorize runtime implementation, host mutation,
network connectivity, transport selection, credential creation, privileged
execution, deployment, Conduit execution, AIDE operations, or operational
readiness claims.

## 1. Purpose

WP6.2 translates the approved WP6.1 Forge/Courier/Scribe logical contract into
a precise, technology-neutral canonical data model suitable for later derivation
of executable schemas and implementation code.

WP6.2 defines what the logical records mean and which relationships and
validation rules must be preserved.

WP6.2 does not select how those records are encoded, transported, stored,
signed, hashed, authenticated, persisted, or executed.

## 2. Authoritative sources

The canonical model shall remain consistent with:

- `docs/architecture/forge-operational-architecture.md`;
- `docs/plans/wp5-operational-requirements.md`;
- `docs/architecture/forge-courier-scribe-contract.md`;
- `docs/plans/wp6-forge-courier-scribe-preparation.md`;
- repository governance in `AGENTS.md`.

Where WP6.2 wording would change an approved authority boundary or contradict
WP5/WP6.1, WP6.2 stops rather than silently redefining the source architecture.

## 3. WP6.2 deliverables

The planned repository artifacts are:

- `docs/plans/wp6-canonical-data-model-preparation.md`;
- `docs/architecture/forge-courier-scribe-data-model.md`;
- `tests/test_wp62_data_model.py`.

No application source package, runtime configuration, network service,
credential material, deployment artifact, host-change script, or AIDE action is
authorized by these deliverables.

## 4. Logical objects in scope

WP6.2 shall model exactly these WP6.1 logical objects:

1. `WorkPackageRevision`
2. `ArtifactIdentity`
3. `AuthorizationReference`
4. `CorrelationIdentity`
5. `TransferRequest`
6. `TransferReceipt`
7. `ScribeDisposition`

WP6.2 may define subordinate logical value types only where they clarify fields
already required by WP5/WP6.1.

A subordinate type shall not introduce a new authority, runtime mechanism,
transport mechanism, credential technology, trusted-time guarantee, or
deployment capability.

## 5. Field requirement classes

Every modeled field shall be classified as one of:

### REQUIRED

The field must be present for every valid instance of that logical object.

Absence makes the object structurally invalid for dependent use.

### CONDITIONAL

The field is required when an explicitly stated condition applies.

The model shall state the condition. An implementation shall not silently omit
the field when the condition is true.

### OPTIONAL_OR_AVAILABLE

The field preserves information when available or applicable but is not required
for every structurally valid instance.

Optionality shall not permit fabrication of unavailable provenance or collapse
an unknown security-relevant state into success.

## 6. Unknown and unavailable information

WP6.2 shall distinguish:

- field absent because it is not applicable;
- field unavailable or unknown;
- field intentionally redacted or represented by a safe reference under policy;
- operation outcome `UNKNOWN`;
- transfer state `PARTIAL`;
- transfer/object state `INCOMPLETE`.

Unknown, unavailable, partial and incomplete information shall not be represented
as successful, accepted, complete or positively verified merely because a value
is absent.

WP6.2 shall not invent placeholder values that appear authoritative.

## 7. Object validity versus effect authorization

Structural validity of a logical object does not authorize an effect.

In particular:

- a valid `WorkPackageRevision` does not by itself authorize every operation;
- a valid `AuthorizationReference` does not replace receiver-side authorization
  evaluation;
- a valid `TransferRequest` does not authorize transfer;
- a valid `TransferReceipt` does not establish Scribe acceptance;
- a valid `ScribeDisposition` does not authorize deployment.

Each receiving authority remains responsible for independent validation required
by WP5 and WP6.1.

## 8. Cross-object binding rules

The model shall define consistency requirements for references shared across
objects, including where applicable:

- exact work-package identity and revision;
- authorization reference;
- source/requester identity;
- target component or destination;
- exact operation;
- artifact/evidence identity;
- policy/classification;
- correlation/operation identity;
- predecessor/retry relationship;
- outcome/disposition;
- completeness;
- available provenance.

Conflicting bindings shall fail validation rather than be automatically
normalized or rewritten.

Wildcard authority, unspecified consequential destinations and unspecified
consequential operations remain invalid.

## 9. Canonical identity boundary

WP6.2 shall identify the logical content that must participate in canonical
identity/integrity binding where required by WP5/WP6.1.

WP6.2 shall not select:

- a serialization format;
- canonical byte encoding;
- hash algorithm;
- signature algorithm;
- signing mechanism;
- certificate technology;
- key technology;
- key custody implementation.

A future work package may derive concrete canonical serialization and
cryptographic rules only after applicable decisions and authorization.

## 10. State vocabularies

The model shall preserve the WP6.1 transfer-related vocabulary:

- `PROPOSED`
- `REJECT`
- `INCOMPLETE`
- `PARTIAL`
- `UNKNOWN`
- `TRANSFERRED`

The model shall preserve the Scribe disposition vocabulary:

- `ACCEPT`
- `REJECT`
- `UNKNOWN`

`TRANSFERRED` shall not mean Scribe acceptance.

`ACCEPT` shall not mean deployment authorization.

No additional success or authority state may be introduced without reconciling
it against the approved architecture.

## 11. Replay, duplicate and retry representation

The model shall support representation of:

- independent operation identity;
- exact duplicate;
- detected replay;
- predecessor relationship;
- explicit retry;
- retry following known rejection;
- retry following incomplete or partial transfer;
- unresolved prior `UNKNOWN` outcome;
- reconciliation state.

A retry shall not erase or replace the identity or evidence of the prior
attempt.

A sensitive operation with unresolved prior outcome shall not be represented as
safe to repeat merely by assigning a new identifier.

## 12. Cancellation, revocation and amendment

The model shall preserve enough information to distinguish:

- active authorized revision;
- cancelled revision;
- revoked authority;
- superseded revision;
- amended/new revision;
- evidence historically attributable to an earlier revision.

Old evidence shall remain attributable to the revision under which it occurred.

Amendment shall not rewrite prior evidence as though it occurred under the new
revision.

## 13. DEC-08 boundary

WP6.2 may model attributable time information, uncertainty and explicit logical
ordering when such information is available.

WP6.2 shall not select or imply:

- trusted time source;
- clock synchronization mechanism;
- allowed skew;
- numeric freshness window;
- timestamp-based replay window;
- time-based authorization guarantee.

Timestamp presence alone shall not establish trusted freshness.

## 14. Secrets and sensitive values

The canonical model shall not require raw:

- passwords;
- private keys;
- bearer tokens;
- authentication secrets;
- release credentials;
- deployment credentials.

Where policy permits, logical records may contain safe identifiers, references,
digests or redacted representations.

Credential technology and custody remain separately gated.

## 15. Deferred decisions

DEC-06 through DEC-13 retain their WP5 capability-scoped deferrals.

WP6.2 shall not silently resolve those decisions.

In particular, WP6.2 shall not select:

- general network egress;
- Watchtower runtime integration;
- trusted-time mechanism or numeric freshness;
- production backup/retention/recovery;
- RTO/RPO;
- Cerberus administration;
- deployment/Conduit execution;
- workload isolation technology or general runtime resource limits.

If a required data-model decision depends on one of these unresolved choices,
the dependent portion stops and is returned to the operator.

## 16. Technology-neutral boundary

WP6.2 shall not select a concrete:

- JSON or JSON Schema representation;
- YAML representation;
- TOML representation;
- XML representation;
- Protocol Buffers representation;
- Avro representation;
- CBOR representation;
- MessagePack representation;
- REST API;
- gRPC API;
- database schema;
- filesystem storage format;
- transport protocol;
- listener, daemon, port or session direction.

Examples, if required for explanation, must be clearly non-normative and shall
not become implementation defaults.

## 17. Planned structural verification

Offline repository tests shall verify at minimum:

1. all seven logical objects are represented exactly once;
2. each field has an explicit requirement class;
3. required WP6.1 bindings remain represented;
4. transfer and Scribe state vocabularies remain exact;
5. transfer success cannot imply Scribe acceptance;
6. Scribe acceptance cannot imply deployment;
7. unknown/partial/incomplete semantics remain fail closed;
8. receiver-side independent validation remains required;
9. replay/duplicate/retry relationships preserve prior operation identity;
10. cancellation/revocation/amendment semantics preserve historical attribution;
11. DEC-06 through DEC-13 remain deferred;
12. no concrete serialization/schema/runtime stack is selected;
13. no cryptographic algorithm is selected;
14. no credential technology is selected;
15. no trusted-time or numeric freshness value is selected;
16. no deployment or Conduit authority is created;
17. passing document/model tests cannot be represented as operational
    acceptance.

The existing full offline regression suite shall remain green.

## 18. Stop conditions

WP6.2 preparation stops before the dependent portion if:

- the model requires resolution of DEC-06 through DEC-13;
- a concrete serialization/schema technology must be selected;
- a cryptographic algorithm or signing mechanism must be selected;
- credential technology or secrets must be created;
- trusted-time behavior or numeric freshness must be selected;
- runtime transport/network behavior must be selected;
- workload isolation/runtime resource bounds become necessary;
- deployment or Conduit execution becomes necessary;
- a host, privileged or AIDE action would be required;
- the model would change an approved WP5/WP6.1 authority boundary;
- repository identity, integrity or source provenance becomes unexplained.

The stop condition is fail closed. It is not permission to choose a convenient
default.

## 19. Verification and review boundary

WP6.2 changes remain repository-only.

Before any WP6.2 commit:

- exact changed files shall be reviewed;
- document/model structural tests shall pass;
- the full offline regression suite shall pass;
- `git diff --check` shall pass;
- deferred decisions shall remain visibly deferred;
- no runtime or operational-readiness claim shall be introduced.

A successful WP6.2 test or commit establishes repository preparation only.

It does not establish runtime correctness, runtime security, host readiness,
network readiness, credential readiness, Courier readiness, Scribe readiness,
release approval, deployment approval or production readiness.

## 20. Exit condition

WP6.2 is complete only when:

1. the canonical logical data model is reviewed against WP5 and WP6.1;
2. every modeled field has explicit requirement semantics;
3. cross-object binding and failure rules are explicit;
4. deferred dependencies remain explicit and fail closed;
5. offline structural and regression tests pass;
6. the operator explicitly approves the WP6.2 candidate.

Completion of WP6.2 does not authorize a concrete schema implementation or
runtime implementation.

Any subsequent work package requires separate authorization.
