# Execution contexts and initial observations

Initially recorded during Work Package 2 on 2026-09-22; supplemented by WP4B
operator reconciliation on 2026-09-22. The initial documentation date does not
establish the original collection time of Work Package 2 operator evidence.

## Context definitions
| Context | Meaning |
| --- | --- |
| CODEX SANDBOX CONTEXT | Commands run by Codex in its isolated execution environment; exposed state may differ from Forge. |
| FORGE USER HOST CONTEXT | Commands explicitly executed on the actual Forge host as forgeadmin without escalation. |
| FORGE PRIVILEGED HOST CONTEXT | Commands explicitly executed on the actual Forge host with operator-approved escalation. |

Never infer host state from sandbox observations or silently merge observations
across contexts. A username, filesystem path, or hostname alone is insufficient
proof of execution context. If supplied evidence lacks its privilege context,
retain the host attribution and mark user/privileged classification unknown.

## Historical Work Package 2 operator-observed assertions
Source: operator's Work Package 2 instruction. Collector: operator. Original
collection times and commands were not supplied. Codex has not independently
verified these facts on the host. Host origin is explicitly supplied; whether
each command used FORGE USER HOST CONTEXT or FORGE PRIVILEGED HOST CONTEXT was
not specified.

| Fact | Operator-reported value |
| --- | --- |
| Hostname | `sentinel-forge` |
| Account | `forgeadmin` |
| Host-only IPv4 | `192.168.56.104/24` |
| Underlying OS, previously reported from host shell | Ubuntu 24.04.4 — superseded by WP4B reconciliation on 2026-09-22 |
| AIDE version | 0.19.2 |

These limited facts were explicitly supplied for governance documentation. They
are not a raw host inventory or proof of current security-control effectiveness.

## Current operator-verified host identity: WP4B reconciliation
Source: operator's WP4B reconciliation report dated 2026-09-22. Collector:
operator. Context: **FORGE PRIVILEGED HOST CONTEXT**, explicitly established on
the actual host. Codex transcribed these supplied facts; it did not independently
verify them on the host. Original reconciliation commands were not supplied.

| Identity/configuration fact | Operator-observed value |
| --- | --- |
| Hostname | `sentinel-forge` |
| Machine ID | `c1c620cdbd8b4c4fbdd827ed2d769b4f` |
| Virtualization | `oracle` / VirtualBox |
| Host-only network | `enp0s8`, `192.168.56.104/24` |
| Operating system | Ubuntu 26.04.1 LTS; `VERSION_ID=26.04`; `VERSION_CODENAME=resolute` |
| Kernel | Linux `7.0.0-31-generic` |
| Architecture | x86-64 |

These are the reconciled identity/configuration values, not guarantees that OS,
kernel, or network configuration can never change. The prior Ubuntu 24.04.4
operator assertion was incorrect/stale and is explicitly superseded. This does
not establish an upgrade event or its timing. The earlier AIDE version assertion
is historical and was not reverified by this reconciliation.

Transient/contextual reconciliation evidence, not permanent machine identity:

| Observation | Operator-reported value |
| --- | --- |
| Boot ID | `93b7f67d-8a7a-4df5-bc9a-106754ad95a2` |
| Boot time | `2026-09-22 19:56:15` (timezone not supplied) |
| Root filesystem | `/dev/mapper/ubuntu--vg-ubuntu--lv`, ext4 |
| NAT interface | `enp0s3`, `10.0.2.15/24` |
| Repository HEAD during reconciliation | `b2a7c57777c9eaf6115c77299341006ec46d6af4` |

The operator reports that the WP4B preflight stopped safely at the stale OS gate,
before AIDE evidence inspection. It did not execute K42, create its record, run
`aide --check`, modify AIDE databases/policy, or modify host configuration. This
does not establish that the target is absent or that current anchors match:
those checks were not reached. At that WP4B stage, authorization was
documentation-only reconciliation; renewed host preflight/execution required operator direction. WP5 supplies no
host authorization.

## Independently observed sandbox facts
Context: **CODEX SANDBOX CONTEXT**. Collector: Codex during initial discovery
on 2026-09-22; exact collection timestamps were not captured.

| Command/source | Observation |
| --- | --- |
| `cat /etc/os-release` | Ubuntu 26.04.1 LTS |
| `uname -r` | `7.0.0-31-generic` |
| `ps -p 1 -o comm=` | `codex` |
| `findmnt -no TARGET,FSTYPE,OPTIONS /` | Root exposed as ext4, read-only, nosuid, nodev |
| `id` | `forgeadmin`, UID 1001; this does not establish host context |

The initial OS discrepancy prompted a stop in host reconnaissance. The operator
subsequently classified these observations as sandbox observations. WP4B host
reconciliation independently supplied matching OS/kernel values; matching values
did not prove that the earlier commands ran on the host. CODEX SANDBOX CONTEXT
and both FORGE HOST CONTEXT variants remain distinct. PID 1, mount behavior,
permissions, filesystem visibility, and other sandbox observations must not be
reclassified as host facts. No host upgrade or remediation is inferred from them.

## Repository observations and limits
Context: CODEX SANDBOX CONTEXT. Initial discovery found a non-bare Git repository
on `master`, no commits or tracked files, and empty `docs/`, `evidence/`,
`scripts/`, and `tests/` directories. `.agents/` and `.codex/` were empty and
exposed read-only. Work Package 2 creates the governance files and reserved layout.

AIDE paths have not been inspected by Codex. Their readability, current contents,
and current hashes are unknown to Codex. No permission denial or independent
anchor verification is claimed. Host service, network, authentication, firewall,
AppArmor, and recovery state remain unverified. Inaccessible state is not failure.

## K42 reconciliation supplied 2026-09-25

Source: operator's WP5 instruction, historical K42 reconciliation. Collector:
operator. Collection date: 2026-09-25; exact collection time and command/method
not supplied. Execution context: **FORGE PRIVILEGED HOST CONTEXT**, explicitly
supplied by the operator. Verification status: operator-observed host evidence,
transcribed by Codex in CODEX SANDBOX CONTEXT on 2026-09-25; no independent Codex
host inspection or hash calculation. This is a provenance note, not a new closure
record. The earlier WP2/WP4B uncertainty is retained as historical context.

Observed file: `/var/lib/aide/trusted-history/f117k42-evidence-closure.txt`.

| Supplied observation | Value |
| --- | --- |
| Owner/group | root:root |
| Mode / links / size | 0600 / one link / 1562 bytes |
| Birth and modification time | 2026-09-22 20:17:04 UTC |
| File SHA256 | `34e01052913d25e54442aff676650429d1afe47acf77e39bf1d28beebad2fe88` |
| Historical determination in record | PASS |
| Recorded trusted aide.db SHA256 | `3c63b0d1bca62c4cc0472239962fbeef84979842207cee5bbd9ebcd22f39b18f` |
| Recorded candidate aide.db.new SHA256 | `3c63b0d1bca62c4cc0472239962fbeef84979842207cee5bbd9ebcd22f39b18f` |
| Recorded policy SHA256 | `72e121a5151844906acdfb2b12a7201d4a9ec382fc7db39b7317e064f14a4407` |
| Recorded K41 evidence SHA256 | `32ba78267a8a980b6c2067ba98038446e807acad1b1d748241ba0ebe3646b05f` |

All digests above are operator-supplied. The four recorded anchors are contents
reported from the historical record, not newly measured live source hashes.
File metadata does not prove authorship. The operator reports that the historical
record is not byte-format-compatible with the currently committed
`close_f117k42.py` `render()` output. Current-writer provenance is NOT established;
the supplied format evidence indicates that writer did not generate that exact
September 22 record. Actual creator and creation procedure remain unknown.

K42 record existence is no longer unknown as of this supplied observation.
Preserve the existing record: do not regenerate, replace or overwrite it. The
historical PASS and anchor equality do not establish current live AIDE cleanliness,
authorize a trust transition, or establish current source state. Candidate lifecycle
remains deferred. The earlier anchor manifest remains unchanged as a historical
record with its original collection/provenance limitations.
