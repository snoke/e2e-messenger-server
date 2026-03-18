# Crypto Overview

## Goals
- Server never sees plaintext secret key material.
- Client holds secrets in RAM only.
- Clear separation between live transport and storage encryption.

## Cryptographic Domains
- **MLS**: live transport encryption for realtime messages and signals.
- **MLS Key Agreement**: X‑Wing (X25519 + ML‑KEM‑768) for post-quantum key exchange.
- **CHK**: storage/history encryption for messages at rest.
- **Vault / UVK**: protects user-bound key material.

## Access Semantics
- `invite != access`
- `accept = access + key delivery`
- Pending members cannot fetch history keys.

## High-Level Key Flow

```mermaid
flowchart TD
  UVK[User Vault Key] -->|wraps| UserKey[User Key (ECDH)]
  UserKey -->|wraps| CHK[Conversation History Key]
  CHK -->|encrypts| History[Stored Messages]
  MLS[MLS Epoch Keys] -->|encrypts| Live[Live Transport]
```

## Server Visibility
- Sees only wrapped keys and ciphertext.
- Never sees plaintext CHK, MLS state, or UVK.
- Server is not provided with user key or CHK material and therefore cannot unwrap or decrypt them.

## Related
- Key lifecycle: [`docs/crypto/lifecycle-matrix.md`](lifecycle-matrix.md)
- CHK: [`docs/crypto/chk.md`](chk.md)
- Wrapping: [`docs/crypto/wrapping.md`](wrapping.md)
