# Realtime Communication Architecture (Standard)

Status: Binding architecture standard for new features.
Scope: Frontend plugins, Gateway routing, Symfony realtime handlers, and event delivery back to frontend.

This document defines the **target standard** (Soll-Zustand). New features must follow this flow end-to-end.

References:
- Scopes.MD (frontend scope model)
- workflow-protocol.md (live vs committed semantics)
- gateway/rust-http3-gateway/src/routes.rs (RoutingClass and MessageSemanticType)
- gateway/rust-http3-gateway/src/project/command_registry.rs (command registry and relay auth)

---

## 1) Frontend Plugin Model

### 1.1 Plugin Structure (Standard)
A frontend plugin is organized into:
- UI components (views, panels, modals)
- A **single domain service** responsible for outbound requests and inbound events
- Optional adapters to shared core messaging APIs
- No direct websocket usage; all realtime flows go through the central messenger ingress

### 1.2 Ownership Rules (Non-Negotiable)
Owners are the only modules allowed to mutate domain state and issue domain commands.

- Notifications: UI + feed + delegation only
- Calls: owner for call flow, MLS control conversation, media key exchange
- Chat: owner for conversation list, history, typing, read receipts, conversation MLS
- File-Transfer: owner for transfer flow and relay hotpath

### 1.3 UI-Scopes vs Operation-Scopes
- UI-scopes only reflect visibility
- Operation-scopes drive processing and network traffic
- UI-scopes never enable crypto or request data directly

See Scopes.MD for the definitive list of scopes and scope rules.

### 1.4 Allowed Requests / Responses per Plugin
- Each plugin may **send only commands/queries within its owned domain**
- Each plugin may **consume only events relevant to its owned domain and active scopes**
- Cross-domain data access is forbidden (no call logic in notifications, no chat history in calls, etc)

### 1.5 Delegation Rules
- Notifications may emit `request_operation(...)` only
- Domain owners (chat/calls/file-transfer) activate operation-scopes and execute the flow
- Delegation is one-way; notifications never execute domain logic
  - Calls ops are activated by the calls owner/runtime, not by the UI component

### 1.6 Frontend Operation Dispatch (Explicit)
Operation requests are routed via exactly one dispatcher.

- Exactly one **operation dispatcher** exists in the frontend.
- All `request_operation(...)` calls go through this dispatcher.
- The dispatcher routes operations to the **owning plugin**.
- No ad-hoc cross-plugin event wiring is allowed.
- Operation dispatch is separate from realtime ingress.

### 1.7 Explicitly Forbidden
- Creating a parallel realtime ingress or websocket client
- Handling MLS or call control in notifications
- Loading full conversation history from list scope
- Global users or global presence in notification scope
- Deriving notifications from unrelated responses

---

## 2) Command / Query / Event Model

### 2.1 Definitions
- **Command**: Mutates server state or triggers a domain action
- **Query**: Requests data, does not mutate state
- **Event**: Server-to-client published domain fact
- **Signal**: Realtime control payload not persisted as domain truth.
  - Signals may be transient.
  - Signals must not be used as primary UI truth.
  - Signals must not be reconstructed into notifications or domain state.

### 2.2 Naming Rules (Standard)
- Commands: `<domain>_<verb>` (e.g., `call_session_join`)
- Queries: `<domain>_<noun>_request` (e.g., `chat_conversations_request`)
- Responses:
  - `*_ok` / `*_error` for request responses
  - `*_state`, `*_invited`, `*_committed` for authoritative events
  - Query results use stable domain naming: either collection-style (`messages`, `conversations`, `notifications`) or explicit `*_response`, but never mixed per domain.

### 2.3 Required Envelope Fields
At minimum:
- `type`
- `request_id` for commands/queries
- `conversation_id` or `call_session_id` when scoped
- `ts` or `ts_client`
- `message_id` when dedupe is required

### 2.4 Follow-up Events
Allowed:
- `*_ok`, `*_error`, `*_state`, `*_invited`, `*_committed`
Disallowed:
- Events that replicate unrelated domain data
- Notifications inferred from domain responses (notifications must come from notifications feed)

---

## 3) Gateway Routing Model

Routing classes are defined in `gateway/rust-http3-gateway/src/routes.rs`.

### 3.1 Routing Classes
- **RoutingClass::NoAuth** (preauth)
  - Used for auth and bootstrap
  - Technical messages only
- **gateway_local** (`RoutingClass::GatewayLocal`)
  - Local utility commands (e.g., ping)
  - Technical messages only
- **relay_hotpath** (`RoutingClass::RelayHotpath`)
  - Low-latency peer relay; requires relay auth metadata
  - Must be scoped and guarded
- **backend_control** (`RoutingClass::BackendControl`)
  - Authoritative domain commands/queries
  - Non-technical message types

### 3.2 Registry Requirements
Every new command must be registered in:
- `COMMAND_REGISTRY` with:
  - `command_name`
  - `routing_class`
  - `message_type` (command/query/signal/technical)
  - `mirror_to_backend` (optional; only when explicitly required)

Relay commands **must** also be registered in:
- `RELAY_AUTHORIZATION_REGISTRY` with:
  - `requires_relay_context`
  - `relay_context_type`
  - `audience_scope_mode`
  - `guard_class`
  - `command_family`
  - `operation_key_field`

### 3.3 Targeting Rules
- **backend only**: BackendControl (authoritative)
- **self-targeted**: only for request responses and acks
- **targeted clients**: derived from domain membership or explicit relay context
- **conversation-scoped**: use conversation_id and server-owned membership
- **broadcast**: only if domain truth requires it

No implicit routing fallbacks. If routing cannot be resolved, the command must fail visibly.

---

## 4) Backend Realtime Model (Symfony)

### 4.1 Handler Layers
- **MessageHandler Registry**: maps command to handler
- **Handler**: input validation, auth, mapping to use case
- **Use Case / Service**: domain logic and state mutation
- **Publisher**: emits realtime events to gateway

### 4.2 Ownership and Truth
- Symfony is the single source of truth for persisted state
- Gateway is transport and routing, not domain logic

### 4.3 Response and Event Rules
- Responses must be scope-minimal
- No unrelated payload fields
- No notification reconstruction from other responses

### 4.4 Standard Response Patterns
- Queries reply with stable domain response types:
  - collection-style (`messages`, `conversations`, `notifications`) or
  - explicit `*_response` where the domain already uses it.
- Commands reply with `*_ok` or `*_error`
- Domain updates publish `*_state` or `*_committed`

---

## 5) Scope and Visibility Rules

Visibility is governed by the operation scopes defined in Scopes.MD.

### Scope Rules (Summary)
- notifications scope: notification feed and invites only
- chat list scope: conversation summaries only
- conversation scope: messages, typing, read, attachments
- calls scope: call session state, control conversation, media keys
- file transfer scope: transfer handshake and chunks

Any payload that exceeds a scope is a contract violation.

---

## 6) End-to-End Example Flows

### a) notifications_request
- Owner: notifications
- Request: `notifications_request`
- Gateway: BackendControl
- Symfony: NotificationsMessageHandlerRegistry -> notifications handler
- Response/Event: `notifications` payload and optional `notification_event`
- Scope: notifications_feed_ops only

### b) chat_conversations_request
- Owner: chat
- Request: `chat_conversations_request`
- Gateway: BackendControl
- Symfony: ChatMessageHandlerRegistry -> conversations handler
- Response/Event: `conversations`
- Scope: chat_list_ops only

### c) chat_messages_request
- Owner: chat
- Request: `chat_messages_request`
- Gateway: BackendControl
- Symfony: ChatMessageHandlerRegistry -> messages handler
- Response/Event: `messages`
- Scope: conversation_ops only

### d) Call invite accept (from Notifications)
- Owner: calls
- Notifications emits: `request_operation(call_join, { call_session_id })`
- Calls activates: calls_ops
- Calls sends: `call_session_join`
- Gateway: BackendControl
- Symfony: CallsMessageHandlerRegistry -> CallSessionAction
- Response/Event: `call_session_join_ok`, `call_session_state`, `call_session_token_ok`
- Scope: calls_ops only

### e) file_transfer_offer
- Owner: file-transfer
- Request: `file_transfer_offer`
- Gateway: RelayHotpath (relay auth required)
- Symfony: optional persistence / audit
- Response/Event: `file_transfer_offer` delivered to peer
- Scope: file_transfer_ops only

---

## 7) How to Add a New Feature (Mandatory Steps)

1. Define the **owner plugin** and its scope(s).
2. Define the operation(s) and data needs (minimal scope).
3. Define command/query/event contracts (names + payloads).
4. Register commands in the **gateway registry**.
5. Add relay auth metadata if relay hotpath is used.
6. Implement Symfony handler + use case + publisher.
7. Define response/event visibility per scope.
8. Wire the frontend owner through operation dispatcher.
9. Add contract checks / tests where applicable.
10. Update this document if new patterns are introduced.

## 8) Invariants (Binding Rules)

1. Each domain has exactly one owner plugin.
2. Notifications are UI + feed + delegation only.
3. UI-scopes never activate crypto or processing directly.
4. Operation-scopes drive all realtime processing.
5. Exactly one realtime ingress in frontend.
6. No competing websocket clients in plugins.
7. All commands are registered in the gateway registry.
8. Relay commands require relay auth metadata.
9. Payloads are scope-minimal; no domain leakage.
10. Notifications are never derived from other responses.
11. No implicit routing fallbacks.
12. New features must follow this document end-to-end.

---

## 9) MLS-Scoped Signal Pattern (Reusable)

This pattern formalizes MLS-bound operation contexts (e.g., Calls media-key control, File-Transfer control).
It is **not** intended for normal chat messages.

### 9.1 Minimal Model (Behavior)

- **Context established gate**: processing starts only when MLS context is ready.
- **Epoch-safe signaling**: outbound signals always include the **current** MLS epoch.
- **Stale signal drop**: inbound `incomingEpoch < localEpoch` is dropped.
- **Future epoch defer**: inbound `incomingEpoch > localEpoch` is queued.
- **Ready-triggered resend/flush**: when context is ready, queued signals are flushed and last state may be re-sent.

### 9.2 Minimal API (Pseudocode)

```ts
type ContextId = number;
type Epoch = number;

type EncryptedSignal = {
  contextId: ContextId;
  session_epoch: Epoch;
  ciphertext: string;
  nonce: string;
  suite: string;
  header: Record<string, unknown>;
};

type PlainSignal = Record<string, unknown>;

type MlsScopedChannel = {
  isReady: (contextId: ContextId) => boolean;
  ensureReady: (contextId: ContextId) => Promise<boolean>;
  send: (contextId: ContextId, payload: PlainSignal, reason?: string) => Promise<boolean>;
  onSignal: (contextId: ContextId, signal: EncryptedSignal) => Promise<void>;
  notifyReady: (contextId: ContextId) => void;
};

type MlsTransport = {
  getEpoch: (contextId: ContextId) => Epoch;
  encrypt: (contextId: ContextId, epoch: Epoch, payload: PlainSignal) => Promise<EncryptedSignal | null>;
  decrypt: (contextId: ContextId, epoch: Epoch, signal: EncryptedSignal) => Promise<PlainSignal | null>;
};
```

### 9.3 Usage Guidance

**Apply to:**
- Calls media-key control
- File-transfer handshake / file-key control
- Other MLS-bound operation contexts

**Do not apply to:**
- Standard chat message flow
- Notifications feed
