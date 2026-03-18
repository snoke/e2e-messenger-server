# Key Matrix

| Key | Owner | Client Storage | Server Storage | Notes |
|---|---|---|---|---|
| UVK | User | RAM only | Wrapped | Root storage key |
| User Key (ECDH) | User | RAM only (private) | Public key | Wraps CHK |
| Device Key | Device | IndexedDB CryptoKey | Public key / wraps | Used for identity auth and UVK unwrap |
| WebAuthn Credential | Device authenticator | OS / hardware | Public key + metadata | Used for WebAuthn auth + PRF |
| Wrapped UVK (WebAuthn) | User | ❌ | Wrapped | Stored per credential in `user_webauthn_vaults` |
| CHK | Conversation | RAM only | Wrapped per member | History encryption |
| MLS State | Device | RAM only | None | Live transport only |

Notes:
- No plaintext secret key material is stored or processed on the server.
- Server sees ciphertext, public keys, and metadata only, and is not provided with key material to decrypt them.
