# Tech Debt

This file tracks concrete, current technical debt items. It is not a design doc. Each item should describe what is missing today, why it matters, and what it would take to resolve it.

## 1) E2E Trust and Device Verification (Not Implemented)

**Current state**
- Device keys are server-registered and mapped to users.
- The system does not perform user-verified trust (no QR/code verification).
- New devices are accepted without user confirmation.
- Trust Center UI exists but does not drive mandatory trust flows.

**Why this matters**
- Server mapping is not the same as E2E verification.
- Users cannot prove a device is truly controlled by the contact.
- MITM or compromised server scenarios are not detectable by users.

**Debt scope**
- No per-contact/per-device trust state (trusted/untrusted/revoked) persisted client-side.
- No cross-sign flow for new devices.
- No explicit UX for verification on new device joins.
- No policy that restricts history/visibility based on trust state.

**Resolution direction (not yet implemented)**
- Introduce trust state per contact + device.
- Support QR/code verification and/or cross-sign.
- Add notifications and UI warnings for unverified devices.
- Decide policy: allow chat with warnings vs. block until verified.

**Status**
- Priority: Medium
- Owner: TBD
- Target: Pilot+1

## 2) Terminology Alignment (Auth vs. Device Keys)

**Current state**
- "Device Key", "IdentityAuth", and "WebAuthn" are used inconsistently across docs.
- Some docs still describe a single device-key-based auth flow.

**Why this matters**
- Confusing for contributors and new developers.
- Increases onboarding time and risks wrong assumptions.

**Resolution direction**
- Clarify: Device Key is the key material, IdentityAuth is the login flow using it, WebAuthn is a separate auth path.
- Update affected docs in `docs/workflows/` and `docs/crypto/`.

**Status**
- Priority: Low
- Owner: TBD

## 3) Trust/Verification Data Sync Across Devices

**Current state**
- No encrypted sync of trust decisions across a user's devices.

**Why this matters**
- Trust decisions are device-local and can diverge.

**Resolution direction**
- Store trust records encrypted with user key and sync via backend.

**Status**
- Priority: Low
- Owner: TBD
