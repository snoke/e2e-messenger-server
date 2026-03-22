# System Behavior Overview

This document describes the current runtime behavior of the project. It is focused on *what happens* in the running system (not a design proposal), so new contributors can understand the end‑to‑end flow.

## Scope

- Authentication + vault unlock
- Realtime session readiness
- Conversation lifecycle (MLS)
- History encryption (CHK) and distribution
- Crypto state gating in UI
- Notifications for inactive chats
- Contacts vs users directory behavior

## High‑Level Architecture (Runtime)

- MLS is used for live transport of chat/call payloads.
- CHK (Conversation History Key) is used for storage/history encryption.
- User Vault (UVK) protects per‑user key material on the client.
- Server stores only wrapped keys and ciphertexts.

## Auth, Vault, and Crypto Readiness

### What “crypto ready” means (global)

A user is considered crypto‑ready when all of the following are true:

- Vault is unlocked (`vaultUnlocked`).
- Device vault is registered (`deviceRegistered`).
- User Key material is available (`userKeyReady`).

The gate is enforced in [`frontend/src/app/messaging/sessionGate.ts`](../../frontend/src/app/messaging/sessionGate.ts) and used by the UI.
This is **global readiness**. Conversation readiness is handled separately (see below).

### Sign‑in / unlock sequence (runtime)

1. User authenticates (password, identity, or WebAuthn).
2. Client unlocks vault:
   - Password: `user_vault_fetch` + KDF unwrap
   - Identity: `user_device_vault_fetch` + device unwrap
   - WebAuthn: `POST /api/webauthn/login/*` + PRF unwrap
3. Client unwraps UVK and loads or generates the user key.
4. Client persists user key (`user_vault_update_user_key`).
5. Client registers device vault (`user_device_vault_register`).
6. When all are ready, client emits `session_ready` and sets crypto ready.

**Key files**

- [`frontend/src/app/messaging/messenger/vaultUnlock.ts`](../../frontend/src/app/messaging/messenger/vaultUnlock.ts)
- [`frontend/src/app/messaging/messenger/userKey.ts`](../../frontend/src/app/messaging/messenger/userKey.ts)
- [`frontend/src/app/messaging/sessionGate.ts`](../../frontend/src/app/messaging/sessionGate.ts)
- [`frontend/src/plugins/webauthn-auth/webauthnClient.ts`](../../frontend/src/plugins/webauthn-auth/webauthnClient.ts)
- [`symfony/src/Controller/WebAuthnController.php`](../../symfony/src/Controller/WebAuthnController.php)

## Realtime Session and Scopes

Realtime is driven by `realtimeRouter.ts`. It routes incoming frames to modules based on active scopes.

- `conversation_ops` handles active chat operations.
- `chat_list_ops` drives list updates and background state.
- `notifications_feed_ops` drives notification delivery.

**Key files**

- [`frontend/src/app/messaging/realtimeRouter.ts`](../../frontend/src/app/messaging/realtimeRouter.ts)
- [`frontend/src/app/messaging/messenger/realtimeModules.ts`](../../frontend/src/app/messaging/messenger/realtimeModules.ts)

## Conversations and MLS

### Creating a group conversation

1. Creator creates a conversation.
2. MLS state is created locally.
3. Server broadcasts `group_created` and updates membership.
4. MLS commit/welcome flows are queued for new members.

MLS is used only for live transport (realtime encryption of messages, typing, etc.).
MLS key agreement uses **X‑Wing (X25519 + ML‑KEM‑768)** for post‑quantum KEX.

**Key files**

- [`frontend/src/app/messaging/messenger/realtime/conversations.ts`](../../frontend/src/app/messaging/messenger/realtime/conversations.ts)
- [`frontend/src/app/messaging/messenger/realtime/crypto.ts`](../../frontend/src/app/messaging/messenger/realtime/crypto.ts)

## CHK (Conversation History Key)

### What CHK is used for

- History/storage encryption only.
- A message is encrypted **twice**:
  1. MLS for live transport
  2. CHK for storage/persistence

### Server storage

The server stores only wrapped CHKs per member in `conversation_key_records`.
The server is not provided with CHK material and therefore cannot decrypt or unwrap it.

### Distribution and accept delivery (current model)

- Creator generates CHK in RAM.
- Creator **pre‑provisions a member‑specific wrap at invite time** and persists it server‑side.
- Pending members **cannot** fetch wraps (`conversation_key_fetch` is blocked for pending).
- When the invited member accepts, the **accept response includes the prepared wrap**.
- The accepting client unwraps immediately and becomes conversation‑ready.

**Key files**

- [`frontend/src/app/messaging/messenger/conversationKeys.ts`](../../frontend/src/app/messaging/messenger/conversationKeys.ts)
- [`symfony/src/Plugins/Chat/Application/Realtime/Action/GroupAddAction.php`](../../symfony/src/Plugins/Chat/Application/Realtime/Action/GroupAddAction.php)
- [`symfony/src/Plugins/Chat/Application/Realtime/Action/GroupMembershipAcceptAction.php`](../../symfony/src/Plugins/Chat/Application/Realtime/Action/GroupMembershipAcceptAction.php)

### State‑based distribution (non‑invite cases)

If active members exist without a wrap (legacy state, recovery, or migration), the creator can still distribute missing wraps based on active member state.

**Key files**

- [`frontend/src/app/messaging/messenger/realtime/conversations.ts`](../../frontend/src/app/messaging/messenger/realtime/conversations.ts)

## Crypto State Gating in UI

The UI is tied to a per‑conversation crypto state:

- `pending_key_init`
- `crypto_ready`
- `crypto_error`

Behavior:

- If `pending_key_init`, chat input is disabled and a status message is shown.
- If `crypto_ready`, full chat UI is enabled.
- If `crypto_error`, UI shows an error and stays disabled.

**Key files**

- [`frontend/src/app/messaging/messenger/index.ts`](../../frontend/src/app/messaging/messenger/index.ts)
- [`frontend/src/plugins/vue-chat/components/VueChatHome.vue`](../../frontend/src/plugins/vue-chat/components/VueChatHome.vue)

## CHK Fetch Behavior (Recovery Only)

`conversation_key_fetch` exists as a recovery path, but **pending members are blocked**.  
The normal flow for an invited user is **accept → wrap delivered → unwrap** (no retry loop).

## Notifications for Inactive Chats

Notifications must fire even when chat UI is inactive.

Current approach:

- Background Event Bridge (BEB) receives realtime frames globally.
- Adapters convert events into background events.
- Notification layer is the single delivery authority.

**Key files**

- [`frontend/src/app/messaging/messenger/backgroundEventBridge.ts`](../../frontend/src/app/messaging/messenger/backgroundEventBridge.ts)
- [`frontend/src/app/messaging/messenger/notificationCenter.ts`](../../frontend/src/app/messaging/messenger/notificationCenter.ts)

## Contacts vs Users Directory

The system is intended to expose **contacts only**, not the full tenant user list.

- Contacts are requested via the contacts flow.
- `users` is not the authoritative directory for key distribution in normal UI.

**Known gap:** some environments still emit `users` payloads. This is a bug or legacy behavior and should be treated as inconsistent with the intended model.

**Key files**

- [`symfony/src/Plugins/ContactBook/Application/Realtime/ContactRealtimeSupport.php`](../../symfony/src/Plugins/ContactBook/Application/Realtime/ContactRealtimeSupport.php)
- [`symfony/src/Plugins/Chat/Application/UserDirectoryService.php`](../../symfony/src/Plugins/Chat/Application/UserDirectoryService.php)
- [`frontend/src/app/messaging/messenger/userDirectory.ts`](../../frontend/src/app/messaging/messenger/userDirectory.ts)

## Typical Invite/Accept Flow (With CHK)

1. A creates group (MLS state created).
2. A creates CHK and **pre‑provisions Bob’s wrap at invite time**.
3. A invites B (MLS commit + welcome for B).
4. B accepts → **accept response includes the prepared wrap**.
5. B unwraps CHK immediately and becomes conversation‑ready.
6. History can now be decrypted; UI is enabled.

## Where to Start Debugging

- `conversation_key_fetch_ok` is received but UI stuck:
  - Check `unwrap` logs and `crypto_ready` logs.
- No notifications for inactive chats:
  - Check background event bridge and notification center.
- Key mismatch issues:
  - Compare `user_vault_fetch_ok` user_key_public with DB.
