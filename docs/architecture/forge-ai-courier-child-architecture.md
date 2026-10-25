# Forge Standalone AI + Courier Child Architecture

Date: 2026-09-26

## Operator objective
Forge accepts operator commands, reasons through an interchangeable local-model provider, proposes bounded actions, executes only policy-authorized local tools, verifies results, and returns a response/fix record.

Courier can prepare a child bootstrap, deliver it using an explicitly invoked OpenSSH bootstrap adapter, receive a one-time authenticated callback, verify the intended child/enrollment/challenge, and then establish a relationship-specific AES-256-GCM protected Courier session. Bootstrap SSH is not the Courier steady-state trust mechanism.

## Trust sequence
1. Operator defines exact child identity/endpoint and approves bootstrap.
2. Forge creates target-bound enrollment/challenge and child bootstrap artifact.
3. OpenSSH adapter performs strict-host-key checked bootstrap only when explicitly invoked.
4. Child installs/stages Courier and returns authenticated enrollment proof.
5. Callback possession alone grants no trust.
6. Forge verifies enrollment ID, child identity, challenge, proof signer/key reference and revocation state.
7. Forge activates the pairwise relationship only after operator/policy authorization.
8. A unique 256-bit relationship key reference is provisioned through the approved credential boundary.
9. Courier messages use AES-256-GCM with relationship/session/operation/artifact/sequence associated data.
10. Forge displays connection state; child receives only a minimal connection notification.

## Non-negotiable invariants
- no fleet-wide symmetric key;
- no trust from IP address, hostname, SSH success or callback arrival alone;
- AES-GCM nonce uniqueness per key;
- authenticated encryption failure is terminal for that message;
- replay/sequence validation remains mandatory in addition to AEAD;
- revocation/rotation immediately blocks stale sessions;
- AI model output is never authority;
- AI cannot bypass operator/security gates;
- command execution is allowlisted and evidence-producing;
- unknown effect blocks blind retry;
- child bootstrap is target-bound and single-use;
- child notification contains no topology, credential, peer-list or sensitive Forge state.

## Completion states
AI_ENGINE_IMPLEMENTED is distinct from LOCAL_MODEL_OPERATIONAL.
CHILD_BOOTSTRAP_IMPLEMENTED is distinct from SSH_BOOTSTRAP_EXECUTED.
AES256_GCM_PROVIDER_IMPLEMENTED is distinct from PRODUCTION_KEY_PROVISIONED.
CALLBACK_HANDLER_IMPLEMENTED is distinct from LIVE_CALLBACK_OBSERVED.
VISUAL_MONITOR_IMPLEMENTED is distinct from LIVE_CHILD_CONNECTED.
