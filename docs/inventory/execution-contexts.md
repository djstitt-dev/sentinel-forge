# Execution contexts and initial observations

Recorded during Work Package 2 on 2026-09-22. This is a documentation date, not
the original collection time of operator evidence.

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

## Operator-observed host facts
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
| Underlying OS, previously observed from host shell | Ubuntu 24.04.4 |
| AIDE version | 0.19.2 |

These limited facts were explicitly supplied for governance documentation. They
are not a raw host inventory or proof of current security-control effectiveness.

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
subsequently classified these observations as sandbox observations. No host OS
upgrade, inconsistency, or remediation is inferred from them.

## Repository observations and limits
Context: CODEX SANDBOX CONTEXT. Initial discovery found a non-bare Git repository
on `master`, no commits or tracked files, and empty `docs/`, `evidence/`,
`scripts/`, and `tests/` directories. `.agents/` and `.codex/` were empty and
exposed read-only. Work Package 2 creates the governance files and reserved layout.

AIDE paths have not been inspected by Codex. Their readability, current contents,
and current hashes are unknown to Codex. No permission denial or independent
anchor verification is claimed. Host service, network, authentication, firewall,
AppArmor, and recovery state remain unverified. Inaccessible state is not failure.
