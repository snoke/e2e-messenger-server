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

### What “crypto ready” means

A user is considered crypto‑ready when all of the following are true:

- Vault is unlocked (`vaultUnlocked`).
- Device vault is registered (`deviceRegistered`).
- User Key material is available (`userKeyReady`).

The gate is enforced in `frontend/src/app/core/messaging/services/sessionGate.ts` and used by the UI.

### Sign‑in / unlock sequence (runtime)

1. User authenticates (password or identity auth).
2. Client fetches vault via realtime (`user_vault_fetch`).
3. Client unwraps UVK and loads or generates the user key.
4. Client persists user key (`user_vault_update_user_key`).
5. Client registers device vault (`user_device_vault_register`).
6. When all are ready, client emits `session_ready` and sets crypto ready.

**Key files**

- `frontend/src/app/core/messaging/services/messenger/vaultUnlock.ts`
- `frontend/src/app/core/messaging/services/messenger/userKey.ts`
- `frontend/src/app/core/messaging/services/sessionGate.ts`

## Realtime Session and Scopes

Realtime is driven by `realtimeRouter.ts`. It routes incoming frames to modules based on active scopes.

- `conversation_ops` handles active chat operations.
- `chat_list_ops` drives list updates and background state.
- `notifications_feed_ops` drives notification delivery.

**Key files**

- `frontend/src/app/core/messaging/services/realtimeRouter.ts`
- `frontend/src/app/core/messaging/services/messenger/realtimeModules.ts`

## Conversations and MLS

### Creating a group conversation

1. Creator creates a conversation.
2. MLS state is created locally.
3. Server broadcasts `group_created` and updates membership.
4. MLS commit/welcome flows are queued for new members.

MLS is used only for live transport (realtime encryption of messages, typing, etc.).

**Key files**

- `frontend/src/app/core/messaging/services/messenger/realtime/conversations.ts`
- `frontend/src/app/core/messaging/services/messenger/realtime/crypto.ts`

## CHK (Conversation History Key)

### What CHK is used for

- History/storage encryption only.
- A message is encrypted **twice**:
  1. MLS for live transport
  2. CHK for storage/persistence

### Server storage

The server stores only wrapped CHKs per member in `conversation_key_records`.
The server never sees plaintext CHKs.

### Distribution and fetch

- Creator generates CHK in RAM.
- Creator wraps CHK for each member (user‑scoped).
- Creator sends `conversation_key_init` to persist wraps.
- Members use `conversation_key_fetch` to retrieve their wrapped CHK.

**Key files**

- `frontend/src/app/core/messaging/services/messenger/conversationKeys.ts`
- `symfony/src/Plugins/Chat/Application/Realtime/Action/ConversationKeyFetchAction.php`

### State‑based distribution

Distribution is driven by **active member state**, not just local diffs. If active members exist without a wrap, the creator distributes missing wraps.

**Key files**

- `frontend/src/app/core/messaging/services/messenger/realtime/conversations.ts`

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

- `frontend/src/app/core/messaging/services/messenger.ts`
- `frontend/src/plugins/vue-chat/components/VueChatHome.vue`

## CHK Fetch Retry and Ready State

### Bug that was fixed

The retry path previously ran only the low‑level fetch/unwrap and never set the crypto state to ready, so the UI stayed stuck on “Secure channel initializing…”.

### Current behavior

- `conversation_key_fetch_empty` schedules a retry.
- Retry uses `ensureConversationHistoryKey(...)` and triggers hooks.
- When a retry succeeds, `onKeyReady(...)` updates the crypto state to ready.

**Key files**

- `frontend/src/app/core/messaging/services/messenger/conversationKeys.ts`
- `frontend/src/app/core/messaging/services/messenger.ts`

## Notifications for Inactive Chats

Notifications must fire even when chat UI is inactive.

Current approach:

- Background Event Bridge (BEB) receives realtime frames globally.
- Adapters convert events into background events.
- Notification layer is the single delivery authority.

**Key files**

- `frontend/src/app/core/messaging/services/messenger/backgroundEventBridge.ts`
- `frontend/src/app/core/messaging/services/messenger/notificationCenter.ts`

## Contacts vs Users Directory

The system is intended to expose **contacts only**, not the full tenant user list.

- Contacts are requested via the contacts flow.
- `users` is no longer the authoritative directory for key distribution in normal UI.

**Key files**

- `symfony/src/Plugins/ContactBook/Application/Realtime/ContactRealtimeSupport.php`
- `symfony/src/Plugins/Chat/Application/UserDirectoryService.php`
- `frontend/src/app/core/messaging/services/messenger/userDirectory.ts`

## Typical Invite/Accept Flow (With CHK)

1. A creates group (MLS state created).
2. A creates CHK and persists wraps for members.
3. A invites B (MLS commit + welcome for B).
4. B accepts, applies welcome, and fetches CHK.
5. B unwraps CHK and becomes crypto‑ready.
6. History can now be decrypted; UI is enabled.

## Where to Start Debugging

- `conversation_key_fetch_ok` is received but UI stuck:
  - Check `unwrap` logs and `crypto_ready` logs.
- No notifications for inactive chats:
  - Check background event bridge and notification center.
- Key mismatch issues:
  - Compare `user_vault_fetch_ok` user_key_public with DB.

