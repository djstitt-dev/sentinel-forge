# Evidence handling and provenance

Existing host AIDE configuration, databases, and trusted history are protected
evidence. Retain them in their established locations. This repository records
references and provenance; it does not replace the host evidence store.

## Required record fields
For each record preserve: identifier, source path or source reference, execution
context, collector, collection time when known, command/method when known,
verification status, and any digest with algorithm and provenance. Record unknown
fields explicitly. Documentation time must not substitute for collection time.
See [context definitions](../docs/inventory/execution-contexts.md).

Separate operator-verified host evidence from independently verified Codex
evidence. A supplied digest is not a digest computed by Codex. A sandbox read of
a similarly named path does not establish host verification. Host evidence whose
user/privileged context was not supplied must retain that uncertainty.

When comparing contexts, label both inputs and document the reason the comparison
is meaningful. Never silently combine records. A hash comparison establishes
byte identity at collection time, not authenticity, policy adequacy, or deployment
authorization. Candidate/trusted equality alone does not authorize promotion.

## Storage and review
Do not add secrets, credentials, private keys, authentication artifacts, raw
sensitive host inventories, or trusted AIDE databases to Git. Do not copy raw
evidence here without an approved handling and sensitivity review. Ignore rules
are defense in depth, not a substitute for content review; do not force-add
excluded material. Use sanitized fixtures for future tests.

Preserve prior evidence and provenance when adding later verification. Do not
overwrite historical evidence or change supplied provenance to claim independent
verification. Record new observations separately with context and time. Stop and
report unexplained differences before any repair or trust change.

## Initial manifest
[aide-anchors.json](manifests/aide-anchors.json) transcribes operator-verified host
evidence supplied in the task. Original commands, times, and user/privileged
context were not supplied. Codex has not independently verified these anchors.
The candidate's digest is not separately claimed: the supplied assertion is
byte equality with the trusted database.

F1.17K42 conceptual closure was reported validated by the operator, but existence
of its final record remains unknown. This documentation is not a closure record.
Creating that record requires separate operator approval after evidence review.
