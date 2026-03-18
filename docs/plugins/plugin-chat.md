# Plugin: Chat

## Responsibilities
- Conversations and membership UI.
- Message history and live updates.
- Typing and read receipts.
- Conversation-level MLS orchestration.

## Crypto
- MLS for live transport.
- MLS key agreement uses **X‑Wing (X25519 + ML‑KEM‑768)**.
- CHK for history storage.
- Invite/accept pre-provisions CHK wraps.

## Key Files
- [`frontend/src/plugins/vue-chat/components/VueChatHome.vue`](../../frontend/src/plugins/vue-chat/components/VueChatHome.vue)
- [`frontend/src/app/core/messaging/services/messenger/realtime/conversations.ts`](../../frontend/src/app/core/messaging/services/messenger/realtime/conversations.ts)
- [`frontend/src/app/core/messaging/services/messenger/conversationKeys.ts`](../../frontend/src/app/core/messaging/services/messenger/conversationKeys.ts)

Related:
- [`docs/workflows/invite-accept.md`](../workflows/invite-accept.md)
- [`docs/crypto/chk.md`](../crypto/chk.md)
