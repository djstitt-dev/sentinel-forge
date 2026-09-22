# Project Sentinel Forge

## Authority and scope
The operator is the sole approval authority for security-sensitive,
architecture-changing, destructive, privileged, and trust-boundary actions.
Work only within the explicitly authorized phase and scope. A plan, repository
commit, or successful test is not deployment approval.

Authorization is granted by the operator for a specific work package or task.
Never infer authorization from a prior work package, prior session, Git state,
AGENTS.md, or a successful test. Authorization expires at the boundary defined
by the operator. Before beginning a new phase, identify the currently authorized
scope. When authorization is unclear, stop before taking an approval-required
action. Permanent governance rules in AGENTS.md remain applicable across all
work packages.

## Execution and evidence contexts
Every observation and evidence record must identify its execution context:

- **CODEX SANDBOX CONTEXT**: Codex commands may execute in an isolated sandbox.
  Its OS, processes, mounts, kernel-visible state, permissions, and other
  properties may differ from the underlying Forge host.
- **FORGE USER HOST CONTEXT**: commands explicitly executed on the actual Forge
  host as `forgeadmin`, without privilege escalation.
- **FORGE PRIVILEGED HOST CONTEXT**: commands explicitly executed on the actual
  Forge host using operator-approved privilege escalation.

Never infer underlying Forge host state solely from sandbox observations.
Never silently combine evidence from different contexts. The account name alone
does not establish context. Record collector, source, time if known, command if
known, and verification status. If a supplied host observation does not specify
user versus privileged context, record that distinction as unknown; do not guess.
Operator-verified host evidence is distinct from independently verified Codex
evidence. Codex may claim independent host verification only after actually
performing it in an established, appropriate host context.

## Discovery and unexplained state
Observe before modifying. During discovery, use only non-privileged, read-only
operations. Do not use sudo or create closure records. Treat inaccessible state
as unknown, not as failure. Distinguish observed facts, operator-supplied facts,
assumptions, unknowns, and proposed actions.
Confirm context before interpreting host observations. Stop affected work and
report unexplained identity, integrity, or state; do not normalize or repair it
autonomously.

## Security and evidence
Never weaken a security control to make a task work. Existing AIDE configuration,
databases, and historical evidence are protected evidence. Never autonomously
initialize, replace, promote, delete, or alter an AIDE trust anchor. Do not infer
trust from a filename or candidate/trusted equality alone. Preserve provenance
and distinguish supplied hashes from independently observed hashes.
Do not put secrets, credentials, private keys, authentication artifacts, raw
sensitive host inventories, or trusted AIDE databases into Git. Ignore rules are
only a secondary safeguard; review content before any future staging or commit.

## Change control
Before an approval-required action, present its exact scope, affected resources,
expected effects, verification, stop conditions, and rollback. Obtain explicit
operator approval before execution. Preserve rollback paths; prefer deterministic,
testable, reversible changes. Represent system configuration as code where practical.
Keep observed state, proposed desired state, and verified applied state distinct.

Privilege escalation, including sudo, requires explicit operator approval.
Changes to AIDE, packages, services, networking, authentication, firewall,
AppArmor, SSH, users, groups, permissions outside the repository, or any other
host security state require explicit operator approval for the specific scope.
Repository authorization alone does not authorize changes outside the repository.
Creating evidence closure records, including F1.17K42, requires separate operator
approval after evidence review. Approval does not waive the enduring AIDE trust,
evidence preservation, verification, or stop-condition rules above.

## Verification and reporting
Document command side effects, including logs and output files. Prefer offline
tests before approved host execution. Never claim success without verification.
Report changed files, validation, context, remaining unknowns, and deviations
from the approved plan. Do not overwrite historical evidence or invent missing
closure records. Read the evidence rules in `evidence/README.md` before adding
evidence and the context definitions in `docs/inventory/execution-contexts.md`.
