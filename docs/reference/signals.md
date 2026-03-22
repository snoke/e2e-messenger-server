# Signals (Generic MLS Signal Envelope)

This document defines the **generic signal envelope** used to reduce metadata exposure for MLS‑encrypted realtime signals (currently: chat typing). It describes the on‑wire shape, routing, and how to temporarily disable the envelope for metadata debugging.

## 1) Motivation

Historically, `typing` was delivered as plaintext with:

- `type: typing`
- `conversation_id`
- `isTyping`

That leaks **event type** and **conversation identity** in the raw websocket payload.  
The new envelope hides those fields behind MLS ciphertext and an opaque scope key.

## 2) Signal Envelope (On‑Wire)

All generic signals are sent as:

```
{
  "type": "signal",
  "scope_key": "<opaque>",
  "session_epoch": <number>,
  "crypto_profile": "MLS_256_XWING_CHACHA20POLY1305_SHA512_MLDSA87",
  "ciphertext": "<base64>",
  "nonce": "<base64>",
  "suite": "mls_chacha20",
  "header": { "dh": "mls", ... }
}
```

Notes:
- `type` is always `"signal"`, **not** `"typing"` or other domain types.
- `scope_key` is a per‑conversation opaque identifier (persisted on `Conversation.scopeKey`).
- The payload inside `ciphertext` is a JSON object (currently `{ type: "typing", isTyping: true|false }`).
- `crypto_profile` includes `XWING`, which denotes **X‑Wing (X25519 + ML‑KEM‑768)** for post‑quantum key agreement.

## 3) Scope Key

`scope_key` is used to map the signal back to a conversation without exposing `conversation_id`.

Implementation references:
- **Backend**: [`symfony/src/Entity/Conversation.php`](../../symfony/src/Entity/Conversation.php) (`scopeKey`)
- **Builder**: [`symfony/src/Plugins/Chat/Application/ConversationItemBuilder.php`](../../symfony/src/Plugins/Chat/Application/ConversationItemBuilder.php) (generated and persisted)
- **Frontend mapping**:
  - [`frontend/src/app/messaging/messenger/realtime/conversations.ts`](../../frontend/src/app/messaging/messenger/realtime/conversations.ts)
  - [`frontend/src/app/messaging/messenger/realtime/presence.ts`](../../frontend/src/app/messaging/messenger/realtime/presence.ts)

## 4) Current Usage

Currently, signals are used for **chat typing** only.

Sender path:
- [`frontend/src/app/messaging/messenger/send.ts`](../../frontend/src/app/messaging/messenger/send.ts)
  - builds MLS ciphertext
  - sends `type: "signal"` when `scopeKey` is available
  - falls back to `chat_typing_state` if `scopeKey` is missing

Receiver path:
- [`frontend/src/app/messaging/messenger/realtime/presence.ts`](../../frontend/src/app/messaging/messenger/realtime/presence.ts)
  - accepts `type: "signal"`
  - resolves `scope_key` → `conversation_id`
  - decrypts MLS payload
  - applies typing update

Backend routing:
- [`gateway/rust-http3-gateway/src/project/command_registry.rs`](../../gateway/rust-http3-gateway/src/project/command_registry.rs) (registers `signal`)
- [`symfony/src/Plugins/Chat/Application/Realtime/Action/SignalAction.php`](../../symfony/src/Plugins/Chat/Application/Realtime/Action/SignalAction.php)
- [`symfony/src/Plugins/Chat/Interface/Realtime/MessageHandler/ChatMessageHandlerRegistry.php`](../../symfony/src/Plugins/Chat/Interface/Realtime/MessageHandler/ChatMessageHandlerRegistry.php)

## 5) Security Properties

What is now **hidden** on the wire:
- The event type (`typing`) lives inside MLS ciphertext.
- `conversation_id` is not exposed.

What remains **visible**:
- `type: "signal"` (constant)
- `scope_key` (opaque, random)
- `session_epoch`, `session_updated_at`
- `suite`, `header`, and other MLS metadata

## 6) Failure Modes / Fallbacks

If `scope_key` is missing (or not yet present in the frontend):
- Sender falls back to `chat_typing_state` (legacy path).

If decryption fails or epoch mismatch:
- Receiver drops the signal silently and logs debug entries.

## 7) Debugging: Temporarily Disable Signals (Expose Metadata)

There is **no runtime flag** yet. For metadata debugging you can temporarily revert to the old plaintext typing path.

### Option A: Force the Legacy Path in Frontend (fastest)

In [`frontend/src/app/messaging/messenger/send.ts`](../../frontend/src/app/messaging/messenger/send.ts):
- temporarily bypass the `scope_key` branch so it always sends `chat_typing_state`.

This makes websocket traffic show:

```
{ type: "typing", conversation_id: ..., isTyping: ... }
```

### Option B: Drop `scope_key` in Local State (quick inspection)

If you null out `conversation.scopeKey` in runtime state, the sender falls back to `chat_typing_state`.
This is fragile because the next conversations refresh re‑hydrates `scope_key`.

### Option C: Disable the Signal Command on Backend

Temporarily remove/disable:
- `signal` entry in [`symfony/src/Plugins/Chat/Interface/Realtime/MessageHandler/ChatMessageHandlerRegistry.php`](../../symfony/src/Plugins/Chat/Interface/Realtime/MessageHandler/ChatMessageHandlerRegistry.php)
- `signal` registration in [`gateway/rust-http3-gateway/src/project/command_registry.rs`](../../gateway/rust-http3-gateway/src/project/command_registry.rs)

This forces clients to use the legacy `chat_typing_state` path (assuming Option A or B is applied).

## 8) Re‑Enable

Undo the temporary changes above and rebuild containers:

```
docker compose -f docker-compose.yaml -f docker-compose.websocket.yaml build symfony gateway frontend
docker compose -f docker-compose.yaml -f docker-compose.websocket.yaml up -d symfony gateway frontend
```

## 9) Future Extensions

The signal envelope is intended to cover additional MLS‑encrypted transient events:
- read receipts
- message metadata
- conversation signals

When extending:
- keep `type: "signal"` on the wire
- add only encrypted payload types inside ciphertext
- do **not** reintroduce plaintext `conversation_id` or event type
