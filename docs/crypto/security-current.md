# Security Architecture (Current Implementation Snapshot, v6)

Status: **Current system documentation**
This document describes the **actual implementation** of auth, vault unlock, device keys, and storage encryption as of now.
It is not aspirational. Where something is partially implemented, it is explicitly marked.

Status Legend:
- `[Implemented]` = live in current system
- `[Planned]` = specified, not yet implemented

---

# 1) Core Principle (Implemented) [Implemented]

**Backend = distribution**  
**Client = decryption capability**

- Server stores encrypted blobs, wrapped keys, and metadata.
- Server never sees plaintext long‑lived secrets.
- Clients decrypt and unwrap locally.

---

# 2) Auth Workflow (Implemented) [Implemented]

## 2.1 Realtime Auth Model
- Websocket requires **initial auth handshake**.
- Supported pre‑auth commands:
  - `auth_login_request`
  - `auth_register_request`
  - `auth_identity_request`
- These return a **JWT token**.
- After successful pre‑auth, the gateway validates the token and emits `auth_ok` on the same connection.

### WebAuthn Auth (HTTP)
WebAuthn is **HTTP-based**, not a realtime pre‑auth command.

Endpoints:
- `POST /api/webauthn/register/begin`
- `POST /api/webauthn/register/finish`
- `POST /api/webauthn/login/begin`
- `POST /api/webauthn/login/finish`

These return the same JWT token and then follow the same vault bootstrap.

## 2.2 Token Handling (Client)
- Token is stored in **localStorage** (`auth_token`).
- On websocket reconnect, the client sends `auth` with the token.
- A connection is considered authenticated only after `auth_ok`.

## 2.3 Auth vs Vault Unlock (Implemented Separation)
- Authentication **does not imply** vault unlock.
- Vault unlock is handled by the **Vault Unlock Service** and depends on device‑bound or recovery factors.
- Result: a session can be **authenticated but vault_locked**.

---

# 3) Key Hierarchy (Implemented) [Implemented]

```
Device Keys (Identity, MLS)
      ↓
[Messaging Domain]

User Vault Key (UVK)          ← root of storage domain
      ↓
File Keys
      ↓
Encrypted Files
```

## 3.1 Device Keys (Implemented)
- Per‑device identity keypair (ECDSA P‑256, non‑exportable WebCrypto key).
- Stored in IndexedDB (device key store).
- Used for identity auth + MLS membership.

## 3.2 User Vault Key (UVK) (Implemented)
- 32‑byte random symmetric key generated on client.
- Root key for storage encryption.
- Never stored in plaintext on server.
- Active UVK is **RAM‑only** on client.

## 3.3 File Keys (Implemented)
- 32‑byte random key per file.
- Files encrypted client‑side (ChaCha20‑Poly1305).
- File key is wrapped by UVK and stored server‑side.

## 3.4 Device KEK (Implemented for device unlock)
- Dedicated device‑bound KEK (non‑exportable CryptoKey).
- Stored in IndexedDB (CryptoKey handle).
- Used **only** to unwrap `wrappedUvkForDevice`.
- **Must not** reuse identity key or secure‑store KEKs.
- If IndexedDB is cleared, device unlock is lost for that device.

## 3.5 WebAuthn Credential + PRF (Implemented)
- WebAuthn credential private keys live in the authenticator (OS / hardware).
- Client derives a PRF output from the authenticator to wrap/unwrap UVK.
- Server stores only the credential metadata and the **wrapped UVK** per credential.

---

# 4) Cryptographic Algorithms (Implemented) [Implemented]

- **Password KDF:** Argon2id (64MB, 3 iterations, parallelism 1)
- **Recovery KEK:** HKDF‑SHA256 (recovery key = 32 bytes random)
- **File Encryption:** ChaCha20‑Poly1305 (256‑bit key, 96‑bit nonce)
- **Profile Encryption:** AES‑GCM
- **MLS KEX:** X‑Wing (X25519 + ML‑KEM‑768) in `MLS_256_XWING_CHACHA20POLY1305_SHA512_MLDSA87`

Nonce rule (enforced):
- Nonce must be unique **per encryption key**.
- Never reuse nonce, even on re‑upload of the same file.

---

# 5) Persistence Locations (Current) [Implemented]

| Secret / Material | RAM | IndexedDB | localStorage | Server | Notes |
|---|---:|---:|---:|---:|---|
| UVK (active) | ✅ | ❌ | ❌ | ❌ | RAM‑only |
| Wrapped UVK (password) | ❌ | ❌ | ❌ | ✅ | `user_key_vault` |
| Wrapped UVK (recovery) | ❌ | ❌ | ❌ | ✅ | `user_key_vault` |
| Wrapped UVK (device) | ❌ | ❌ | ❌ | ✅ | `user_device_vault` |
| Wrapped UVK (webauthn) | ❌ | ❌ | ❌ | ✅ | `user_webauthn_vaults` |
| Device KEK (non‑exportable) | ❌ | ✅ | ❌ | ❌ | IndexedDB handle |
| Identity device keypair | ❌ | ✅ | ❌ | ❌ | IndexedDB handle |
| WebAuthn credential (public) | ❌ | ❌ | ❌ | ✅ | `user_webauthn_credentials` |
| PRF salt | ❌ | ❌ | ❌ | ✅ | `user_webauthn_vaults`, `user_webauthn_challenges` |
| Auth token | ❌ | ❌ | ✅ | ❌ | `auth_token` |
| File keys (wrapped) | ❌ | ❌ | ❌ | ✅ | `file_key_records` |
| Recovery Key (raw) | ✅ (signup only) | ❌ | ❌ | ❌ | one‑time display, not persisted |

---

# 6) Server‑Side Data Model (Current) [Implemented]

## 6.1 `user_key_vault`
- `user_id`
- `vault_version`
- `wrapped_uvk_by_password`
- `password_kdf_salt`
- `password_kdf_memory`
- `password_kdf_iterations`
- `password_kdf_parallelism`
- `wrapped_uvk_by_recovery`
- `created_at`, `updated_at`

## 6.2 `user_device_vault`
- `user_id`
- `device_id`
- `wrapped_uvk_for_device`
- `wrap_algorithm`
- `created_at`, `updated_at`

## 6.3 `device_registry` (identity keys)
- `device_id`
- `user_id`
- `identity_public_key`
- `device_label`
- `status` (`pending` | `trusted` | `revoked`)
- `created_at`, `last_seen_at`, `revoked_at`

## 6.4 `file_objects`
- `file_id`
- `owner_user_id`
- `ciphertext_ref`
- `nonce_seed`
- `size`
- `created_at`

## 6.5 `file_key_records`
- `file_id`
- `wrapped_file_key`
- `wrap_algorithm`
- `created_at`

## 6.6 `user_webauthn_credentials`
- `user_id`
- `credential_id`
- `credential_json`
- `created_at`, `updated_at`, `last_used_at`

## 6.7 `user_webauthn_vaults`
- `user_id`
- `credential_id`
- `wrapped_uvk`
- `wrap_alg`
- `prf_salt`
- `created_at`, `updated_at`

## 6.8 `user_webauthn_challenges`
- `user_id`
- `request_id`
- `type` (`register` | `login`)
- `payload`
- `prf_salt`
- `created_at`, `expires_at`

---

# 7) Auth + Vault Unlock Flows (Current) [Implemented]

## 7.0 Server-side Handling (Verification)
Server-side actions **only persist wrapped material** and do not decrypt user secrets.

Evidence (code):
- [`symfony/src/Plugins/UserVault/Application/Realtime/Action/UserVaultInitAction.php`](../../symfony/src/Plugins/UserVault/Application/Realtime/Action/UserVaultInitAction.php) stores `wrapped_uvk_*` and `wrapped_user_key_private`.
- [`symfony/src/Plugins/UserVault/Application/Realtime/Action/UserVaultUpdateUserKeyAction.php`](../../symfony/src/Plugins/UserVault/Application/Realtime/Action/UserVaultUpdateUserKeyAction.php) stores `wrapped_user_key_private`.
- [`symfony/src/Service/ConversationKeyService.php`](../../symfony/src/Service/ConversationKeyService.php) stores `wrapped_chk` only.

## 7.1 Signup (Password)
1. Client generates UVK + Recovery Key.
2. Ensure Device KEK exists (create if missing, IndexedDB).
3. Derive password KEK (Argon2id).
4. Wrap UVK by password + recovery.
5. Send `auth_register_request` (pre‑auth).
6. Store token in localStorage.
7. Call `user_vault_init` with wrapped UVK payload.
8. Mark vault authenticated + set active UVK in RAM.
9. Ensure user key exists (generate if missing) and persist via `user_vault_update_user_key`.
10. Wrap UVK with Device KEK and register via `user_device_vault_register`.
11. Show recovery key screen (one‑time display).

Note: `user_vault_init` requires an **authenticated realtime connection** (must have `auth_ok`).

## 7.2 Login (Password)
1. Send `auth_login_request`.
2. Store token.
3. Fetch `user_key_vault` via `user_vault_fetch`.
4. Derive password KEK and unwrap UVK locally.
5. Set UVK active in RAM.
6. Ensure Device KEK exists (create if missing, IndexedDB).
7. Ensure user key exists and is persisted (`user_vault_update_user_key` if missing).
8. Register device wrap if missing (`user_device_vault_register`).

## 7.3 Identity Login (Passwordless)
1. Send `auth_identity_request`.
2. Store token.
3. Attempt device unlock via `user_device_vault_fetch`.
4. If `wrapped_uvk_for_device` exists, unwrap with Device KEK (IndexedDB).
5. Ensure user key exists and is persisted (`user_vault_update_user_key` if missing).
   (This may trigger an internal `user_vault_fetch` for key material.)
6. If successful: UVK in RAM → `vault_unlocked`.
7. If missing/fails: `vault_locked` until recovery or pairing approval.

## 7.3.1 Browser Restart (Known Device)
1. Browser reopens → `auth_token` present.
2. Client reconnects → sends `auth` → receives `auth_ok`.
3. Client calls `user_device_vault_fetch`.
4. Server returns `wrapped_uvk_for_device` if device is registered.
5. Client unwraps using Device KEK from IndexedDB.
6. Ensure user key exists and is persisted (`user_vault_update_user_key` if missing).
7. UVK restored to RAM → `vault_unlocked`.

If Device KEK is missing or no device wrap exists, vault remains locked.

## 7.4 Signup (WebAuthn)
1. Client calls `POST /api/webauthn/register/begin`.
2. Server returns WebAuthn `publicKey` options + `prf_salt`.
3. Client calls `navigator.credentials.create`.
4. Client derives PRF output and wraps UVK locally.
5. Client sends credential + wrapped UVK to `POST /api/webauthn/register/finish`.
6. Server stores credential + wrapped UVK and returns token.
7. Client ensures user key material and registers device vault.
8. Global crypto readiness becomes true.

## 7.5 Login (WebAuthn)
1. Client calls `POST /api/webauthn/login/begin` (email).
2. Server returns `publicKey` options + `prf_salt` for a matching credential.
3. Client calls `navigator.credentials.get`.
4. Client derives PRF output and unwraps UVK locally.
5. If UVK unwrap fails, login is aborted and `login/finish` is **not** called.
6. Client calls `POST /api/webauthn/login/finish` with assertion.
7. Server returns token.
8. Client ensures user key material and registers device vault.

## 7.4 Recovery
1. Fetch `user_key_vault`.
2. Derive recovery KEK (HKDF).
3. Unwrap UVK.
4. Rewrap by password if password is reset.
5. Register device wrap (`user_device_vault_register`).
6. Recovery‑Key rotation is only possible while UVK is unlocked.

---

# 8) Realtime Commands (Current) [Implemented]

**Auth:**
- `auth_register_request`
- `auth_login_request`
- `auth_identity_request`

**WebAuthn (HTTP):**
- `POST /api/webauthn/register/begin`
- `POST /api/webauthn/register/finish`
- `POST /api/webauthn/login/begin`
- `POST /api/webauthn/login/finish`

**Vault:**
- `user_vault_init`
- `user_vault_fetch`
- `user_vault_update_user_key`
- `user_vault_update_password`
- `user_vault_update_recovery`

**Device Vault:**
- `user_device_vault_fetch`
- `user_device_vault_register`

**Storage:**
- `file_key_wrap`
- `file_key_fetch`
- user_storage upload/list/download commands

---

# 9) Security Invariants (Implemented) [Implemented]

1. UVK never leaves the client unencrypted.
2. Active UVK is RAM‑only.
3. File keys are wrapped by UVK.
4. Device KEK is non‑exportable and device‑scoped.
5. localStorage must not store any cryptographic key material.
6. Auth success does not imply vault unlock.

---

# 10) Known Gaps / TODO (Explicit) [Planned]

- Token in localStorage is still used (acceptable for now, but not ideal).
- Device approval flow (new device unlock) is not yet implemented.
- Recovery UX still manual and needs explicit UI flow.
- Storage metadata encryption policy is minimal (filename plaintext for UI indexing).

---

# 11) Summary (Current) [Implemented]

The system now separates **authentication** from **vault unlock**.
UVK is the single storage root key, stored only as wrapped ciphertext server‑side.
Known devices can unlock via a device‑bound KEK, while new devices remain locked until recovery or approval.

This version documents the **current, running implementation** rather than a future target.

---

# 12) Device Pairing Specification (Binding, Next Step) [Planned]

This section defines the **required pairing flow** to allow multi‑device usage without weakening vault security.
It is **not implemented yet**; it specifies the next required build steps.

## 12.1 Principle
- **Auth != Unlock** remains enforced.
- New devices are **authenticated but vault_locked** until approved.
- Approval results in a **device‑wrapped UVK** stored server‑side.

## 12.2 Data Model (Server)
**`device_pairing_requests` (new)**
- `id`
- `user_id`
- `device_id`
- `device_label`
- `pairing_public_key` (exported public key from new device)
- `pairing_public_key_alg`
- `pairing_endpoint_token` (one‑time link token)
- `pairing_session_token` (short‑lived session for new device)
- `status` (`pending` | `approved` | `rejected` | `expired`)
- `created_at`
- `expires_at`
- `approved_at`
- `approved_by_device_id`

**`user_device_vault` (existing)**
- holds `wrapped_uvk_for_device` after approval.

## 12.2.1 Pairing Crypto (Binding)
- `pairing_public_key_alg`: `ECDH-P256`
- `pairing_wrap_alg`: `ECDH-P256 + HKDF-SHA256 + AES-GCM-256`
- `device_pairing_approve` must include `ephemeral_public_key` and a 96‑bit `nonce`.
- Derived wrap key is single‑use and must be discarded after encryption/decryption.

## 12.3 Commands (Realtime)
**From new device:**
- `device_pairing_request` (create pending request; includes `pairing_public_key` + `pairing_public_key_alg` + `pairing_endpoint_token`)

**From existing device:**
- `device_pairing_approve` (approve + deliver UVK transfer payload)
- `device_pairing_reject` (reject request)

**From server:**
- `device_pairing_request_ok`
- `device_pairing_status` (push to existing devices with new device info + `pairing_public_key`)
- `device_pairing_approved` (push to new device with encrypted UVK payload + `pairing_session_token`)
- `device_pairing_rejected`

## 12.4 Flow (Step‑by‑Step)

### A) New Device Flow
1. User opens **pairing link** containing `pairing_endpoint_token`.
2. Vault remains locked (no account login yet).
3. Client generates a **pairing public key** (exportable) and sends `device_pairing_request` with `pairing_endpoint_token`.
4. Server notifies existing devices (`device_pairing_status`) including the pairing public key.
5. UI shows “Waiting for approval”.

### B) Existing Device Approval
1. Existing device receives pairing request.
2. User confirms approval.
3. Existing device unwraps UVK (already active).
4. Existing device encrypts UVK for the **new device’s pairing public key**.
5. Existing device sends `device_pairing_approve` with `request_id`, `wrapped_uvk_for_pairing`, `pairing_wrap_alg`, `ephemeral_public_key`, and `nonce`.
6. Server marks pairing request as approved and forwards the payload to the new device.

### C) New Device Unlock
1. New device receives `device_pairing_approved` with encrypted UVK payload and `pairing_session_token`.
2. New device unwraps UVK using its pairing private key.
3. New device wraps UVK with its Device KEK and calls `user_device_vault_register` (authorized via `pairing_session_token`).
4. New device calls `user_device_vault_fetch` and unlocks.
5. Vault becomes `unlocked`.

## 12.5 UI States (Required)
**New Device**
- `pairing_pending`
- `pairing_failed`
- `vault_unlocked`

**Existing Device**
- `pairing_request_inbox`
- `approve` / `reject` actions

## 12.6 Security Rules (Binding)
1. Device approval must require **an already unlocked UVK**.
2. Approval never exposes UVK to the server (wrap occurs on client).
3. Rejection/expiry leaves vault locked.
4. Pairing requests must expire after **15 minutes**.
5. Audit events must be logged for all approvals/rejections.
6. Pairing payloads must be short‑lived and non‑replayable (single use).
7. Pairing link must be **one‑time** (consume `pairing_endpoint_token` on first request).
8. `pairing_session_token` must be short‑lived and scoped only to device registration calls.
