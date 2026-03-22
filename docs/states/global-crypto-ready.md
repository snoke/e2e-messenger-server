# Global Crypto Ready

Global readiness is the **login/vault** state, not conversation-specific. It gates access to protected UI areas.

## Definition
A user is global-crypto-ready when all are true:
- Vault unlocked
- User key available and persisted
- Device registered

## Why It Exists
- Prevents users from entering protected UI when key material is missing.
- Ensures contact and chat flows can derive keys immediately.

## Where It Is Enforced
- [`frontend/src/app/messaging/sessionGate.ts`](../../frontend/src/app/messaging/sessionGate.ts)
- Gating applied in routing and UI shells.

## Logs
The frontend emits a `[crypto_ready]` log when the state becomes ready.

## Related
- Conversation readiness: [`docs/states/conversation-crypto-ready.md`](conversation-crypto-ready.md)
- Auth flows: [`docs/workflows/auth-password.md`](../workflows/auth-password.md), [`docs/workflows/auth-identity.md`](../workflows/auth-identity.md), and [`docs/workflows/auth-webauthn.md`](../workflows/auth-webauthn.md)
