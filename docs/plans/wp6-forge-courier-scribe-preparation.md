# WP6.1 Forge/Courier/Scribe implementation preparation

Status: WP6.1 DRAFT — repository-only implementation preparation.

Prepared after operator architecture/security approval of WP5 and separate
operator authorization to enter bounded repository-only WP6 preparation.
The approved WP5 repository revision is:

`0ce6457b31c7d798bf00626aeaeaeb963a103e52`

This work package does not authorize runtime implementation, host mutation,
network connectivity, credential creation, deployment, privileged execution,
AIDE operations, or operational-readiness claims.

## Purpose

Prepare an implementation-ready logical contract for the first bounded
Forge/Courier/Scribe capability without selecting or enabling runtime mechanisms
whose architectural dependencies remain deferred.

The admitted logical flow is:

1. Forge prepares a revision-bound candidate/artifact/evidence package.
2. Forge proposes a bounded transfer request.
3. Courier independently verifies transfer authority, package identity,
   destination and applicable policy before controlling transfer.
4. Courier returns an attributable transfer disposition/receipt.
5. Scribe independently evaluates controlled release/evidence state.
6. An attributable Scribe disposition/result returns as evidence.

Creation, transfer authorization, transfer execution, destination acceptance,
release/evidence acceptance and deployment remain distinct authority events.

## Scope

WP6.1 may prepare repository documentation and offline structural validation for:

- logical object and contract definitions;
- canonical identity and revision-binding requirements;
- immutable artifact/evidence identity requirements;
- authorization-reference binding;
- component responsibility and authority boundaries;
- transfer request and receipt semantics;
- Scribe disposition semantics;
- ACCEPT, REJECT, UNKNOWN and applicable incomplete/partial states;
- duplicate, replay and unresolved-prior-outcome behavior;
- dependency/admission mapping against WP5 requirements and decisions;
- implementation change plans, verification plans, stop conditions and rollback;
- sanitized offline structural tests for the preparation documents.

WP6.1 may identify candidate implementation technologies or alternatives only as
non-executable proposals where useful. It shall not select a deferred mechanism
as an executable default.

## Explicit exclusions

WP6.1 does not authorize or select:

- host or privileged changes;
- deployment or Conduit execution;
- direct Forge administration of Scribe;
- general-purpose inbound connectivity;
- general Internet or provider egress;
- transport protocol, port, listener, daemon or session-initiation direction;
- production credential, certificate, key or secret creation/storage;
- final authentication technology;
- final key algorithm or credential technology;
- Watchtower runtime integration;
- Cerberus administration;
- Reaper execution;
- production backup/recovery implementation;
- AIDE discovery, checking, baseline, promotion, closure or trust transition;
- operational or production readiness.

## Governing decisions

WP6.1 preserves the approved WP5 architecture:

- DEC-01 through DEC-05 and DEC-14 through DEC-16 are architecturally approved.
- DEC-06 through DEC-13 retain their capability-scoped deferrals.
- A deferral is not approval of an unknown value.
- A deferred value shall not become an executable placeholder or default.
- If the admitted design depends on a deferred choice, dependent preparation
  stops at that boundary and returns the decision to the operator.

## Required logical objects

WP6.1 shall prepare reviewable definitions for at least:

- `WorkPackageRevision`
- `ArtifactIdentity`
- `AuthorizationReference`
- `TransferRequest`
- `TransferReceipt`
- `ScribeDisposition`
- `CorrelationIdentity`

Names are logical vocabulary for preparation and do not select a programming
language, serialization format, API, transport or storage technology.

Each applicable cross-component object shall preserve or bind:

- source/caller principal or component identity;
- exact target component and permitted operation;
- exact authorized work-package revision;
- authorization reference;
- artifact/evidence identity and immutable digest/reference where applicable;
- policy/classification;
- correlation/operation identity;
- disposition/outcome;
- explicit UNKNOWN/PARTIAL/INCOMPLETE state where applicable;
- available provenance without fabricating unavailable fields.

## Authority invariants

The prepared contract shall preserve all of the following:

1. Forge creates candidates but cannot declare Scribe-controlled release state.
2. Courier controls transfer but cannot create release or deployment authority.
3. Scribe independently determines Scribe-controlled release/evidence acceptance.
4. Transfer success is not release approval.
5. Release/evidence acceptance is not deployment authorization.
6. AI/model output cannot authorize transfer, release, deployment or authority
   expansion.
7. Communication, reachability, equal hashes and tool availability do not transfer
   authority.
8. Missing, expired, revoked, mismatched or unestablished authority fails closed.
9. Unknown sensitive outcomes remain UNKNOWN until reconciled.
10. A sensitive operation with unresolved prior outcome is not blindly retried.

## Requirement admission and deferred-dependency rule

WP6.1 shall build a traceability/admission matrix for requirements relevant to
the first Forge/Courier/Scribe capability.

Each requirement shall be classified as one of:

- `ADMITTED_FOR_PREPARATION`: logical preparation can proceed using approved
  architecture without inventing a deferred mechanism.
- `PARTIAL_PREPARATION_ONLY`: invariant/schema/test planning may proceed, but a
  deferred dependency prevents executable implementation preparation.
- `BLOCKED_PENDING_OPERATOR_DECISION`: the requirement depends directly on a
  deferred architectural or numeric choice and dependent preparation stops.

The matrix shall identify:

- requirement ID;
- applicable decision IDs;
- responsible component/verifier;
- preparation classification;
- required positive/negative/failure tests;
- evidence expected from later verification;
- unresolved dependency, if any;
- exact stop condition.

No numeric timeout, freshness, retention, capacity, concurrency, iteration,
workspace-lifetime, RTO, RPO or similar value shall be invented merely to make a
requirement appear implementable.

## Initial requirement focus

The first contract preparation shall trace at least:

- FORGE-AUTH-001 through FORGE-AUTH-004;
- FORGE-AUTH-006;
- FORGE-IF-001 through FORGE-IF-004;
- FORGE-IF-006;
- FORGE-IAM-001 through FORGE-IAM-003 as applicable;
- FORGE-FAIL-001 and FORGE-FAIL-002;
- FORGE-ACC-001 through FORGE-ACC-003;
- FORGE-AI-001 through FORGE-AI-011 where AI provenance, authority, revision
  binding, tool access or deferred resource bounds affect the contract.

Requirements outside this focus remain governed by WP5 and are not implicitly
waived or satisfied.

## Planned WP6.1 repository artifacts

Subject to review during this work package, the intended preparation artifacts are:

- `docs/plans/wp6-forge-courier-scribe-preparation.md`
- `docs/architecture/forge-courier-scribe-contract.md`
- `tests/test_wp6_documents.py`

Existing status/index documentation may receive narrowly scoped reconciliation
updates so it accurately distinguishes historical WP5 state from the current
approved WP6.1 preparation state. Such updates shall not rewrite historical
evidence or claim runtime application.

No application source package, runtime configuration, network service, credential
material or host-change script is authorized by this work package.

## Verification

WP6.1 offline validation shall verify at minimum:

- required logical objects are defined exactly once;
- admitted objects contain required identity/authority/outcome bindings;
- decision and requirement references resolve to WP5;
- authority invariants remain explicit;
- DEC-06 through DEC-13 remain deferred rather than silently resolved;
- deferred numeric/mechanism values do not appear as executable defaults;
- no deployment authority is introduced;
- no runtime transport, credential or host mechanism is accidentally selected;
- UNKNOWN/PARTIAL/INCOMPLETE states cannot become ACCEPT through omission;
- replay/duplicate/uncertain-outcome cases retain fail-closed semantics;
- local documentation links resolve;
- repository whitespace checks pass;
- the complete existing offline regression suite remains green.

Passing structural tests demonstrates document consistency only. It does not prove
runtime security, host state, deployment readiness or operational acceptance.

## Stop conditions

Stop affected WP6.1 work and return to the operator if:

- a required design choice depends on DEC-06 through DEC-13;
- a numeric bound is required before dependent preparation can be meaningful;
- a proposed contract changes an approved WP5 trust or authority boundary;
- implementation would require host, network, credential, deployment, privileged
  or AIDE action;
- unexplained repository identity, integrity or state is encountered;
- the approved WP5 revision cannot be preserved;
- tests reveal a conflict with the approved architecture.

## Rollback

Until committed, WP6.1 consists only of repository working-tree changes and may
be rolled back by removing/reverting only the explicitly reviewed WP6.1 changes.
Existing historical evidence and prior commits shall not be rewritten.

A future WP6.1 commit, if separately reviewed and approved, records preparation
state only. A commit does not authorize runtime implementation or application.

## Exit gate

WP6.1 exits only after:

1. the operator reviews the logical contract and admission/dependency matrix;
2. all active references trace to the approved WP5 architecture;
3. offline structural and regression validation passes;
4. deferred dependencies remain explicit and fail closed;
5. exact implementation-preparation boundaries and remaining decisions are
   identified;
6. the operator explicitly approves the WP6.1 preparation revision and any
   separately proposed next work package.

No later implementation phase is authorized by WP6.1 completion alone.
