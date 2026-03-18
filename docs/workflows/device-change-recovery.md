# Device Change / Recovery

## New Device (Password)
1. User logs in with password.
2. Vault fetch + UVK unwrap.
3. Device wrap is registered.
4. Global crypto readiness becomes true.

## New Device (Identity)
1. User logs in via identity.
2. Device wrap missing → vault locked.
3. User unlocks via recovery or approval.
4. Device wrap is registered.

## New Device (WebAuthn)
1. User logs in via WebAuthn on the new device (new credential).
2. Server returns PRF salt for the credential.
3. Client unwraps UVK locally and completes bootstrap.
4. Device wrap is registered for future device unlocks.

## Recovery Key Flow
1. User provides recovery key.
2. Client unwraps UVK.
3. Device wrap is registered for future logins.

Related:
- [`docs/crypto/security-current.md`](../crypto/security-current.md)
- [`docs/states/global-crypto-ready.md`](../states/global-crypto-ready.md)
