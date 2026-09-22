# F1.17K42 closure procedure proposal

Status: Work Package 4A preparation committed; WP4B host preflight subsequently
stopped at the stale OS gate. Current scope is approved repository-only
reconciliation finalization and commit; stop after commit and verification,
without host preflight or execution. This is a procedure
specification, not the closure record. No host AIDE paths were accessed by Codex
while preparing or testing it.

## WP4B reconciled preflight expectations
The operator's FORGE PRIVILEGED HOST CONTEXT reconciliation on 2026-09-22
supersedes the earlier Ubuntu 24.04.4 assertion with Ubuntu 26.04.1 LTS,
kernel `7.0.0-31-generic`, x86-64. Preserve both observations and their provenance
in the [context inventory](../inventory/execution-contexts.md). The stopped
preflight reached no AIDE evidence checks and is not a successful preflight.

The prior preflight command was supplied in conversation, not stored as a
repository script. Its expected OS gate must be Ubuntu 26.04.1 LTS:
`ID=ubuntu`, `VERSION_ID=26.04`, `VERSION_CODENAME=resolute`, and
`PRETTY_NAME="Ubuntu 26.04.1 LTS"`. Do not retain Ubuntu 24.04.4 as a current
acceptance value or relax the gate to accept any Ubuntu version. Unexpected
identity still requires a stop and operator review. Matching sandbox OS/kernel
values do not establish host context.

The approved writer remains unchanged: SHA256
`23c40f541e9d23c88c29118d16e517af689bcf44bd1f5839b402ac4d0d9356a9`, originally
approved at commit `b2a7c57777c9eaf6115c77299341006ec46d6af4`. It has no OS
gate; that gate belongs to operator preflight. The remaining preflight checks
(exact approved HEAD, clean tree, script hash, Python, target absence, source
metadata, anchor hashes, database equality, and concurrent AIDE process screen)
remain required. A future reconciliation commit will change HEAD; obtain the
operator's explicit approved commit before issuing a revised host preflight,
rather than silently relaxing the HEAD check. This update authorizes no host
commands and changes no anchor, database, temporal-boundary, or lifecycle semantics.

## Purpose and temporal boundary
Close the previously validated F1.17 evidence chain, using the operator-verified
anchors in the [manifest](../../evidence/manifests/aide-anchors.json). Original
collection times and user/privileged host context remain unspecified. The
historical candidate equality assertion is distinguished from the byte comparison
that the proposed procedure will make at its own execution time.

Software and filesystem changes occurred after K41, including Codex setup and
supporting packages/files. They are outside the F1.17 acceptance state. K42 must
not claim that the current live filesystem is AIDE-clean, perform a new AIDE
check, establish a baseline, promote a candidate, authorize changes to either
database, or normalize post-K41 changes. Candidate lifecycle remains deferred.

## Preconditions and operator approval gate
The operator must separately authorize this exact procedure and establish actual
FORGE PRIVILEGED HOST CONTEXT. A root UID or matching hostname alone is not proof
of host context. The context command argument is an explicit operator attestation,
not automated context detection.

Before execution, the operator must review the script and ensure its bytes remain
unchanged through execution. Do not run a concurrently editable script as root.
Ensure a quiescent window with no concurrent AIDE runs, database/policy/history
writers, or directory changes. This proposal does not authorize stopping services
or changing permissions to obtain that window. If the preconditions cannot be
met, stop for a separate approved plan.

The host must already provide Python 3 and Linux support for the file operations
used. No installation is included. All ancestor directories must be real,
root-owned directories without group/world write permission. Sources must be
regular, root-owned, singly linked files without group/world write permission.
Symlinks are refused. These are fail-closed preconditions, not permission-repair
instructions. Directory existence, source accessibility, and host compatibility
are unverified until separately authorized execution.

## Fixed inputs and output
The script pins these SHA256 values; it takes no path or hash override arguments:

| Source | Expected SHA256 |
| --- | --- |
| `/var/lib/aide/aide.db` | `3c63b0d1bca62c4cc0472239962fbeef84979842207cee5bbd9ebcd22f39b18f` |
| `/etc/aide/aide.conf.d/90_sentinel_forge_local` | `72e121a5151844906acdfb2b12a7201d4a9ec382fc7db39b7317e064f14a4407` |
| `/var/lib/aide/trusted-history/f117k41-final-post-promotion-verification.txt` | `32ba78267a8a980b6c2067ba98038446e807acad1b1d748241ba0ebe3646b05f` |

`/var/lib/aide/aide.db.new` must compare byte-for-byte equal to the trusted
database. Its execution-time SHA256 is calculated and recorded too.
The sole created file is:
`/var/lib/aide/trusted-history/f117k42-evidence-closure.txt`.

## Algorithm and effects
1. Require explicit execution/context arguments and effective UID 0 before host
   path access. Open and pin safe parent directories without following symlinks.
2. Refuse an existing target, including a dangling symlink. Read pinned input
   files with `O_NOATIME`; unsupported/denied operations stop the procedure.
3. Validate all three pinned hashes, hash the candidate, and compare databases
   byte-for-byte. Check source identities and metadata for change. Repeat the
   validation immediately before creation. Any detected mismatch here means no
   K42 creation.
4. Assemble deterministic UTF-8 content with UTC execution time, explicit context,
   anchor provenance, all four validated hashes, comparison result, temporal
   boundary, and candidate-lifecycle deferral. The execution timestamp is the
   closure event time, not a retroactive F1.17 acceptance timestamp.
5. Exclusively create the fixed target with mode 0600 and umask 077. Set ownership
   to root:root and mode to 0600 on that new descriptor only. Write the record,
   then fsync the file and parent directory. No temporary output or lock file is
   created. A concurrently created target is never overwritten.
6. Revalidate source evidence, then verify target ownership, exact mode, regular
   file type, link count, size, path identity, and SHA256 against the prepared
   bytes. Reopen the safe directory chains to verify parent identity. Only then
   print successful root:root/0600 verification and the output SHA256; exit zero.

No AIDE executable is invoked. No input content, permissions, ownership, or
candidate lifecycle is changed. Intended filesystem effects are the one new
record, its metadata, and its parent directory's entry/timestamps. Reads request
no access-time update for evidence files and directory traversal. Ordinary OS
audit/logging and script/interpreter access metadata may still occur; this is not
a promise of zero incidental host activity. No logs are explicitly created by
the script; stdout/stderr remain on the operator's terminal.

## Proposed command — not executed
Only after separate approval, from an already authorized root shell on the actual
Forge host, execute the reviewed script at its approved location:

```sh
python3 -I -B /home/forgeadmin/Project-Sentinel-Forge/scripts/changes/close_f117k42.py --execute-host --context 'FORGE PRIVILEGED HOST CONTEXT'
```

`-I` isolates Python from user environment/module search settings; `-B` suppresses
bytecode files. No privilege-escalation command is part of this proposal.
There is no force, overwrite, promotion, or repair option. Root execution was not
tested on the host and is not authorized by preparing this command.

## Failure, recovery, and evidence preservation
Before creation, failure leaves K42 absent unless it already existed or another
writer created it. Existing records are preserved even if apparently valid.
After exclusive creation, any error, interruption, or failed verification can
leave an empty, partial, or complete record. The script never deletes, renames,
overwrites, or silently repairs it. A rerun refuses that record. Nonzero exit or
missing success output is not evidence of successful closure.

On any such failure, stop, preserve the record and terminal result, and have the
operator authorize inspection of its bytes, hash, ownership, mode, provenance,
and the original anchors. Do not automatically roll back by deleting evidence.
Any quarantine, corrective evidence, removal, or rerun requires an explicit
operator-approved recovery plan preserving the original record and provenance.
There is no automatic rollback. A power loss can leave uncertain durability;
successful fsync and verification are the normal completion criteria, not proof
against all storage failures.

The script does not claim its own post-write checks inside the record, since those
occur after writing; their result and the record digest are printed on success.
No second receipt file is written. The operator can authorize preservation of
terminal output separately.

Race detection is defense in depth, not a coherent filesystem snapshot or a lock
against another root actor. A detected change after creation retains K42 and
reports failure; the requirement to abort without creation applies to mismatches
detected in preflight. A quiescent window is required to close that race boundary.

## Offline validation
Run from the repository in CODEX SANDBOX CONTEXT:

```sh
python3 -B -m unittest discover -s tests -p 'test_*.py' -v
git diff --check
```

Tests import the inert script and call the shared engine with synthetic fixtures
under `tests/.k42-test-*/`. They supply fixture hashes, sandbox context, and the
current user's ownership, never host AIDE paths. Fixtures are removed after each
test; this cleanup concerns synthetic test data, never host evidence. No CLI
fixture override can redirect production execution. Tests of CLI refusal mock
host directory access to fail if reached. Offline success does not verify real
host evidence, root ownership enforcement on the host, or host readiness.
