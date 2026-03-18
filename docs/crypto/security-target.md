# Security Architecture (Current State → Target Architecture)

Status: **Binding contract (v5)**  
This document is the authoritative security architecture for the system.  
It replaces previous security documents and defines **binding rules**, **security invariants**, **explicit non-goals**, and **implementation constraints**.

This specification eliminates architectural ambiguity and prevents design drift.

---

# 1) Core Architectural Principle

**Backend = distribution**  
**Client = decryption capability**

The backend stores and distributes encrypted data only.  
The backend never gains plaintext access to secret key material.

All secret key material is decrypted exclusively on client devices.

Server-side storage contains only:

- ciphertext
- wrapped keys
- metadata
- public keys

This model enables:

- zero-knowledge storage
- secure multi-device access
- minimal trust assumptions toward the backend

---

# 2) Cryptographic Domains (Strict Separation)

The architecture enforces strict separation between **messaging security** and **storage security**.

These domains must never share root keys.

---

## 2.1 Messaging Domain (Device-Scoped)

```
Device Keys
     ↓
MLS Messaging
```

Properties:

- Each device is an independent MLS member.
- Device keys are **non-exportable**.
- Devices join messaging groups through standard MLS flows.
- Messaging group state is **device-local**.
- MLS uses **X‑Wing (X25519 + ML‑KEM‑768)** for post‑quantum key agreement.
- **MLS private state is never restored** from the backend.
- **Chat history is restored via CHK** (storage domain), not via MLS state.

Messaging security is therefore **device-centric** for live transport.

### Note on History
Conversation history is **not** restored from MLS state. It is restored via **CHK** in the storage domain.

Messaging key hierarchies must never be merged with storage key hierarchies.

---

## 2.2 Storage Domain (User-Scoped)

```
User Vault Key (UVK)
      ↓
   File Keys
      ↓
Encrypted Files
```

Properties:

- Files belong to the **user**, not to individual devices.
- Any authorized device that can unwrap the UVK can access file keys.
- The backend stores only ciphertext and wrapped keys.

Storage security is therefore **user-centric**.

---

# 3) Key Hierarchy (Binding)

The system uses a layered key hierarchy.

Each layer has a strictly defined purpose.

---

## 3.1 Device Keys

Device-specific cryptographic keys.

Usage:

- authentication proofs
- digital signatures
- device identity
- MLS membership
- MLS KeyPackages
- WebAuthn (passkey) authentication with PRF-based UVK unwrap

Properties:

- device-specific
- non-exportable
- stored locally only
- private components never leave the device
- public components stored server-side

Examples:

- identity keypair
- MLS init keys
- MLS KeyPackages
- WebAuthn credentials (authenticator-bound)

---

## 3.2 User Vault Key (UVK)

The **User Vault Key** is the root key of the storage domain.

Properties:

- randomly generated symmetric key
- exactly one root key per user
- 32 bytes
- generated from a cryptographically secure random generator (CSPRNG)
- never leaves the client unencrypted
- stored server-side only in wrapped form

Usage:

- wrapping file keys
- wrapping user-scoped encrypted application secrets
- potential future storage backup secrets

The UVK is **not**:

- an authentication key
- a signature key
- a password-derived key
- a messaging key

---

## 3.3 File Keys

Each file receives its own encryption key.

Structure:

```
file_key
   ↓
file encryption
```

Properties:

- randomly generated
- unique per file
- 32 bytes
- wrapped with the UVK
- stored server-side only as ciphertext

---

# 4) Password & Recovery (KEK-Only)

Password and Recovery Key are **not root keys**.

They exist only to unlock the UVK.

```
Password / Recovery Key
        ↓
   Key Derivation
        ↓
         KEK
        ↓
   User Vault Key
        ↓
      File Keys
        ↓
   Encrypted Files
```

Consequences:

- password changes only update the UVK wrapper
- file encryption does not change during password rotation
- recovery restores UVK access, not device keys

---

## 4.1 Password Key Derivation

Algorithm: **Argon2id**

Version 1 parameters:

- memory: 64 MB
- iterations: 3
- parallelism: 1
- salt: 16–32 bytes randomly generated per user

Stored parameters:

- `password_kdf_salt`
- `password_kdf_memory`
- `password_kdf_iterations`
- `password_kdf_parallelism`
- `kdf_version`

Derived output:

```
password_kek (32 bytes)
```

---

## 4.2 Recovery Key

Recovery Key properties:

- 32 bytes of cryptographically secure randomness
- printable representation (base32 or mnemonic)
- stored only by the user

Recovery KEK derivation:

```
recovery_key
     ↓
 HKDF (SHA-256, no salt)
     ↓
 recovery_kek
```

Recovery restores **only UVK access**, not device private keys.

---

# 5) Cryptographic Algorithms (Binding)

## 5.1 Password KDF

Algorithm: **Argon2id**

Used exclusively for deriving password KEKs.

---

## 5.2 Data Encryption

File encryption:

- **ChaCha20-Poly1305**
- 256-bit key
- 96-bit nonce

Nonce requirements:

- nonce must be unique per encryption key
- nonce reuse is forbidden
- nonce must never be reused, even for re-uploads of the same file

Identity profile encryption:

- **AES-GCM**

---

# 6) Server-Side Data Model (Target)

The backend stores only ciphertext and public information.

---

## 6.1 user_key_vault

Stores wrapped UVK material.

Fields:

- `user_id`
- `vault_version`
- `wrapped_uvk_by_password`
- `password_kdf_salt`
- `password_kdf_memory`
- `password_kdf_iterations`
- `password_kdf_parallelism`
- `wrapped_uvk_by_recovery`
- `created_at`
- `updated_at`

---

## 6.2 device_registry

Stores registered devices.

Fields:

- `device_id`
- `user_id`
- `identity_public_key`
- `device_label`
- `created_at`
- `last_seen_at`
- `revoked_at`

---

## 6.3 device_key_packages

Stores MLS KeyPackages.

Fields:

- `device_id`
- `key_package`
- `consumed_at`
- `expires_at`

---

## 6.4 file_objects

Stores encrypted file objects.

Fields:

- `file_id`
- `owner_user_id`
- `ciphertext_ref`
- `nonce_seed`
- `size`
- `created_at`

---

## 6.5 file_key_records

Stores wrapped file keys.

Fields:

- `file_id`
- `wrapped_file_key`
- `wrap_algorithm`
- `created_at`

---

# 7) Metadata Policy (Binding)

Plaintext metadata:

- `object_id`
- `owner_user_id`
- `size`
- `filename` (allowed plaintext for UI indexing in v1)
- `nonce_seed` (required to derive nonces; not secret)
- `created_at`

Encrypted metadata:

- description
- tags
- all user content metadata

---

# 8) Operational Flows (Target)

## 8.1 Signup

1. Device generates identity key locally.
2. Client generates UVK.
3. Client generates Recovery Key.
4. Derive password KEK (Argon2id).
5. Wrap UVK by password KEK.
6. Wrap UVK by recovery KEK.
7. Publish device KeyPackages.
8. Store vault payload on server.

Server receives only:

- wrapped UVK
- public keys
- key packages

---

## 8.2 Login (New Device)

1. User authenticates.
2. Server returns wrapped UVK + KDF params.
3. Client derives password KEK.
4. UVK unwrapped locally.
5. Device generates new device keys.
6. Device publishes new KeyPackages.
7. Fetch wrapped file keys.
8. Unwrap file keys with UVK.

Result:

- access to existing encrypted files
- participation in new messaging sessions

---

## 8.3 Recovery

1. User provides Recovery Key.
2. Recovery KEK derived.
3. UVK unwrapped locally.
4. New password set.
5. UVK re-wrapped with new password KEK.

---

## 8.4 Password Change

1. Unwrap UVK with current password KEK.
2. Derive new password KEK.
3. Re-wrap UVK.
4. Store updated wrapper.

---

## 8.5 File Upload

1. Generate `file_key`.
2. Encrypt file locally (ChaCha20-Poly1305).
3. Wrap `file_key` with UVK.
4. Upload ciphertext + wrapped key.

---

## 8.6 Device Revocation

1. Mark device revoked.
2. Block future sessions.
3. Rotate MLS group membership if necessary.

Revocation prevents **future access**, not access to already cached secrets.

---

# 9) Security Invariants (Binding)

1. Backend never stores plaintext secrets.
2. UVK never leaves the client unencrypted.
3. Password/recovery keys wrap only the UVK.
4. File keys are wrapped only by the UVK.
5. Device keys are device-scoped and non-exportable.
6. Messaging and storage key hierarchies remain separate.
7. Revocation stops future access only.
8. localStorage must never contain plaintext root keys or file keys.
9. UVK is the **only storage root key**.

---

# 10) Explicit Non-Goals / Forbidden Choices

The following architectural decisions are forbidden unless explicitly approved in a future revision:

1. Using device or identity keys as storage roots.
2. Wrapping file keys directly with password-derived keys.
3. Using password-derived keys as data encryption roots.
4. Merging messaging and storage key hierarchies.
5. Storing private keys, UVK, or file keys in plaintext on the backend.
6. Restoring MLS private state from backend storage.
7. Requiring device-to-device transfer for normal multi-device access.

---

# 11) Migration (Binding for v1)

Current model:

```
file_key
   ↓
KeyGraph project key
   ↓
localStorage
```

Problems:

- root key stored in plaintext in browser storage
- device-bound storage access
- single point of decryption

Target model:

```
file_key
   ↓
UVK
   ↓
wrapped_file_key
   ↓
server storage
```

Result:

- storage becomes user-scoped
- multi-device access becomes possible
- no root key stored in localStorage

---

# 12) Version 1 Decisions (Binding)

1. Argon2id is the password KDF.
2. File key rotation is manual only.
3. Metadata plaintext list is minimal and fixed.
4. Hard migration is allowed in development environments.
5. The existing KeyGraph project key is replaced by UVK wrapping.

---

# 13) Vision (Non-Binding, Not Part of v1)

**Post-Quantum (Kyber KEM) – Possible Future Extensions**

Optional future possibilities:

1. UVK transfer to new devices via Kyber KEM.
2. File-sharing user → user using Kyber-wrapped file keys.

These ideas are exploratory and **not part of this architecture contract**.

---

# 14) Client Security Assumption

Client compromise (XSS, malware, or device takeover) is considered a **full client compromise**.

In such a scenario:

- decrypted keys may be exposed
- the backend architecture cannot prevent key extraction
- security relies on protecting the client environment

This architecture protects **data at rest and in transit**, but cannot protect against a fully compromised client.

---

# 15) Final Summary

The architecture is based on three rules:

1. strict separation of messaging and storage domains
2. UVK as the single root of storage encryption
3. backend stores ciphertext only

This enables:

- secure multi-device access
- zero-knowledge storage
- a clear and enforceable key hierarchy
- minimized attack surface

---

# 16) Implementation Plan (Progress Tracker)

This plan tracks implementation progress against this contract.

1. DONE — Add backend schema for `user_key_vault` and `file_key_records`.
2. DONE — Add gateway commands for vault init/fetch/update and file_key wrap/fetch.
3. DONE — Implement UVK generation + KEK derivation on signup.
4. DONE — Implement vault fetch + UVK unwrap on login (new device).
5. DONE — Replace KeyGraph localStorage root with UVK‑wrapped file keys.
6. DONE — Update upload/download flows to use wrapped file keys from server.
7. DONE — Implement recovery flow (unwrap UVK via recovery key, rewrap by password).
8. DONE — Implement password change flow (rewrap UVK only).
9. DONE — Add migration/reset tooling (hard cut in dev as allowed).
10. DONE — Add invariant checks + telemetry (missing vault, missing keys, nonce misuse).
