# Security Architecture (Ist‑Zustand → Zielbild)

Status: **Architecture planning** (binding target standard for future security work).
This document describes the **current implementation (Ist‑Zustand)** and the **target model (Zielbild)** for keys, encryption, storage, and multi‑device behavior.

---

## 0) Scope and Principles

**Goal:**
- Backend is the **source of distribution**.
- Client holds the **source of decryption capability**.

**Constraints:**
- Device keys are device‑specific and **not exportable**.
- No server access to plaintext secrets.

---

## 1) Ist‑Zustand (Current Implementation)

### 1.1 Auth / Recovery
- **Recovery‑Key** is currently just the **account password**.
  - Sent as `password` in `auth_register_request` and `auth_login_request`.
  - Stored as password hash in `users`.
- **Identity login** exists via device key proof (`auth_identity_request`).

### 1.2 Device / Identity Keys
- Device identity keypair: **ECDSA P‑256** (WebCrypto, non‑extractable).
- Stored locally in IndexedDB:
  - DB: `identity.auth.keys.v1`
  - Store: `keys`
- Server stores **public key + metadata** in `user_identity_keys`.

### 1.3 Identity Profile Encryption
- Profile payload encrypted with **AES‑GCM**.
- Symmetric key stored in IndexedDB:
  - DB: `identity.profile.crypto.v1`
  - Store: `keys`
- Server stores encrypted profile blob in `user_identity_profiles`.

### 1.4 User Storage (Cloud) – File Encryption
- Files are encrypted **client‑side** with **ChaCha20‑Poly1305**.
- For each file:
  - `file_key` + `nonce_seed` generated locally.
  - `ciphertext` + `sha256` uploaded via `user_storage_upload_payload`.
- **KeyGraph envelope** (wraps `file_key + nonce_seed`):
  - Encrypted with a **project key** stored in **localStorage** (`messaging.keygraph.project.v1:<scope>`).
  - KeyGraph is stored on server as part of file meta.
  - **Result:** key material is **device‑bound** (not multi‑device friendly).

### 1.5 Secure Store (Local)
- `e2ee.secure.store.v1` stores wrapped records (KEK/DEK) used by keyfile store.
- Used by user‑storage keyfile store (`keyfileStore.ts`).

### 1.6 MLS / KeyPackages
- Each device publishes its own **KeyPackages**.
- Commands:
  - `mls_key_package_publish`
  - `mls_key_package_fetch`
  - `mls_commit`, `mls_welcome_request`, `mls_welcome_ack`
- MLS membership is device‑based (new device requires new KeyPackage + Commit/Welcome).

### 1.7 IndexedDB Usage (Current)
- `identity.auth.keys.v1` (device identity keys)
- `identity.profile.crypto.v1` (profile encryption key)
- `e2ee.secure.store.v1` (secure store for wrapped records)
- `void-contact-profiles-v1` (contacts cache)
- `storage.manager.cloud.v1` (cloud folders cache)
- `void.file-transfer.memory.v1` (transfer temp chunks)
- `anonymous.dropbox.keys.v2` (dropbox PQ private keys)
- `desktop.secure.vault.keys.v1` (local vault keys)

### 1.8 Current Commands (Relevant)
**Auth:**
- `auth_register_request`
- `auth_login_request`
- `auth_identity_request`

**Identity profile:**
- `identity_profile_request`
- `identity_profile_upsert`

**Contacts:**
- `contacts_request`
- `contact_profiles_request`
- `contact_profile_upsert`
- `contact_profile_delete`

**User storage:**
- `user_storage_upload_init`
- `user_storage_upload_payload`
- `user_storage_upload_finalize`
- `user_storage_download`
- `user_storage_list_request`
- `user_storage_delete_request`
- `user_storage_share_link_create`
- `user_storage_share_links_request`
- `user_storage_share_link_revoke`
- `user_storage_share_info_request`
- `user_storage_share_download`

**MLS:**
- `mls_key_package_publish`
- `mls_key_package_fetch`
- `mls_commit`
- `mls_welcome_request`
- `mls_welcome_ack`

### 1.9 Ist‑Zustand Limitations
- Recovery key does **not** decrypt any secrets.
- File keys are **device‑bound** due to localStorage project key.
- Multi‑device access to old encrypted files is **not possible** without manual key transfer.

---

## 2) Zielbild (Target Architecture)

### 2.1 Core Decision
**Backend = Source of Distribution**
**Client‑held master secret = Source of Decryption**

### 2.2 Key Layers

**A) Device Keys (per device)**
- Identity/signing keys, MLS key packages.
- Non‑exportable.
- Used for auth proofs + MLS membership.

**B) User Vault Key (UVK) (per user)**
- Random symmetric root key.
- Used **only** to wrap other keys (file keys, app secrets).

**C) Access Keys**
- Per file or per scope (e.g., file_key).
- Wrapped by UVK; stored server‑side as ciphertext.

### 2.3 Key Wrapping Strategy
Password/recovery keys **wrap only UVK**:
- `wrapped_uvk_by_password`
- `wrapped_uvk_by_recovery`
- optional: `wrapped_uvk_by_device_transfer`

**Benefit:** password/recovery changes do **not** require re‑wrapping all file keys.

---

## 3) Target Data Model

### 3.1 user_key_vault
- `user_id`
- `vault_version`
- `wrapped_uvk_by_password`
- `password_kdf_salt`
- `password_kdf_params`
- `wrapped_uvk_by_recovery`
- `recovery_kdf_salt`
- `recovery_kdf_params`
- `created_at`, `updated_at`

### 3.2 device_registry
- `device_id`
- `user_id`
- `device_label`
- `identity_public_key`
- `credential_public_data`
- `created_at`, `last_seen_at`, `revoked_at`

### 3.3 device_key_packages
- `device_id`
- `key_package_ref`
- `mls_key_package`
- `consumed_at`, `expires_at`

### 3.4 file_objects
- `file_id`
- `owner_user_id`
- `ciphertext_ref`
- `content_nonce_info`
- `metadata_ciphertext` or explicit plaintext metadata
- `created_at`

### 3.5 file_key_records
- `file_id`
- `access_scope` (user | group | device)
- `scope_id`
- `key_version`
- `wrapped_file_key`
- `wrap_alg`
- `created_at`

---

## 4) Target Commands / Contracts

### 4.1 Auth / Vault
- `user_vault_init` (store wrapped UVK + KDF params)
- `user_vault_fetch` (return wrapped UVK + KDF params)
- `user_vault_update_password` (rewrite wrapped_uvk_by_password)
- `user_vault_update_recovery` (rewrite wrapped_uvk_by_recovery)

### 4.2 File Keys
- `file_key_wrap` / `file_key_fetch`
- `file_key_rewrap` (optional for rotation)

### 4.3 Device Registry
- `device_register`
- `device_revoke`

### 4.4 MLS
- no change to MLS commands; new device uses publish → commit/welcome.

---

## 5) Frontend Flows (Target)

### 5.1 Signup
1. Create Device Identity Key (local).
2. Generate UVK (random).
3. Generate Recovery‑Key.
4. Derive `password_kek` and `recovery_kek` via KDF.
5. Wrap UVK twice (password + recovery).
6. Publish KeyPackages.
7. Send `user_vault_init` to server.

### 5.2 Login (New Device)
1. Normal login (password).
2. Fetch wrapped UVK + KDF params (`user_vault_fetch`).
3. Derive `password_kek`, unwrap UVK.
4. Create device keys, publish KeyPackages.
5. Fetch wrapped file keys → unwrap with UVK.

### 5.3 Recovery
1. User provides Recovery‑Key.
2. Fetch wrapped UVK + KDF params.
3. Derive `recovery_kek`, unwrap UVK.
4. Set new password → rewrap UVK by password.

### 5.4 Password Change
1. Unwrap UVK with current password.
2. Derive new `password_kek`.
3. Rewrap UVK by password.

### 5.5 File Upload
1. Generate `file_key`.
2. Encrypt file locally (ChaCha20‑Poly1305).
3. Wrap file_key with UVK.
4. Store ciphertext + wrapped file key on server.

### 5.6 Device Revocation
1. Mark device revoked.
2. Rotate MLS group membership (commit/welcome).
3. Optionally rotate file keys (expensive).

---

## 6) Security Invariants (Binding)

1. Server never stores plaintext secrets.
2. UVK never leaves the client unwrapped.
3. Password/recovery only wrap UVK, not file keys.
4. Device keys are non‑exportable and device‑scoped.
5. MLS state remains device‑centric (no blind server restore in v1).
6. Revocation stops **future** access; cached keys remain on revoked devices.

---

## 7) Migration Notes (Future)

- Ist‑Zustand uses localStorage project key for keyGraph (device‑bound). Target replaces with UVK wrapping.
- Recovery‑Key becomes a **true recovery path** (unwrap UVK).
- Introduce `user_key_vault` and `file_key_records` tables.

---

## 8) Open Decisions

- Which metadata remains plaintext vs encrypted.
- KDF parameters (Argon2 vs scrypt) and rotation cadence.
- File key rotation policy (on device revoke or only on explicit action).

