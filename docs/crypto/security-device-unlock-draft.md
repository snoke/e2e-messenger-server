# Security Architecture — Device Unlock Target (v1)

Status: **Binding decision draft**

This document captures the **explicit architecture decision** for passwordless authentication + device-based vault unlock.
It translates the current system into a **clear state machine**, introduces **device-wrapped UVKs**, and defines the minimal refactor path.

---

## 1. Core Decisions (Binding)

### Decision 1 — Auth and Unlock are separate
**Authentication** answers: *Who is the user?*
- Session, token, passkey, identity proof.

**Vault Unlock** answers: *Is this device allowed to decrypt the UVK?*
- Controlled by **device-bound unlock factors**.

Authentication **must not imply** vault unlock.

### Decision 2 — UVK remains the only storage root key
- UVK is the sole root for storage encryption.
- File keys remain wrapped by UVK.
- Server stores **only wrapped UVKs**.

### Decision 3 — Device-wrapped UVKs for known devices
Each registered device gets a **device-bound KEK**.
- The **Device KEK is a new, dedicated key** used **only** for vault unlock.
  - It must **not** reuse Identity keys.
  - It must **not** reuse Secure Store KEK/DEK.
- UVK is additionally wrapped **per device** → `wrappedUvkForDevice`.
- Server stores `wrappedUvkForDevice` bound to `device_id`.
- Client stores **only device-bound key material** (non-exportable CryptoKey or handle).
- **Active UVK stays RAM-only.**

### Decision 4 — New devices are locked by default
On a new device:
- Authentication may succeed.
- Vault remains locked.
- Unlock requires **Recovery** or **Device Approval**.

### Decision 5 — localStorage is forbidden for sensitive material
No cryptographic secrets or derived keys in localStorage.
This explicitly includes:
- KeyGraph project keys
- any UVK or device-wrapped UVK

---

## 2. State Machine (Target)

**States**
- `authenticated`
- `vault_locked`
- `vault_unlocked`
- `device_registered`

**Transitions**
1. `authenticated` + `device_registered` + device unwrap success → `vault_unlocked`
2. `authenticated` + device unwrap failed → `vault_locked`
3. `vault_locked` + recovery unlock → `vault_unlocked`
4. `vault_locked` + device approval → `vault_unlocked`
5. `vault_unlocked` + logout/reload → `vault_locked`

---

## 3. Data Model (Device-Wrapped UVK)

### 3.1 Server-side (new or extended)
**Decision — New table** `user_device_vault`
- `user_id`
- `device_id`
- `wrapped_uvk_for_device`
- `wrap_algorithm`
- `created_at`
- `updated_at`

**Binding rule:** server stores only **wrapped** UVK, never raw.

### 3.2 Client-side (device-bound key)
**Device KEK**
- Generated via `crypto.subtle.generateKey` with non-exportable flag.
- Stored in IndexedDB (CryptoKey handle).
- Used to unwrap `wrappedUvkForDevice` locally.

**No raw UVK persistence.**

---

## 4. Target Flows

### 4.1 Known device (passwordless)
1. Identity login (auth OK → session established)
2. Fetch device record + `wrappedUvkForDevice`
3. Unwrap with device KEK
4. UVK stays in RAM
5. Storage enabled

### 4.2 New device
1. Identity login (auth OK)
2. `wrappedUvkForDevice` missing
3. Vault locked UI
4. Unlock via:
   - Recovery Key, or
   - Device Approval

### 4.3 Recovery flow
1. User provides Recovery Key
2. Fetch `wrapped_uvk_by_recovery`
3. Unwrap UVK
4. **Always** register device KEK and store `wrappedUvkForDevice`
5. Mark device as `device_registered = true`

---

## 5. Mapping to Existing Code

**Existing vault logic (RAM-only UVK)**
- [`frontend/src/app/messaging/messenger/userVault.ts`](../../frontend/src/app/messaging/messenger/userVault.ts)
  - `activeUvk` is in-memory only
  - `fetchUserVault()`, `initUserVault()`

**Password login unlocks UVK**
- [`frontend/src/plugins/auth/app/components/AuthLogin.vue`](../../frontend/src/plugins/auth/app/components/AuthLogin.vue)
  - fetch + unwrap + `setActiveUvk`

**Identity login does NOT unlock UVK**
- [`frontend/src/plugins/identity-auth/components/IdentityAuthLogin.vue`](../../frontend/src/plugins/identity-auth/components/IdentityAuthLogin.vue)

**Storage requires UVK**
- [`frontend/src/app/messaging/messenger/userStorage.ts`](../../frontend/src/app/messaging/messenger/userStorage.ts)
  - throws `user_storage_missing_uvk`

**Local device keys**
- Identity device key in IndexedDB
  - [`frontend/src/plugins/device-key-manager/services/deviceKeyStore.ts`](../../frontend/src/plugins/device-key-manager/services/deviceKeyStore.ts)

**Local secure store (IndexedDB CryptoKeys)**
- [`frontend/src/app/messaging/crypto/shared/secureStore.ts`](../../frontend/src/app/messaging/crypto/shared/secureStore.ts)

**Server vault storage**
- [`symfony/src/Entity/UserKeyVault.php`](../../symfony/src/Entity/UserKeyVault.php)
- [`symfony/src/Plugins/UserVault/...`](../../symfony/src/Plugins/UserVault/...) actions

---

## 6. Minimal Refactor Path

### Phase A — Explicit state model
Introduce a **Vault State Store** with:
- `authenticated`
- `vault_locked`
- `vault_unlocked`
- `device_registered`

### Phase B — Central Unlock layer
Remove direct UVK setting from login components.
Instead, route all unlocks via a **Vault Unlock Service**.

### Phase C — Device-wrap UVK
- Generate device KEK (non-exportable).
- Wrap UVK and store `wrappedUvkForDevice` server-side.

### Phase D — Wire identity login → device unlock
- Identity login triggers device-unlock attempt.
- If failure → locked UI.

### Phase E — New device flow
- Recovery or Approval unlock path.
- After success, register device wrap.

---

## 7. Non-Goals (Explicit)
- UVK never persisted in raw form.
- No sensitive secrets in localStorage.
- Passwordless login must not imply vault unlock unless device is trusted.

---

## 8. Open Decisions

1. **Device approval flow**: UX + transport channel.
2. **Recovery UX**: where and how recovery unlock is triggered.
3. **localStorage cleanup**: migrate KeyGraph project keys or deprecate.

---

## 9. Implementation Guardrails (Binding)

- `activeUvk` is RAM-only.
- No plaintext UVK in IndexedDB or localStorage.
- Device KEK is a **dedicated vault-unlock key** (no reuse of Identity keys or Secure Store keys).
- Device KEKs must be non-exportable CryptoKeys.
- Authentication success does not imply storage access.
- Storage operations must enforce `vault_unlocked`.