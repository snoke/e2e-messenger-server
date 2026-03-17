# Keys & Vault

This document explains the key hierarchy and how vault unlock works.

## Key Types
- **UVK (User Vault Key)**: root for user-bound storage.
- **User Key (ECDH-P256)**: wraps CHK for a specific user.
- **Device Key / Device Vault**: device-bound wrapping for UVK.
- **CHK (Conversation History Key)**: per-conversation storage key.

## Storage Rules
- Server stores only wrapped keys and metadata.
- Client stores plaintext keys in RAM only.

## Vault Unlock Sequence (Password)
1. Client authenticates and receives token.
2. Client fetches vault via `user_vault_fetch`.
3. UVK is unwrapped locally (password KDF).
4. User key is generated or loaded.
5. User key is persisted via `user_vault_update_user_key`.
6. Device wrap is registered via `user_device_vault_register`.

## Vault Unlock Sequence (Identity)
1. Client authenticates via device identity.
2. Client fetches device vault via `user_device_vault_fetch`.
3. UVK is unwrapped using the device key.
4. If device wrap is missing, vault remains locked.

## Persistence Locations
- UVK plaintext: RAM only.
- User key private: RAM only.
- User key public: server and client cache.
- Device key: IndexedDB CryptoKey handle.

## Related
- CHK: `docs/crypto/chk.md`
- Wrapping: `docs/crypto/wrapping.md`
- Global crypto readiness: `docs/states/global-crypto-ready.md`
