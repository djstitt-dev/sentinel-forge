# Forge/Courier/Scribe Technology-Neutral Schema Derivation Contract

Status: **WP6.3 DRAFT — repository-only implementation preparation.**

This contract is derived from and bound to committed WP6.2 revision:

`3bb6fb09c77d7ca3e11958dad1b0fc3d61692f5d`

WP6.2 committed tree:

`1eae8065ce361aaf3165803ecdcb667f450ba652`

WP6.2 defines the canonical logical data model for the first bounded
Forge/Courier/Scribe capability.

This document defines semantic derivation requirements for a future concrete
representation of that model.

It is not an executable schema.

It does not select or authorize a schema language, serialization format,
canonical byte encoding, runtime implementation, storage mechanism, transport,
network behavior, credential mechanism, cryptographic mechanism, deployment
mechanism, Conduit execution, host mutation or AIDE action.

## 1. Purpose

A future concrete representation may be considered a conformant derivation of
the WP6.2 canonical logical model only when it preserves the consequential
semantics defined by WP5, WP6.1 and WP6.2.

Representation convenience shall not weaken:

- identity;
- integrity;
- authorization;
- scope;
- target;
- operation;
- policy;
- classification;
- correlation;
- completeness;
- provenance;
- replay and retry state;
- outcome or disposition;
- authority separation.

Schema validity is a structural property.

Structural validity is not authorization.

## 2. Governing authority

This derivation contract remains subordinate to:

1. the operator;
2. the approved WP5 architecture and requirements;
3. the committed WP6.1 Forge/Courier/Scribe logical contract;
4. the committed WP6.2 canonical logical data model.

If a future representation cannot preserve a governing semantic without
resolving a deferred architectural decision, derivation shall stop.

A representation mechanism shall not be selected merely because it is
convenient, familiar, available in a toolchain or suggested by an AI system.

AI output is proposed engineering input.

AI output does not constitute architecture approval, security approval,
transfer authority, release authority or deployment authority.

## 3. Derivation boundary

WP6.3 defines semantic requirements only.

It does not select:

- a schema language;
- a serialization format;
- a wire format;
- a canonical byte representation;
- a programming language;
- a runtime framework;
- a storage technology;
- a database technology;
- a filesystem representation;
- a transport protocol;
- a session model;
- a listener;
- a daemon;
- a port;
- a network direction;
- a cryptographic algorithm;
- a signature algorithm;
- a certificate technology;
- a credential technology;
- a key-custody implementation;
- a deployment mechanism;
- a Conduit implementation.

Technologies such as JSON, JSON Schema, YAML, TOML, XML, Protocol Buffers,
Avro, CBOR, MessagePack, ASN.1, REST, gRPC and database-specific schema
languages are examples of choices not made by WP6.3.

Mentioning a technology in this prohibition does not approve it.

## 4. Canonical logical object inventory

Every conformant future representation shall provide an attributable semantic
mapping for each of the seven WP6.2 logical objects:

1. `WorkPackageRevision`
2. `ArtifactIdentity`
3. `AuthorizationReference`
4. `CorrelationIdentity`
5. `TransferRequest`
6. `TransferReceipt`
7. `ScribeDisposition`

A representation shall not silently merge two canonical logical objects when
that merge would erase authority, identity, provenance, lifecycle or
validation distinctions.

A representation shall not split a canonical logical object in a manner that
makes required consequential semantics impossible to reconstruct or validate.

Representation structure may differ from logical structure only when semantic
equivalence remains attributable and independently verifiable.

## 5. Canonical field inventory

The committed WP6.2 model defines 83 logical fields.

Requirement-class totals are:

- `REQUIRED`: 65
- `CONDITIONAL`: 11
- `OPTIONAL_OR_AVAILABLE`: 7
- total: 83

A conformant derivation shall account for every canonical field.

A future representation shall not silently:

- remove a canonical field;
- invent a replacement semantic;
- rename a field without attributable mapping;
- merge consequentially distinct fields;
- weaken a requirement class;
- strengthen a requirement class in a manner that fabricates information;
- assign authority not present in the canonical model.

The committed WP6.2 source remains authoritative for the exact per-object field
inventory.

## 6. Exact CONDITIONAL field set

The following fields are `CONDITIONAL` in WP6.2 and shall retain that semantic
classification unless a later operator-approved canonical-model revision
changes it:

- `WorkPackageRevision.supersession_amendment_relationship`
- `ArtifactIdentity.source_candidate_build_workspace`
- `AuthorizationReference.validity_information`
- `CorrelationIdentity.artifact_identity`
- `CorrelationIdentity.predecessor_retry_relationship`
- `CorrelationIdentity.reconciliation_state`
- `TransferReceipt.destination_acknowledgement_state`
- `TransferReceipt.failure_information`
- `ScribeDisposition.source_requester_context`
- `ScribeDisposition.transfer_correlation_identity`
- `ScribeDisposition.explicit_unknown_fields`

A concrete representation shall not make these fields universally required or
universally absent merely because doing so simplifies a schema.

Their applicability is controlled by their canonical logical semantics.

## 7. Requirement-class preservation

### 7.1 REQUIRED

A `REQUIRED` logical field remains semantically required.

If a required security-relevant fact cannot be established, the representation
shall preserve the applicable unknown, unavailable or other fail-closed
semantic defined by the canonical model.

Missing information shall not become a positive assertion.

### 7.2 CONDITIONAL

A `CONDITIONAL` logical field is required when its governing logical condition
applies.

Its representation shall preserve enough information to determine or
independently validate that condition where the governing model requires such
determination.

### 7.3 OPTIONAL_OR_AVAILABLE

An `OPTIONAL_OR_AVAILABLE` field shall not be fabricated merely to satisfy a
representation.

Where the canonical model requires available information to be preserved, a
representation shall not silently discard it.

Optionality does not permit fabrication.

## 8. Logical type preservation

WP6.2 defines technology-neutral semantic types.

A conformant future derivation shall preserve the distinctions represented by:

- `Identifier`
- `Reference`
- `Text`
- `Enum`
- `BooleanState`
- `IdentityReference`
- `PrincipalReference`
- `TargetReference`
- `PolicyReference`
- `IntegrityReference`
- `ObjectReference`
- `RelationshipReference`
- `OrderedEventReference`
- `TimeEvidence`
- `ProvenanceValue`
- `UnknownCapableValue`
- `CompletenessState`
- `ReconciliationState`

A future representation may use representation-specific constructs only after
that representation technology is separately authorized.

Representation-specific convenience shall not collapse logical types when the
distinction affects security, authority, provenance, interpretation or
validation.

## 9. ObjectReference semantics

`ObjectReference` identifies or references another canonical logical object.

It does not require recursive embedding of the referenced object's complete
canonical representation.

A future representation may define an approved concrete reference mechanism
only after the representation technology is separately selected and
authorized.

Failure to resolve a required reference shall not:

- fabricate the referenced object;
- infer its contents;
- infer authorization;
- infer successful validation;
- infer completeness;
- infer a safe retry state.

A reference mechanism shall not create authority merely by resolving
successfully.

## 10. Unknown, unavailable, absent and redacted semantics

A conformant derivation shall preserve applicable distinctions among:

- known;
- not applicable;
- unknown;
- unavailable;
- redacted;
- approved safe reference;
- `UNKNOWN`;
- `PARTIAL`;
- `INCOMPLETE`.

Bare absence shall not be used where it would make two consequential semantic
states indistinguishable.

A representation shall not collapse unknown, unavailable or redacted
information into a known value.

A representation shall not collapse `UNKNOWN`, `PARTIAL` or `INCOMPLETE` into
success, completion or acceptance.

Unknown security-relevant information shall not default to:

- authorized;
- authenticated;
- valid;
- complete;
- successful;
- accepted;
- fresh;
- intact;
- attributable;
- reconciled;
- safe to retry.

## 11. Transfer disposition vocabulary

The exact WP6.2 transfer disposition vocabulary is:

- `PROPOSED`
- `REJECT`
- `INCOMPLETE`
- `PARTIAL`
- `UNKNOWN`
- `TRANSFERRED`

A conformant representation shall preserve these meanings.

It shall not silently map multiple consequential transfer states into a single
success state.

`TRANSFERRED` means only that Courier's controlled transfer operation reached
the transfer-completion state defined by the governing contract.

`TRANSFERRED` does not mean:

- Scribe `ACCEPT`;
- release approval;
- deployment approval;
- Conduit authorization;
- host-administration authorization;
- security approval.

## 12. Scribe disposition vocabulary

The exact WP6.2 Scribe disposition vocabulary is:

- `ACCEPT`
- `REJECT`
- `UNKNOWN`

Only Scribe's approved controlled decision path may create authoritative Scribe
disposition.

A conformant representation shall not allow Forge, Courier, Reaper, Watchtower,
Conduit, an AI model, a parser or schema validation result to manufacture
Scribe `ACCEPT`.

Scribe `ACCEPT` means controlled release/evidence acceptance under applicable
Scribe policy.

Scribe `ACCEPT` does not authorize:

- deployment;
- Conduit execution;
- host administration;
- privilege expansion;
- credential use;
- network reconfiguration;
- trust-anchor modification;
- AIDE modification;
- another consequential effect outside Scribe's approved authority.

## 13. Structural validity and authority

A representation can be structurally valid and still be unauthorized for use.

Structural validity shall not establish:

- principal authority;
- operation authority;
- target authority;
- transfer authority;
- release authority;
- deployment authority;
- freshness;
- replay safety;
- integrity;
- provenance;
- completeness.

A structurally valid `TransferRequest` does not authorize transfer.

Courier remains responsible for its independent controlled-transfer decision
under applicable authority and policy.

A structurally valid `ScribeDisposition` representation does not allow another
component to create authoritative Scribe disposition.

Authority remains with the component and decision path defined by the governing
architecture.

## 14. Cross-object consistency

A conformant future representation shall permit independent validation of
applicable shared consequential bindings.

These include:

- exact work-package revision;
- authorization;
- artifact identity;
- source/requester;
- target/destination;
- operation;
- policy/classification;
- correlation;
- predecessor/retry relationship;
- outcome/disposition;
- completeness;
- provenance.

When multiple logical objects bind the same consequential fact, those bindings
shall agree.

A conflicting consequential binding shall fail validation.

A representation or implementation shall not silently:

- rewrite the conflict;
- merge conflicting identities;
- normalize away the difference;
- choose one conflicting value;
- infer which value was intended;
- convert the conflict into success.

Schema validity alone does not satisfy cross-object consistency.

## 15. Artifact identity and substitution resistance

A future representation shall preserve the distinction between an artifact's
identity, its integrity reference, its provenance, its source work-package
revision and its completeness state.

Representation transformation shall not permit an artifact to acquire the
identity or authority of another artifact merely because fields are
syntactically compatible.

Substitution or identity mismatch shall remain detectable and fail closed.

A representation shall not manufacture provenance for an artifact whose
required provenance cannot be established.

## 16. Authorization binding

Authorization shall remain explicitly attributable to the applicable
`AuthorizationReference` and exact governed operation context.

A representation shall not infer authorization from:

- successful parsing;
- successful schema validation;
- authentication alone;
- possession of an object;
- possession of an artifact;
- network reachability;
- tool availability;
- prior successful operation;
- AI recommendation;
- another component's authority.

Authorization for one principal, role, operation, target or work-package
revision shall not be widened to another.

Revoked or cancelled authority shall not be represented as valid authority.

## 17. Correlation, predecessor, retry and replay

A future representation shall preserve operation correlation identity and
applicable predecessor, retry, duplicate and replay relationships.

A retry shall not silently appear to be an unrelated clean first attempt when
the governing model requires preservation of prior-attempt state.

Where a prior sensitive operation is:

- `UNKNOWN`;
- `PARTIAL`;
- `INCOMPLETE`;

the unresolved state shall survive derivation.

A future implementation shall not repeat a sensitive effect merely because a
representation can be parsed or validated.

Required reconciliation shall occur before a repeat effect when the governing
contract requires it.

If reconciliation depends on a mechanism deferred by DEC-06 through DEC-13,
the dependent action shall stop rather than assume a safe retry.

## 18. Cancellation, revocation, amendment and supersession

A conformant derivation shall preserve historical attribution for:

- cancellation;
- revocation;
- amendment;
- supersession.

A newer representation, revision or relationship shall not erase the identity
or disposition of an earlier object.

A superseding object shall not rewrite historical evidence to make the earlier
object appear as though it never existed.

Cancellation or revocation shall not be represented as successful completion.

## 19. Completeness

Completeness is security-relevant state.

A representation shall preserve whether an object or operation is complete,
incomplete or otherwise subject to an explicit canonical completeness state.

Incomplete input shall not become accepted output merely through:

- serialization;
- parsing;
- schema validation;
- transfer;
- retry;
- reconstruction;
- default values.

`INCOMPLETE` shall not silently become complete.

`PARTIAL` transfer state shall not silently become `TRANSFERRED`.

## 20. Provenance

Where provenance is required or available under the canonical model, a
representation shall preserve attributable provenance or the applicable
explicit unknown/unavailable/safe-reference semantic.

A representation shall not fabricate provenance.

Redaction shall not be represented as though raw provenance were present.

Absence of provenance shall not be converted into a trusted provenance claim.

## 21. Canonical identity participation

WP6.2 requires canonical integrity identity for applicable logical content.

A future representation shall preserve which consequential semantics
participate in the applicable logical identity.

WP6.3 does not define:

- canonical bytes;
- byte ordering;
- field ordering;
- serialization ordering;
- whitespace normalization;
- normalized byte representation;
- text encoding;
- hash algorithm;
- signature algorithm;
- certificate technology;
- key technology.

A representation shall not silently exclude security-relevant semantic content
from an integrity identity when the governing model requires that content to
participate.

Canonical logical identity is not equivalent to a selected canonical byte
encoding.

## 22. DEC-08 time and ordering boundary

DEC-08 remains deferred.

WP6.3 does not select:

- a trusted time source;
- a clock-skew tolerance;
- a freshness interval;
- an expiry interval;
- a replay time window;
- a time-based authorization guarantee.

`TimeEvidence` remains attributable evidence with known uncertainty where
available.

`OrderedEventReference` may preserve attributable logical ordering.

Neither type independently establishes trusted chronological freshness.

A future representation shall not turn the presence of a timestamp into proof
of freshness, authorization or replay safety.

## 23. Schema and representation evolution

Representation evolution shall not create authority.

Every later concrete representation shall have an attributable version or
equivalent identity sufficient to determine which approved interpretation
applies.

A newer or unsupported representation shall not be silently accepted merely
because a parser can consume it.

Historical records shall remain interpretable according to the approved
semantics that governed them.

Unknown fields or extensions shall not:

- create authority;
- widen scope;
- change target;
- change operation;
- convert failure to success;
- convert unknown to known;
- erase provenance;
- erase replay relationships;
- manufacture release or deployment approval.

Backward compatibility, forward compatibility, extension behavior, migration
and unknown-field policy remain later explicit decisions.

WP6.3 selects none of those mechanisms.

## 24. Semantic round-trip requirement

A future approved concrete representation shall be capable of demonstrating
semantic preservation conceptually as:

canonical logical object
→ concrete representation
→ logical interpretation

The resulting logical interpretation shall preserve all consequential
semantics required by the governing canonical model.

This requirement concerns semantic equivalence.

WP6.3 does not require or define byte-for-byte equality.

WP6.3 does not select:

- serializer;
- parser;
- codec;
- normalization mechanism;
- comparison mechanism.

A representation that round-trips syntactically while losing consequential
security semantics is not conformant.

## 25. Conformance evidence

Future derivation acceptance evidence shall demonstrate attributable mapping
for every canonical object and field.

At minimum, evidence shall establish that:

1. all seven canonical logical objects are represented;
2. all 83 canonical fields remain attributable;
3. the 65/11/7 requirement-class distribution remains preserved;
4. the exact conditional field set remains preserved;
5. logical type distinctions remain semantically preserved;
6. unknown-state distinctions remain preserved;
7. transfer disposition vocabulary remains exact;
8. Scribe disposition vocabulary remains exact;
9. reference semantics remain attributable;
10. cross-object consistency remains independently enforceable;
11. structural validity cannot manufacture authority;
12. retry/replay state remains attributable;
13. cancellation/revocation/amendment history remains attributable;
14. canonical identity participation remains semantically preserved;
15. deferred decisions remain deferred unless separately approved;
16. representation evolution creates no authority;
17. semantic round-trip requirements are met.

Passing syntax or schema validation alone does not establish:

- operational correctness;
- operational security;
- authorization;
- transfer authority;
- release acceptance;
- deployment authority;
- runtime readiness;
- production readiness.

## 26. Negative conformance cases

Future concrete-representation testing shall include negative cases sufficient
to demonstrate fail-closed handling.

At minimum, testing shall cover:

1. omitted REQUIRED security-relevant field;
2. invalid enum value;
3. unsupported logical-object type;
4. unsupported representation or schema version;
5. conflicting work-package revision;
6. conflicting authorization;
7. artifact substitution;
8. target mismatch;
9. operation mismatch;
10. malformed required reference;
11. unresolved required reference;
12. fabricated provenance;
13. unknown value collapsed to success;
14. `UNKNOWN` disposition collapsed to success;
15. `PARTIAL` collapsed to complete or transferred;
16. `INCOMPLETE` collapsed to complete;
17. retry without a required predecessor relationship;
18. replay treated as a fresh operation without required reconciliation;
19. revoked authority treated as valid;
20. cancelled authority treated as valid;
21. `TRANSFERRED` interpreted as Scribe `ACCEPT`;
22. `TRANSFERRED` interpreted as deployment authority;
23. Scribe `ACCEPT` interpreted as deployment authority;
24. Scribe `ACCEPT` interpreted as Conduit authority;
25. representation validity interpreted as authorization;
26. unknown field interpreted as authority expansion.

A negative case that cannot be evaluated because it depends on an unresolved
architecture decision shall remain blocked rather than be assigned a
convenient default.

## 27. Authority-domain preservation

Forge, Courier, Scribe, Reaper, Watchtower and Conduit remain distinct
authority domains.

Representation, communication, reachability, tooling and successful validation
do not transfer authority between them.

In particular:

- Forge may prepare authorized candidates and requests but cannot self-grant
  transfer, release or deployment authority;
- Courier controls its authorized transfer function but cannot manufacture
  Scribe release acceptance or deployment authority;
- Scribe controls its approved release/evidence disposition but cannot thereby
  manufacture deployment authority;
- Reaper findings do not independently authorize remediation, release,
  deployment or trust changes;
- Watchtower observations and alerts do not create command authority;
- Conduit enforces separately applicable authorized management/deployment
  operations and does not create the authorization it enforces;
- AI systems may propose engineering output but cannot approve their own work
  or acquire any of these authority domains.

## 28. Automation and autonomous engineering boundary

The derivation contract is intended to support future bounded automation.

Future Forge automation may, when separately authorized and implemented:

- derive candidate representations from approved canonical models;
- generate candidate implementation artifacts;
- validate candidate mappings;
- execute approved offline structural tests;
- compare candidate semantics against governing contracts;
- detect semantic drift;
- reject nonconformant candidates;
- preserve attributable evidence;
- prepare candidates for operator review and later controlled handoff.

Automation shall not infer that successful generation or validation grants
permission for the next consequential action.

A future automated engineering loop shall preserve separate states for:

- proposal;
- generation;
- validation;
- rejection;
- revision;
- operator decision;
- transfer disposition;
- Scribe disposition;
- deployment disposition where separately authorized in the future.

No loop may convert its own successful tests into architecture approval,
security approval, release approval or deployment approval.

The operator remains the architecture/security approval authority unless a
future explicit operator-approved delegation defines a narrower automated
decision.

WP6.3 does not create such a delegation.

## 29. Deferred decisions

DEC-06 through DEC-13 remain deferred exactly as established by WP5 and
preserved by WP6.1 and WP6.2.

WP6.3 does not resolve:

- DEC-06 egress/external providers;
- DEC-07 Watchtower export/retention/failure behavior;
- DEC-08 trusted time/freshness;
- DEC-09 backup/recovery;
- DEC-10 RTO/RPO/outage;
- DEC-11 Cerberus administration;
- DEC-12 deployment;
- DEC-13 workload/isolation/capacity.

Deferral creates no executable default.

A future derivation or implementation that becomes dependent on one of these
decisions shall stop at that dependency until applicable authority resolves it.

## 30. Secrets and sensitive material

A future representation shall not require raw secrets as ordinary canonical
model fields.

Credential material, private keys, tokens, passwords and equivalent secrets
remain outside ordinary Forge/Courier/Scribe canonical payload semantics unless
a later explicit architecture decision defines a separately protected
mechanism.

A representation shall not require retention of sensitive raw content where
the governing model permits an approved safe reference or redacted
representation.

## 31. Numeric and capacity defaults

WP6.3 selects no numeric defaults for:

- field size;
- artifact size;
- message size;
- rate;
- concurrency;
- retry count;
- timeout;
- retention;
- freshness;
- clock skew;
- capacity;
- resource consumption.

Where a future implementation requires such a bound, the bound shall come from
applicable approved architecture or a separately authorized implementation
decision.

Absence of a bound does not authorize an unlimited operational value.

## 32. Repository-only WP6.3 verification

Repository structural tests may verify this contract against the committed
WP6.2 canonical model.

Such tests may verify:

- revision/tree binding;
- object inventory;
- field inventory;
- requirement-class counts;
- conditional-field inventory;
- logical type vocabulary;
- state vocabulary;
- authority boundaries;
- unknown-state semantics;
- reference semantics;
- cross-object consistency requirements;
- retry/replay semantics;
- canonical identity deferrals;
- DEC-08 limitations;
- DEC-06 through DEC-13 deferrals;
- representation-evolution boundaries;
- semantic round-trip requirements;
- negative-conformance coverage.

These repository tests are documentation and semantic-consistency checks.

They are not operational acceptance.

They do not establish runtime correctness, runtime security, host readiness,
network readiness, credential readiness, Courier readiness, Scribe readiness,
deployment readiness or production readiness.

## 33. Stop conditions

WP6.3 shall fail closed if preparation requires:

- selection of a concrete schema language;
- selection of a serialization technology;
- selection of canonical bytes;
- selection of field or serialization ordering;
- selection of a cryptographic primitive;
- selection of credential technology;
- selection of runtime language or framework;
- selection of storage technology;
- selection of transport/session technology;
- selection of network behavior;
- selection of deployment behavior;
- implementation of Conduit behavior;
- host mutation;
- protected AIDE mutation;
- resolution of DEC-06 through DEC-13;
- weakening or changing WP6.2 canonical semantics;
- expansion of an authority domain;
- a consequential architecture decision not already approved.

The stop condition is fail closed.

It is not permission to infer or choose a default.

## 34. WP6.3 completion boundary

WP6.3 may be considered complete only when:

1. this derivation contract binds to the exact committed WP6.2 revision and
   tree;
2. all seven logical objects are accounted for;
3. all 83 fields remain attributable;
4. requirement classes remain 65 REQUIRED, 11 CONDITIONAL and
   7 OPTIONAL_OR_AVAILABLE;
5. the exact conditional field set remains preserved;
6. logical type distinctions remain preserved;
7. unknown and failure-state semantics remain fail closed;
8. authority separation remains explicit;
9. cross-object consistency remains enforceable;
10. replay/retry/reconciliation semantics remain preserved;
11. canonical byte/crypto/runtime choices remain unselected;
12. DEC-06 through DEC-13 remain deferred;
13. repository structural tests pass;
14. the complete offline regression suite passes;
15. the operator explicitly approves the WP6.3 candidate.

Completion of WP6.3 does not authorize selection or implementation of a
concrete schema technology.

Completion of WP6.3 does not authorize runtime implementation.

Completion of WP6.3 does not authorize transfer, release or deployment.

Any subsequent concrete-schema or runtime work requires a separately
authorized work package and any applicable architecture decisions.
