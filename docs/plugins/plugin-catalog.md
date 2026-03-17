# Plugin Catalog

This document reflects the **current plugin inventory** in [`frontend/src/plugins`](../../frontend/src/plugins) and summarizes their roles.
Last verified: 2026-03-17.

## Shared Principles
- Realtime via WebSocket/WebTransport only (no ad-hoc REST for core flows).
- Source of truth: MySQL; Redis is transport.
- Client storage: IndexedDB for keys/caches/metadata.
- Crypto: plaintext only on client; server stores ciphertext and wrapped keys only, and is not provided with key material to decrypt them.

## Inventory (from [`frontend/src/plugins`](../../frontend/src/plugins))
- `about-void`: build/version info modal.
- `anonymous-dropbox`: public encrypted dropbox flow.
- `audit-timeline`: audit event timeline viewer.
- `auth`: password auth UI.
- `calls`: call signaling and LiveKit integration.
- `chat`: legacy chat UI.
- `client-devices`: device/session listing.
- `contact-book`: contacts UI and flows.
- `dead-man-switch`: safety/trigger flows (experimental).
- `desktop`: app shell / layout.
- `desktop-logout`: desktop logout UX.
- `device-key-manager`: device key creation/management.
- `device-pairing`: device pairing/approval (experimental).
- `file-transfer`: file transfer flow.
- `identity`: profile / identity UI.
- `identity-auth`: identity (device-key) login.
- `key-trust-center`: key trust UI (verified/unverified/revoked).
- `mobile`: mobile shell (experimental).
- `notification`: notification UI + settings.
- `opfs-storage`: OPFS storage adapter.
- `password-manager`: encrypted password vault.
- `secret-vault`: encrypted secret vault.
- `storage`: generic storage UI / adapters.
- `vue-chat`: current chat UI implementation.
- `vue-storage`: storage UI (VueFinder-based).
- `vue-storage-picker`: file picker UI.

## Crypto/Realtime‑Sensitive Plugins

### Calls
- Signaling via realtime.
- Media via LiveKit WebRTC.
- Optional media E2EE (Insertable Streams), keys delivered over MLS control channel.

### Chat (vue-chat)
- Conversations, history, typing, read receipts.
- MLS for live transport, CHK for storage history.
- Invite pre‑provisions CHK wrap; accept delivers wrap.

### File Transfer
- Realtime negotiation and chunked transfer.
- Crypto path depends on transfer mode (see [`docs/ops/tech-debt.md`](../ops/tech-debt.md)).

### Notification
- Notification center is the delivery authority.
- Uses background event bridge for inactive chat notifications.

## Storage/Vault Plugins
- `password-manager` and `secret-vault` store encrypted blobs in UserStorage.
- `vue-storage` / `storage` / `opfs-storage` provide UI and adapters.
- UserStorage is file-only (see [`docs/storage/user-storage-file-only.md`](../storage/user-storage-file-only.md)).

## Identity/Contacts
- `identity` handles profile values and avatar.
- `identity-auth` handles device-key login.
- `contact-book` manages contact graph and profiles.
- `key-trust-center` tracks fingerprint verification and trust state.

## Notes / Gaps
- Several plugins are experimental or partial (e.g., `dead-man-switch`, `device-pairing`, `mobile`).
- For authoritative flows, prefer the domain service in core messaging.

## Related
- Plugin standards: [`docs/plugins/plugin-standards.md`](plugin-standards.md)
- Scopes: [`docs/reference/scopes.md`](../reference/scopes.md)
- Crypto: [`docs/crypto/README.md`](../crypto/README.md)