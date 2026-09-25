# WP6.3 Schema Derivation Contract Preparation

Status: **WP6.3 DRAFT — repository-only implementation preparation.**

Parent revision:

`3bb6fb09c77d7ca3e11958dad1b0fc3d61692f5d`

Parent tree:

`1eae8065ce361aaf3165803ecdcb667f450ba652`

WP6.3 is derived from the operator-approved and committed WP6.2 canonical
logical data model.

This work package does not authorize executable schema implementation, runtime
implementation, host mutation, transport, networking, credentials, deployment,
Conduit execution, AIDE action, or resolution of deferred WP5 decisions.

## 1. Purpose

WP6.3 shall define a technology-neutral schema derivation contract for the
Forge/Courier/Scribe canonical logical data model.

The contract shall state the invariants that any later concrete representation
must preserve before that representation can be considered a conformant
derivation of the WP6.2 logical model.

WP6.3 shall not select a schema language, serialization format, canonical byte
encoding, transport format, programming language, database representation,
cryptographic primitive, runtime framework, or deployment mechanism.

## 2. Governing sources

WP6.3 remains subordinate to:

1. WP5 operational architecture and requirements;
2. WP6.1 Forge/Courier/Scribe logical contract;
3. WP6.2 canonical logical data model;
4. operator authority and all existing stop boundaries.

If a WP6.3 proposal conflicts with a governing source, the governing source
controls and the conflicting proposal shall fail closed.

## 3. Authorized preparation scope

WP6.3 may define repository-only requirements for:

- logical-object-to-schema derivation;
- logical-field-to-schema derivation;
- preservation of requirement classes;
- preservation of logical field types;
- enum vocabulary preservation;
- reference semantics;
- explicit unknown/unavailable/redacted/not-applicable semantics;
- cross-object binding consistency;
- canonical identity participation boundaries;
- structural validation semantics;
- authority-separation preservation;
- retry, replay and predecessor relationship preservation;
- cancellation, revocation, amendment and supersession preservation;
- schema evolution constraints;
- conformance evidence expectations;
- later implementation acceptance criteria.

These are derivation requirements only.

They do not authorize a concrete schema implementation.

## 4. Prohibited WP6.3 selections

WP6.3 shall not select or imply:

- JSON;
- JSON Schema;
- YAML;
- TOML;
- XML;
- Protocol Buffers;
- Avro;
- CBOR;
- MessagePack;
- ASN.1;
- REST;
- gRPC;
- database schema technology;
- filesystem representation;
- field numbering;
- wire tags;
- byte ordering;
- canonical serialization;
- canonical byte encoding;
- hash algorithm;
- signature algorithm;
- certificate technology;
- credential technology;
- transport/session technology;
- listener, daemon, port or network direction;
- runtime language or framework;
- numeric size, rate, timeout, concurrency or retention defaults;
- trusted time, skew or freshness bounds;
- deployment behavior;
- Conduit behavior.

Mentioning such technologies as examples of prohibited premature selection does
not constitute approval.

## 5. Derivation invariants

Any later concrete representation shall preserve the semantic meaning of the
WP6.2 model without weakening or expanding authority.

At minimum, derivation rules shall preserve:

1. all seven WP6.2 logical objects;
2. the exact logical field inventory unless a later operator-approved revision
   changes that inventory;
3. REQUIRED, CONDITIONAL and OPTIONAL_OR_AVAILABLE semantics;
4. the distinction between structural validity and authorization;
5. exact transfer and Scribe disposition vocabularies;
6. explicit UNKNOWN, PARTIAL and INCOMPLETE semantics;
7. not-applicable versus unknown/unavailable versus redacted/safe-reference
   distinctions;
8. exact work-package revision binding;
9. authorization binding;
10. source/requester identity;
11. target/destination identity;
12. operation identity;
13. artifact identity;
14. policy/classification binding;
15. correlation identity;
16. predecessor/retry/replay relationships;
17. outcome/disposition semantics;
18. completeness semantics;
19. provenance semantics;
20. cancellation, revocation, amendment and supersession history;
21. nonrecursive ObjectReference semantics unless a later approved design
    explicitly changes that boundary;
22. DEC-08 limitations on time/freshness;
23. DEC-06 through DEC-13 deferrals;
24. authority separation among Forge, Courier, Scribe, Reaper, Watchtower and
    Conduit.

A representation that loses or silently changes any consequential semantic
shall not be considered conformant.

## 6. Field requirement-class derivation

A later representation shall not reinterpret:

- REQUIRED as optional;
- CONDITIONAL as always absent or always present without semantic basis;
- OPTIONAL_OR_AVAILABLE as fabricated mandatory data.

A missing required security-relevant value shall not be silently converted into
a positive or authorized state.

Conditional presence shall be driven by the logical condition defined by the
canonical model, not merely by syntactic convenience.

## 7. Logical type derivation

WP6.2 logical field types are semantic contracts.

A later schema may realize them using representation-specific mechanisms only
after separate operator authorization.

The concrete mechanism shall preserve the logical distinctions represented by:

- Identifier;
- Reference;
- Text;
- Enum;
- BooleanState;
- IdentityReference;
- PrincipalReference;
- TargetReference;
- PolicyReference;
- IntegrityReference;
- ObjectReference;
- RelationshipReference;
- OrderedEventReference;
- TimeEvidence;
- ProvenanceValue;
- UnknownCapableValue;
- CompletenessState;
- ReconciliationState.

Representation-specific type convenience shall not collapse semantically
distinct logical types where doing so would weaken validation, authority,
provenance or interpretation.

## 8. Unknown and unavailable-state preservation

A later representation shall be capable of preserving, where applicable:

- known value;
- not applicable;
- unknown;
- unavailable;
- redacted;
- approved safe reference;
- UNKNOWN disposition/outcome;
- PARTIAL transfer state;
- INCOMPLETE object or transfer state.

A representation shall not rely on bare field absence when that absence would
make two security-relevant states indistinguishable.

No unknown security-relevant value may default to authorization, success,
completion, acceptance, freshness, integrity, provenance or safe retry.

## 9. Reference derivation

ObjectReference and other logical reference types shall preserve attributable
identity without requiring recursive embedding of complete referenced objects.

A later representation shall define how references are represented only after
the representation technology is separately approved.

Reference resolution failure shall not silently create or infer a referenced
object.

Conflicting consequential references shall fail validation rather than be
silently rewritten, merged or normalized.

## 10. Cross-object consistency

Any later concrete schema and implementation shall permit validation that
shared consequential bindings agree across objects.

At minimum this includes:

- work-package revision;
- authorization;
- artifact;
- source/requester;
- destination/target;
- operation;
- policy/classification;
- correlation;
- predecessor/retry relationship;
- applicable disposition/outcome.

Schema validity alone shall not satisfy this consistency requirement.

## 11. Canonical identity boundary

WP6.3 may define which semantic content participates in canonical identity
requirements.

WP6.3 shall not define:

- canonical bytes;
- serialization ordering;
- field ordering;
- whitespace rules;
- normalized byte representation;
- hash algorithm;
- signature algorithm.

Those remain later implementation decisions.

A later representation shall not silently exclude security-relevant semantic
content from an integrity identity when the governing logical model requires
that content to participate.

## 12. Schema evolution boundary

A later concrete schema shall not gain authority merely through version change.

Future schema evolution shall preserve:

- explicit version identity;
- exact applicable work-package revision;
- backward/forward compatibility policy where approved;
- unknown-field handling policy where approved;
- prohibition on silently accepting a newer or unsupported representation;
- historical interpretation of previously accepted records.

No compatibility strategy is selected by WP6.3.

## 13. Conformance model

WP6.3 shall define conformance at the semantic level.

Later concrete-schema conformance evidence shall demonstrate, at minimum:

- every canonical logical object has a representation;
- every canonical field has an attributable mapping;
- requirement classes are preserved;
- enum vocabularies are preserved;
- unknown-state semantics are preserved;
- references retain their intended meaning;
- cross-object consistency remains independently enforceable;
- representation validity cannot manufacture authorization;
- TRANSFERRED cannot become Scribe ACCEPT;
- Scribe ACCEPT cannot become deployment or Conduit authority;
- replay/retry relationships are preserved;
- deferred decisions remain unresolved unless separately approved.

Passing schema validation alone shall not establish operational correctness,
authorization, release, deployment or runtime security.

## 14. Round-trip semantic preservation

WP6.3 may require a future approved representation to demonstrate semantic
round-trip preservation:

logical object
→ concrete representation
→ logical interpretation

The interpreted result shall preserve the consequential semantics of the
original logical object.

WP6.3 does not select the concrete encoding, parser, serializer or comparison
mechanism used to demonstrate this property.

Byte-for-byte round-trip identity is not required or defined by WP6.3.

## 15. Negative conformance expectations

Future representation testing shall reject or fail closed on examples such as:

- omitted REQUIRED security-relevant fields;
- invalid enum values;
- unsupported logical-object type;
- unknown representation/schema version where acceptance is not explicitly
  authorized;
- conflicting work-package revision references;
- conflicting authorization references;
- artifact substitution;
- target or operation mismatch;
- malformed or unresolved required references;
- fabricated provenance;
- unknown state collapsed to success;
- incomplete or partial state collapsed to complete;
- retry without required predecessor relationship;
- replay treated as a fresh operation without reconciliation;
- revoked/cancelled authority treated as valid;
- TRANSFERRED interpreted as Scribe ACCEPT;
- Scribe ACCEPT interpreted as deployment authority.

## 16. Deferred decisions

DEC-06 through DEC-13 remain deferred exactly as established by WP5 and
preserved by WP6.1 and WP6.2.

WP6.3 shall stop any dependent preparation that requires resolution of one of
those decisions.

Deferral creates no executable default.

## 17. Planned WP6.3 deliverables

Subject to separate review after this plan, WP6.3 may prepare:

1. this work-package plan;
2. a technology-neutral schema derivation contract;
3. repository-only structural tests validating that contract against the
   committed WP6.2 canonical model.

No executable schema file is authorized by this plan.

No application/runtime package is authorized by this plan.

## 18. Stop conditions

WP6.3 preparation shall stop if:

- a concrete schema or serialization technology must be selected;
- a canonical byte representation must be selected;
- a cryptographic mechanism must be selected;
- a runtime implementation decision is required;
- a host, credential, transport, network or deployment action is required;
- Conduit behavior must be implemented;
- protected AIDE state would be touched;
- DEC-06 through DEC-13 becomes an active unresolved dependency;
- the proposed derivation changes WP6.2 semantics;
- authority would be expanded beyond approved WP5/WP6 boundaries;
- operator approval is required for a consequential architecture decision.

The stop condition is fail closed.

It is not permission to choose a convenient implementation default.

## 19. Verification expectations

Before WP6.3 can be considered complete:

1. the derivation contract shall bind to the exact committed WP6.2 revision;
2. every logical object and field class shall be accounted for;
3. unknown-state semantics shall be preserved;
4. authority-separation rules shall be explicit;
5. cross-object consistency requirements shall remain enforceable;
6. DEC-06 through DEC-13 shall remain deferred;
7. no concrete schema/runtime/crypto/transport technology shall be selected;
8. repository structural tests shall pass;
9. the full offline regression suite shall pass;
10. the operator shall explicitly approve the WP6.3 candidate.

## 20. Exit condition

WP6.3 may exit only after its technology-neutral schema derivation contract and
repository structural tests have been reviewed, verified and explicitly
approved by the operator.

Completion of WP6.3 shall not authorize selection or implementation of a
concrete schema technology.

Any concrete schema work requires a subsequent separately authorized work
package and any architecture decisions required by that work.
