# Forge/Courier/Scribe Canonical Logical Data Model

Status: **WP6.2 DRAFT — repository-only implementation preparation.**

This model is derived from and bound to committed WP6.1 revision:

`1fff05aef06ef79c08a60031f93514a5c0a6b0ee`

WP6.1 derives from the operator-approved WP5 architecture revision:

`0ce6457b31c7d798bf00626aeaeaeb963a103e52`

This document defines logical data semantics only.

It does not select or authorize serialization, canonical byte encoding,
cryptographic algorithms, signatures, credentials, storage, database
representation, transport, network connectivity, runtime implementation,
deployment, Conduit execution, host mutation, privileged execution, AIDE
operations, or operational readiness.

## 1. Model rules

### 1.1 Field requirement classes

Every normative field defined by this model has one requirement class:

- `REQUIRED`: present for every structurally valid instance.
- `CONDITIONAL`: present when the stated condition applies.
- `OPTIONAL_OR_AVAILABLE`: preserved when applicable or available but not
  required for every structurally valid instance.

Field optionality does not authorize fabrication, silent substitution, or
normalization of an unknown security-relevant value into success.

### 1.2 Logical field types

The model uses technology-neutral logical types:

- `Identifier`: opaque identity within its defined namespace.
- `Reference`: opaque reference to another logical record or controlled object.
- `Text`: bounded textual value whose concrete bounds remain later decisions.
- `Enum`: value selected from the explicitly defined logical vocabulary.
- `BooleanState`: logical true/false state when the fact is established.
- `IdentityReference`: reference to a specific principal, component or authority
  identity.
- `PrincipalReference`: reference to a specific principal or an explicitly
  bounded principal class.
- `TargetReference`: reference to an exact component, destination, resource or
  explicitly bounded approved target set.
- `PolicyReference`: reference to applicable policy.
- `IntegrityReference`: immutable content/integrity identity with provenance.
- `ObjectReference`: identity/reference to another logical object defined by
  this model. It does not imply recursive embedding of the referenced object's
  complete canonical representation.
- `RelationshipReference`: reference establishing predecessor, retry,
  supersession or amendment relationship.
- `OrderedEventReference`: attributable logical event-order reference that does
  not imply trusted chronological freshness.
- `TimeEvidence`: attributable time information with known uncertainty where
  available; it does not itself establish trusted freshness.
- `ProvenanceValue`: available provenance, a safe provenance reference, or an
  explicit unknown/unavailable provenance state when required by the object
  semantics.
- `UnknownCapableValue`: a logical value whose unavailability can be explicitly
  represented without fabricating a value.

These are semantic types, not programming-language, schema-language or storage
types.

### 1.3 Unknown, absent and redacted values

The model distinguishes:

- not applicable;
- applicable and known;
- applicable but unknown/unavailable;
- intentionally redacted or represented by an approved safe reference;
- `UNKNOWN` operation/disposition state;
- `PARTIAL` transfer state;
- `INCOMPLETE` object/transfer state.

A required security-relevant value that cannot be established does not become a
positive value merely because it is absent.

Where policy permits a safe reference or redacted representation instead of raw
sensitive content, the representation shall preserve that fact rather than
pretend the raw value was present.

### 1.4 Structural validity and authority

Structural validity is not authorization.

A structurally valid object may still be refused by the responsible receiver
because authorization, identity, integrity, policy, scope, target, operation,
classification, completeness, replay state or another required prerequisite
cannot be independently established.

### 1.5 Reference consistency

When two logical objects bind the same work-package revision, authorization,
artifact, operation, target, policy/classification or correlation identity, the
bindings shall agree.

Conflicting consequential bindings fail validation.

They shall not be silently rewritten, merged or normalized.

## 2. Shared state vocabularies

### 2.1 TransferDisposition

Exact logical vocabulary:

- `PROPOSED`
- `REJECT`
- `INCOMPLETE`
- `PARTIAL`
- `UNKNOWN`
- `TRANSFERRED`

`TRANSFERRED` establishes only Courier-controlled transfer completion under the
applicable transfer contract.

It does not establish Scribe acceptance or deployment authorization.

### 2.2 ScribeDispositionState

Exact logical vocabulary:

- `ACCEPT`
- `REJECT`
- `UNKNOWN`

`ACCEPT` establishes only Scribe-controlled release/evidence acceptance under
applicable policy.

It does not authorize deployment or Conduit execution.

### 2.3 CompletenessState

The model shall preserve whether required object or operation completeness is:

- established complete;
- established incomplete;
- unknown.

A concrete encoded vocabulary for this state is deferred.

No completeness state may be inferred solely from omission of a field.

### 2.4 ReconciliationState

The model shall be capable of distinguishing at least:

- no known predecessor requiring reconciliation;
- exact duplicate detected;
- replay detected;
- explicit retry of identified predecessor;
- predecessor ended in known rejection;
- predecessor ended incomplete or partial;
- predecessor outcome unresolved/unknown;
- reconciliation completed sufficiently for the applicable approved policy;
- reconciliation unresolved.

The concrete encoded vocabulary remains deferred.

## 3. Canonical identity participation

Where WP5/WP6.1 requires canonical integrity identity, the logical identity shall
cover the security-relevant normative content necessary to distinguish the exact
record and its authority-relevant bindings.

The model does not select canonical bytes, field ordering, serialization, hash
algorithm, signing algorithm or signing mechanism.

Mutable display names, paths, filenames, branch names and staging locations
shall not substitute for immutable content/integrity identity.

Unknown or unavailable fields shall not be silently omitted from canonical
meaning where their known/unknown status is security relevant.

## 4. Logical object: WorkPackageRevision

### 4.1 Purpose

`WorkPackageRevision` identifies the exact authorized work-package revision to
which proposed actions and resulting evidence are bound.

### 4.2 Fields

| Field | Requirement | Logical type | Meaning / validation |
| --- | --- | --- | --- |
| `work_package_id` | REQUIRED | Identifier | Identifies the work package independently of revision. |
| `revision_id` | REQUIRED | Identifier | Identifies the exact revision. Broad mission identity, branch name or earlier revision is insufficient. |
| `authorization_state` | REQUIRED | UnknownCapableValue | Preserves whether applicable authorization state is established, denied/revoked/cancelled, or cannot be established. It shall not default to authorized. |
| `authorization_reference` | REQUIRED | ObjectReference | Binds the revision to the applicable `AuthorizationReference`. |
| `scope_reference` | REQUIRED | Reference | Identifies the authorized scope definition without expanding it. |
| `resource_target_scope` | REQUIRED | Reference | Identifies applicable authorized resources/targets. Wildcard component authority is invalid. |
| `allowed_action_classes` | REQUIRED | Reference | Identifies the action classes permitted by the revision. Presence does not authorize an action outside exact receiver-side evaluation. |
| `policy_reference` | REQUIRED | PolicyReference | Identifies applicable governing policy. |
| `cancellation_revocation_state` | REQUIRED | UnknownCapableValue | Preserves current known cancellation/revocation state without assuming validity from silence. |
| `supersession_amendment_relationship` | CONDITIONAL | RelationshipReference | Required when this revision supersedes, amends or is superseded/amended by another known revision. |
| `canonical_integrity_reference` | REQUIRED | IntegrityReference | Immutable canonical identity/reference required for exact revision binding. Algorithm and encoding remain deferred. |

### 4.3 Cross-field rules

- `work_package_id` plus `revision_id` shall identify the exact revision.
- `authorization_reference` shall bind the same exact revision.
- cancellation or revocation shall prevent the revision from authorizing new
  dependent effects.
- an amended revision is a distinct revision and shall not rewrite evidence
  attributable to its predecessor.
- failure to establish canonical integrity where required makes dependent use
  invalid.

## 5. Logical object: ArtifactIdentity

### 5.1 Purpose

`ArtifactIdentity` identifies candidate artifact/evidence bytes or an immutable
artifact set without relying on mutable names or locations.

### 5.2 Fields

| Field | Requirement | Logical type | Meaning / validation |
| --- | --- | --- | --- |
| `artifact_id` | REQUIRED | Identifier | Stable logical identifier for the artifact identity record. |
| `artifact_type_class` | REQUIRED | Identifier | Identifies artifact/evidence type or class under applicable policy. |
| `integrity_reference` | REQUIRED | IntegrityReference | Immutable content digest or equivalent immutable integrity reference. Concrete algorithm is deferred. |
| `integrity_provenance` | REQUIRED | ProvenanceValue | States provenance of the integrity reference. Unavailable provenance remains explicitly unknown. |
| `source_work_package_revision` | REQUIRED | ObjectReference | Binds artifact to exact `WorkPackageRevision`. |
| `source_candidate_build_workspace` | CONDITIONAL | Reference | Required when a candidate, build or workspace identity exists and is applicable to artifact lineage. |
| `source_component` | REQUIRED | IdentityReference | Identifies the component responsible for the artifact source context. |
| `classification_handling` | REQUIRED | Reference | Identifies applicable classification/data-handling designation. |
| `completeness_state` | REQUIRED | CompletenessState | Preserves complete, incomplete or unknown completeness. Absence cannot imply complete. |
| `lineage_provenance` | OPTIONAL_OR_AVAILABLE | ProvenanceValue | Preserves additional lineage/provenance where available. Missing provenance shall not be fabricated. |

### 5.3 Cross-field rules

- mutable path/name/location alone shall not establish artifact identity.
- integrity mismatch or substitution invalidates dependent use.
- artifact revision binding shall agree with referencing request, receipt and
  disposition objects.
- an artifact known incomplete cannot be represented as complete.
- where required provenance is unavailable under applicable policy, dependent
  use fails rather than inventing provenance.

## 6. Logical object: AuthorizationReference

### 6.1 Purpose

`AuthorizationReference` represents applicable operation authority without
embedding raw credentials or secret material.

### 6.2 Fields

| Field | Requirement | Logical type | Meaning / validation |
| --- | --- | --- | --- |
| `authorization_id` | REQUIRED | Identifier | Identifies the authorization record/reference. |
| `authorizing_authority` | REQUIRED | IdentityReference | Identifies the authority responsible for the authorization. |
| `authorized_principal` | REQUIRED | PrincipalReference | Identifies the authorized principal or explicitly bounded principal class. |
| `authorized_work_package_revision` | REQUIRED | ObjectReference | Binds authority to exact `WorkPackageRevision`. |
| `permitted_action` | REQUIRED | Identifier | Identifies exact permitted action/action class as applicable. Wildcard consequential authority is invalid. |
| `permitted_target_resource` | REQUIRED | Reference | Identifies exact permitted target/resource or bounded approved resource set. |
| `policy_reference` | REQUIRED | PolicyReference | Identifies applicable authorization policy. |
| `authorization_state` | REQUIRED | UnknownCapableValue | Preserves known authorization state. It shall not default to valid/authorized. |
| `revocation_cancellation_state` | REQUIRED | UnknownCapableValue | Preserves known revocation/cancellation state. |
| `validity_information` | CONDITIONAL | UnknownCapableValue | Required when approved mechanisms provide applicable expiry/validity information. Presence shall not imply trusted time. |

### 6.3 Cross-field rules

- authentication alone does not satisfy authorization.
- the receiver independently evaluates the exact principal, action, target,
  revision and policy.
- authorization for one role/component shall not be interpreted as another
  role's authority.
- raw credentials, private keys, bearer secrets or authentication artifacts are
  not fields of this object.
- time-dependent validity remains unusable where its required DEC-08 guarantees
  have not been approved.

## 7. Logical object: CorrelationIdentity

### 7.1 Purpose

`CorrelationIdentity` binds requests, receipts, dispositions and evidence into
an attributable operation history and supports duplicate, replay and unknown
outcome reconciliation.

### 7.2 Fields

| Field | Requirement | Logical type | Meaning / validation |
| --- | --- | --- | --- |
| `operation_correlation_id` | REQUIRED | Identifier | Identifies the operation history. A new value shall not erase relationship to a prior sensitive attempt. |
| `originating_identity` | REQUIRED | IdentityReference | Identifies originating component/principal. |
| `work_package_revision` | REQUIRED | ObjectReference | Binds operation history to exact `WorkPackageRevision`. |
| `target_component` | REQUIRED | IdentityReference | Identifies exact target component. |
| `requested_operation` | REQUIRED | Identifier | Identifies exact requested operation. |
| `artifact_identity` | CONDITIONAL | ObjectReference | Required when the operation acts on or concerns an artifact/evidence object. |
| `predecessor_retry_relationship` | CONDITIONAL | RelationshipReference | Required for a retry, duplicate/replay relationship, or other known predecessor relationship. |
| `known_ordering_relationship` | OPTIONAL_OR_AVAILABLE | OrderedEventReference | Preserves attributable logical ordering when available without asserting trusted chronological freshness. |
| `reconciliation_state` | CONDITIONAL | ReconciliationState | Required when a predecessor, retry, duplicate, replay or prior uncertain outcome exists; preserves whether reconciliation is resolved or unresolved under applicable policy. |

### 7.3 Cross-field rules

- independent operations shall be distinguishable.
- retries shall remain linked to prior attempts.
- a new correlation identifier shall not cleanse an unresolved prior
  `UNKNOWN`.
- logical ordering does not establish trusted time.
- unresolved sensitive prior outcome blocks blind repetition of the effect.

## 8. Logical object: TransferRequest

### 8.1 Purpose and authority

Forge may prepare a `TransferRequest` only within an exact authorized
work-package revision.

Structural validity of the request does not authorize transfer.

Courier independently decides whether the requested transfer effect is
authorized and admissible.

### 8.2 Fields

| Field | Requirement | Logical type | Meaning / validation |
| --- | --- | --- | --- |
| `source_identity` | REQUIRED | IdentityReference | Requesting/source principal or component. Anonymous or wrong-role source is invalid. |
| `destination` | REQUIRED | TargetReference | Exact target component/destination. Wildcard or unspecified destination is invalid. |
| `transfer_operation` | REQUIRED | Identifier | Exact requested transfer operation. Wildcard or unspecified operation is invalid. |
| `work_package_revision` | REQUIRED | ObjectReference | Exact `WorkPackageRevision`. |
| `authorization_reference` | REQUIRED | ObjectReference | Exact applicable `AuthorizationReference`. |
| `artifact_identity` | REQUIRED | ObjectReference | Exact `ArtifactIdentity` proposed for transfer. |
| `policy_reference` | REQUIRED | PolicyReference | Applicable transfer policy. |
| `classification_handling` | REQUIRED | Reference | Applicable classification/data-handling designation. |
| `correlation_identity` | REQUIRED | ObjectReference | Exact `CorrelationIdentity`. |
| `intended_purpose_disposition` | REQUIRED | Reference | Bounded intended transfer purpose/disposition. It shall not create release/deployment authority. |
| `expected_transfer_effect_class` | REQUIRED | Reference | Identifies expected class of Courier transfer effect without expanding authority. |
| `provenance` | OPTIONAL_OR_AVAILABLE | ProvenanceValue | Available request/package provenance. Unavailable provenance is not fabricated. |
| `prior_attempt_reconciliation_state` | REQUIRED | ReconciliationState | Preserves known prior-attempt and reconciliation status, including the absence of a known predecessor requiring reconciliation. Unresolved sensitive prior outcome blocks blind repeat. |

### 8.3 Cross-object rules

The request's:

- revision shall agree with artifact, authorization and correlation bindings;
- source shall be consistent with applicable authorization;
- destination and operation shall be permitted by applicable authorization and
  policy;
- classification/handling shall be consistent with artifact and destination
  handling requirements;
- prior-attempt state shall agree with correlation history.

Courier shall independently validate these relationships before any transfer
effect.

## 9. Logical object: TransferReceipt

### 9.1 Purpose and authority

Courier creates the authoritative `TransferReceipt` for Courier's controlled
transfer operation.

Forge cannot self-issue an authoritative Courier receipt.

### 9.2 Fields

| Field | Requirement | Logical type | Meaning / validation |
| --- | --- | --- | --- |
| `courier_identity` | REQUIRED | IdentityReference | Identifies Courier authority producing the receipt. |
| `source_identity` | REQUIRED | IdentityReference | Identifies source/requester associated with the transfer. |
| `destination` | REQUIRED | TargetReference | Exact transfer destination. |
| `transfer_operation` | REQUIRED | Identifier | Exact controlled transfer operation. |
| `work_package_revision` | REQUIRED | ObjectReference | Exact `WorkPackageRevision`. |
| `authorization_reference` | REQUIRED | ObjectReference | Applicable transfer `AuthorizationReference`. |
| `artifact_identity` | REQUIRED | ObjectReference | Exact transferred/proposed `ArtifactIdentity`. |
| `correlation_identity` | REQUIRED | ObjectReference | Exact `CorrelationIdentity`. |
| `policy_classification` | REQUIRED | Reference | Applicable policy/classification binding. |
| `transfer_disposition` | REQUIRED | Enum | One value from `TransferDisposition`. |
| `validation_outcome` | REQUIRED | UnknownCapableValue | Preserves Courier validation result without converting unavailable validation into success. |
| `destination_acknowledgement_state` | CONDITIONAL | UnknownCapableValue | Required when destination acknowledgement is applicable to the approved transfer contract. Missing acknowledgement shall not imply success. |
| `completeness_state` | REQUIRED | CompletenessState | Preserves established complete/incomplete/unknown state. |
| `failure_information` | CONDITIONAL | UnknownCapableValue | Required when failure, rejection, incomplete, partial or unknown outcome information exists or is required by policy. |
| `start_end_time_evidence` | OPTIONAL_OR_AVAILABLE | TimeEvidence | Available attributable start/end time information with uncertainty. It does not establish trusted freshness. |
| `ordered_event_references` | OPTIONAL_OR_AVAILABLE | OrderedEventReference | Available explicit event-order evidence without implying trusted chronology. |
| `retry_reconciliation_state` | REQUIRED | ReconciliationState | Preserves retry/prior-operation reconciliation state, including when no predecessor requires reconciliation. |
| `provenance` | OPTIONAL_OR_AVAILABLE | ProvenanceValue | Available receipt provenance. Unknown provenance remains unknown. |

### 9.3 Disposition rules

- `TRANSFERRED` means Courier determined the controlled transfer completed under
  the applicable transfer contract.
- `TRANSFERRED` does not mean Scribe `ACCEPT`.
- `TRANSFERRED` does not authorize deployment.
- if completion cannot be established, the receipt shall preserve `UNKNOWN`,
  `PARTIAL` or `INCOMPLETE` as appropriate.
- missing acknowledgement shall not be normalized into successful completion.
- failure evidence shall be preserved where available/applicable.
- retry shall reconcile the prior operation before repeating a sensitive effect.

## 10. Logical object: ScribeDisposition

### 10.1 Purpose and authority

Only Scribe's approved controlled release/evidence decision path may create the
authoritative `ScribeDisposition`.

Forge, Courier, Reaper, Watchtower, Conduit and models cannot create or override
this authority state.

### 10.2 Fields

| Field | Requirement | Logical type | Meaning / validation |
| --- | --- | --- | --- |
| `scribe_authority_identity` | REQUIRED | IdentityReference | Identifies the Scribe authority producing the disposition. |
| `source_requester_context` | CONDITIONAL | IdentityReference | Required when source/requester context is applicable to the Scribe evaluation. |
| `work_package_revision` | REQUIRED | ObjectReference | Exact `WorkPackageRevision`. |
| `artifact_identity` | REQUIRED | ObjectReference | Exact `ArtifactIdentity` evaluated by Scribe. |
| `transfer_correlation_identity` | CONDITIONAL | ObjectReference | Required when the Scribe evaluation derives from or references a Courier transfer/correlation operation. |
| `authorization_policy_reference` | REQUIRED | Reference | Applicable authorization/policy binding for Scribe evaluation. |
| `release_evidence_policy_identity` | REQUIRED | PolicyReference | Identifies the Scribe release/evidence policy applied. |
| `disposition` | REQUIRED | Enum | Exactly one of `ACCEPT`, `REJECT` or `UNKNOWN`. |
| `validation_evaluation_references` | REQUIRED | Reference | References the validation/evaluation evidence required by applicable policy. |
| `reason_reference` | REQUIRED | Reference | Attributable reason or safe reason reference appropriate to policy. |
| `provenance` | OPTIONAL_OR_AVAILABLE | ProvenanceValue | Available disposition provenance. |
| `explicit_unknown_fields` | CONDITIONAL | Reference | Required when information required for interpretation/evaluation remains explicitly unknown. |

### 10.3 Disposition rules

- only Scribe may authoritatively create this state.
- `ACCEPT` establishes only Scribe-controlled release/evidence acceptance.
- `ACCEPT` does not authorize deployment.
- `ACCEPT` does not authorize Conduit execution.
- `ACCEPT` does not grant Forge administration.
- if required identity, integrity, policy or exact revision binding cannot be
  established, disposition shall not be `ACCEPT`.
- the applicable approved policy determines whether a known failure is `REJECT`
  or an unresolved outcome remains `UNKNOWN`.

## 11. Cross-object consistency matrix

| Binding | Objects that shall agree where applicable |
| --- | --- |
| Exact work-package revision | `WorkPackageRevision`, `ArtifactIdentity`, `AuthorizationReference`, `CorrelationIdentity`, `TransferRequest`, `TransferReceipt`, `ScribeDisposition` |
| Authorization | `WorkPackageRevision`, `AuthorizationReference`, `TransferRequest`, `TransferReceipt`, `ScribeDisposition` where applicable |
| Artifact identity | `ArtifactIdentity`, `CorrelationIdentity`, `TransferRequest`, `TransferReceipt`, `ScribeDisposition` |
| Source/requester | `AuthorizationReference`, `CorrelationIdentity`, `TransferRequest`, `TransferReceipt`, `ScribeDisposition` where applicable |
| Target/destination | `AuthorizationReference`, `CorrelationIdentity`, `TransferRequest`, `TransferReceipt` |
| Operation | `AuthorizationReference`, `CorrelationIdentity`, `TransferRequest`, `TransferReceipt` |
| Policy/classification | applicable revision, authorization, artifact, request, receipt and Scribe policy bindings |
| Correlation/history | `CorrelationIdentity`, `TransferRequest`, `TransferReceipt`, `ScribeDisposition` where applicable |
| Completeness | `ArtifactIdentity`, `TransferRequest` validation, `TransferReceipt`, Scribe evaluation where applicable |
| Prior attempt/reconciliation | `CorrelationIdentity`, `TransferRequest`, `TransferReceipt` |

A mismatch in a security-relevant shared binding shall fail the affected
dependent validation.

The model shall not automatically choose one conflicting object as authoritative
unless the approved architecture explicitly assigns that decision to the
responsible receiver.

## 12. Replay, duplicate and retry rules

A repeated operation shall be distinguishable from an unrelated new operation.

The logical model shall preserve enough relationship information to identify:

- exact duplicates;
- detected replay;
- explicit authorized retry;
- known rejected predecessor;
- known incomplete or partial predecessor;
- unresolved `UNKNOWN` predecessor;
- reconciliation status.

A retry shall reference the applicable predecessor.

A sensitive operation with unresolved prior outcome shall not be treated as safe
to repeat merely because a new operation identifier is generated.

Where reconciliation requires a mechanism deferred by DEC-06 through DEC-13,
dependent execution remains blocked.

## 13. Cancellation, revocation and amendment rules

Cancellation or revocation prevents new dependent effects from being authorized
by stale authority.

Queued or pending work shall not be represented as authorized after applicable
authority is cancelled or revoked.

In-flight work with uncertain outcome shall preserve the actual known state or
`UNKNOWN` and enter reconciliation as required.

An amendment creates a distinct new/amended `WorkPackageRevision`.

Historical evidence remains bound to the revision under which it occurred.

## 14. DEC-08 and attributable ordering

The model may preserve:

- attributable time information;
- known uncertainty;
- explicit event ordering;
- predecessor relationships.

The model does not select:

- trusted time source;
- synchronization mechanism;
- skew tolerance;
- numeric freshness interval;
- timestamp replay window;
- time-based authorization guarantee.

Time evidence alone shall not establish trusted freshness.

## 15. Secrets boundary

The logical model shall not require raw:

- passwords;
- private keys;
- bearer tokens;
- authentication secrets;
- release credentials;
- deployment credentials.

Safe references, identifiers, digests or approved redacted representations may
be preserved where applicable.

This model does not select credential technology or custody implementation.

## 16. Technology-neutral boundary

This model does not select:

- JSON;
- JSON Schema;
- YAML;
- TOML;
- XML;
- Protocol Buffers;
- Avro;
- CBOR;
- MessagePack;
- REST;
- gRPC;
- a database;
- a filesystem storage format;
- a transport protocol;
- a listener;
- a daemon;
- a port;
- session direction;
- hash algorithm;
- signature algorithm;
- certificate technology;
- credential technology.

These names identify prohibited premature selections, not implementation
recommendations.

## 17. Deferred decisions

DEC-06 through DEC-13 remain deferred for the initial capability as established
by WP5 and preserved by WP6.1.

This model does not resolve them.

A dependent portion of future implementation preparation shall stop if it
requires one of those unresolved decisions.

## 18. Validation boundary

Future offline structural tests may verify this document's internal consistency
and traceability.

Passing those tests shall establish documentation/model consistency only.

It shall not establish:

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

## 19. WP6.2 stop boundary

Preparation stops before any dependent step that requires:

- concrete serialization or schema technology;
- canonical byte encoding;
- cryptographic algorithm or signing mechanism;
- credential technology or secrets;
- trusted-time mechanism or numeric freshness;
- runtime transport or network behavior;
- workload isolation technology or general runtime resource bounds;
- deployment or Conduit execution;
- host mutation or privileged action;
- AIDE action;
- a change to an approved WP5/WP6.1 authority boundary;
- unexplained repository identity, integrity or source provenance.

The stop condition fails closed and does not authorize a convenient default.

## 20. Readiness statement

This document is a repository-only implementation-preparation artifact.

It defines logical data semantics but does not authorize executable schema
implementation or runtime implementation.

Completion, testing, review or commit of this model does not establish
operational acceptance or authorize the next work package.
