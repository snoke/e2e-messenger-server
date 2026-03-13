# Frontend Scope Model

This document defines the frontend scope architecture for realtime messaging. It separates UI presence from operational processing, sets clear ownership by plugin, and defines a single realtime ingress with scoped routing. The model is designed to prevent cross‑scope side effects, duplicate event handling, and UI‑dependent crypto/runtime behavior.

## 1) Scope Model Overview

We distinguish two categories of scopes:

### UI‑Scopes (visibility only)
UI‑scopes represent visible/active UI surfaces. They do **not** control realtime processing directly.

- `notifications_ui`
- `chat_list_ui`
- `chat_conversation_ui`
- `calls_ui`

Recommended binding:
- Use the `ScopeBoundary` component for template‑bound UI scopes.
- Or use `useUiScope(\"...\")` inside `setup()` for explicit control.
- With `keep-alive`, ensure `onActivated/onDeactivated` paths are handled.

### Operation‑Scopes (processing only)
Operation‑scopes control runtime processing, network traffic, and crypto state. They are activated by **operations**, not by UI presence directly.

- `notifications_feed_ops`
- `chat_list_ops`
- `conversation_ops` (per active conversation)
- `calls_ops`
- `file_transfer_ops`

**Rule:** UI‑scopes never directly drive network or crypto logic. Operations activate operation‑scopes.

## 2) Ownership by Plugin

Each operation‑scope has a single owner. Only the owner may process and mutate domain state for that scope.

### Notifications (Owner: notifications plugin)
- Owns `notifications_feed_ops`
- Responsibilities: feed loading, invite display, delegating actions.
- Must **not** perform call/chat domain logic.

### Chat (Owner: chat/vue‑chat)
- Owns `chat_list_ops` and `conversation_ops`
- Responsibilities: conversation summary, history, typing, read receipts, conversation‑MLS.

### Calls (Owner: calls plugin)
- Owns `calls_ops`
- Responsibilities: call join/leave, call session state, MLS control conversation, media key exchange.
- Ops activation is handled by the calls runtime/owner (not by the UI component).

### File Transfer (Owner: file‑transfer plugin)
- Owns `file_transfer_ops`
- Responsibilities: transfer handshake, file key exchange, chunk pipeline.

## 3) Realtime Ingress Design

**Invariant:** There is exactly one realtime ingress (WebSocket runtime). The ingress:

1. Receives all frames.
2. Emits a unified internal event.
3. Routes frames to modules based on **active operation‑scopes**.

No plugin may attach a competing runtime to the WebSocket. All event handling is performed by modules registered with the ingress router.

## 4) Delegation Model (Notifications → Operations)

Notifications are UI‑only. They **delegate** operations to domain owners.

Example: Call invite accept

1. Notifications UI emits `request_operation(call_join, { callSessionId, mediaE2eeRequired })`.
2. Calls plugin (owner) receives the request.
3. Calls plugin activates `calls_ops`.
4. Calls plugin executes join, MLS control, media‑key exchange.

Notifications never run call logic; they only route the request.

## 5) Operation‑Based Activation

Operations are the only trigger for runtime activation. They are independent of UI path.

Examples:

- `call_join` operation always activates `calls_ops` first.
- `open_conversation` activates `conversation_ops` for the target conversation.
- `start_file_transfer` activates `file_transfer_ops` for the transfer lifecycle.
- Incoming domain events may also trigger an operation (e.g., `file_transfer_offer` → activate `file_transfer_ops`).

Result: the same operation behaves identically whether initiated from notifications, chat UI, or calls UI.

## 6) Data Scope Rules

### notifications_feed_ops
- Load: notification feed, invites, minimal labels.
- No global users, no history, no MLS.

### chat_list_ops
- Load: conversation summaries, unread counts, membership state.
- No message history.

### conversation_ops
- Load: messages, typing, read receipts, attachments.
- MLS per conversation only.

### calls_ops
- Load: call session state, call control conversation, media keys, participants.
- No chat history.

### file_transfer_ops
- Load: file transfer meta, MLS file control (if used), chunks.
- No chat/calls domain data.

## 7) Invariants

1. Exactly one realtime ingress.
2. No plugin attaches a competing WebSocket runtime.
3. UI‑scopes are visual only; operation‑scopes drive processing.
4. Each operation‑scope has a single owner.
5. Operations are path‑independent and activate required scopes.
6. MLS/recovery/crypto never depends on UI visibility.
7. Data loading is minimal and scope‑bound.

## 8) Implementation Notes (Non‑Functional)

- Modules must register with the central ingress router.
- Modules may only process frames when their operation‑scope is active.
- All request/response flows must use the central ingress pipeline.
- Any feature needing realtime data must activate its operation‑scope explicitly.
