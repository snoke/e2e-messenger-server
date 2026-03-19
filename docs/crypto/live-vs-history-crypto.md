# Live Transport vs. History Crypto

This document explains why calls and chat use different crypto strategies, and why MLS-only history is not viable without persistent key storage.

## 1) Calls (Live Media)

**Summary**
- LiveKit transports media streams.
- Optional media E2EE uses Insertable Streams (SFrame-style).
- **Media keys are distributed over MLS-protected control conversations**.
- Media keys are **ephemeral** and **not persisted**.

**Implication**
- Clean model for live media.
- Not suitable for history or late device joins.

## 2) Chat (Live + History)

**Summary**
- **MLS = live transport** for realtime messages.
- **CHK = storage/history** encryption.
- CHK is **user-bound** and stored as server-side wraps.
- **Invite pre-provisions** CHK wraps; **Accept delivers** them.
- `conversation_key_fetch` is **recovery**, not the normal path.

**Implication**
- History is stable across reloads and new devices.
- MLS state is not required for history.
- Accept implies **access + key delivery** (no post-accept race).

## 3) MLS-Only History Options

### Option A: MLS-only History (No CHK)

**Cost:** Very high.

**Problems**
- MLS keys are epoch-based and ephemeral.
- Reloads or device changes lose old secrets.
- History becomes unreadable ("desired gen in the past").

**Consequence**
- Persisting MLS secrets breaks forward secrecy and adds high complexity.

### Option B: Storage Keys per MLS Epoch

**Cost:** High to very high.

**Pros**
- Better damage radius on membership changes.

**Cons**
- Still requires persistent epoch keys.
- More complex than a single CHK.

### Option C: Hybrid (MLS for live + persistent wraps for history)

**Cost:** Medium.

**Model**
- MLS carries storage keys as a fast path.
- **Source of truth remains persistent wraps**.

**Result**
- Works with new devices and reloads.
- MLS is not the sole authority for history.

## 4) User Flow Effects

### Current (CHK + user-bound wraps)

**Signup**
- Auth session established.
- Vault/UVK initialized.
- User key created and stored.
- CHK is pre-provisioned at invite and delivered at accept.

**Sign-in**
- Auth session established.
- Vault unlock (UVK).
- User key ensured.
- CHK delivered by accept (fetch only on recovery).

**Device change / reload**
- Vault unlock.
- `conversation_key_fetch` as recovery.
- History remains readable.

### MLS-only History

**Device change / reload**
- History is missing unless MLS secrets are persisted.

## 5) Recommended Direction

- Keep **CHK for history**.
- Optionally rotate CHK on membership changes.
- Use MLS only for live transport and fast key distribution.

## Related
- Crypto overview: [docs/crypto/crypto-overview.md](crypto-overview.md)
- CHK: [docs/crypto/chk.md](chk.md)
- Wrapping: [docs/crypto/wrapping.md](wrapping.md)
