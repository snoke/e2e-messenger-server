# CODEX.md

Working guide for contributors/agents in this repository.

## Scope
This repo is the integration layer around three submodules:
- `frontend` (Vue messenger client)
- `symfony` (backend + demo coordinator + consumer)
- `gateway/rust-http3-gateway` (transport gateway)

Most realtime bugs are cross-component. Always trace request/response across all three.

## Core Principles

### 1) Gateway blind-by-design
- Gateway should stay payload-blind for business content.
- Metadata inspection is allowed only for transport/runtime behavior (e.g. `request_id`, envelope `type`, subjects, connection/session scoping).
- Do not add business/domain branching in gateway.

### 2) Init is client-driven, sequential, correlated
- No protocol-level server bootstrap dependency.
- Client init sequence:
  - `users_request` -> `users` (+ `users_done` optional)
  - `contacts_request` -> `contacts` (+ `contacts_done` optional)
  - `conversations_request` -> `conversations` (+ `conversations_done` optional)
- One step in flight at a time.
- Every step request uses `request_id`.
- Matching responses must echo the same `request_id`.
- Retries reuse same `request_id`.

### 3) Push events are independent
- Push events (`presence`, `chat/messages`, typing, etc.) can arrive anytime.
- Push events must not reset/restart init.

### 4) Legacy bootstrap events are compatibility only
- `bootstrap_snapshot` and `bootstrap_done` may still be emitted.
- Treat them as idempotent legacy events.
- Never use them to trigger init progression or handshake restarts.

## Where To Change What

### Frontend
- Init orchestration: `frontend/src/Messenger/services/messenger/realtime/bootstrap.ts`
- Incoming history/messages handling: `frontend/src/Messenger/services/messenger/realtime/history.ts`
- Realtime transport abstraction: `frontend/src/Messenger/services/realtimeClient.ts`
- Transport implementations:
  - `frontend/src/Messenger/services/client/wsClient.ts`
  - `frontend/src/Messenger/services/client/wtClient.ts`

### Symfony
- Realtime event coordinator: `symfony/src/Messenger/Application/ChatDemoCoordinator.php`
- Request handlers for `*_request` and `*_done` are here.
- If init stalls, verify this file echoes `request_id` on both payload and done events.

### Gateway
- Broker dispatch/log semantics: `gateway/rust-http3-gateway/src/broker.rs`
- Dispatch/requeue mechanics: `gateway/rust-http3-gateway/src/state.rs`
- Transport specifics:
  - WebTransport: `gateway/rust-http3-gateway/src/transport/webtransport.rs`
  - WebSocket: `gateway/rust-http3-gateway/src/transport/websocket.rs`

## Dev Start Commands
WebSocket mode:
```bash
docker compose -f docker-compose.yaml -f docker-compose.realtime-core.yaml -f docker-compose.websocket.yaml up -d
```

HTTP/3 mode:
```bash
docker compose -f docker-compose.yaml -f docker-compose.realtime-core.yaml -f docker-compose.http3.yaml up -d
```

## Debug Workflow (Init Issues)
1. Check browser log for `init.step.request` / `init.step.done`.
2. Confirm same `request_id` on:
   - `users` and `users_done`
   - `contacts` and `contacts_done`
   - `conversations` and `conversations_done`
3. Confirm out-of-order/old responses are ignored (expected after reconnect).
4. Check gateway logs for session churn (`auth_timeout`, `connection closed by peer`).
5. Validate Symfony actually emits the expected step response for current request.

## Logging Semantics
Use explicit delivery language:
- `attempted`: dispatch/send was attempted
- `enqueued`: accepted into outbound queue/channel
- `transport accepted` (if logged): transport send succeeded

Avoid conflating internal dispatch with client-level delivery acknowledgment.

## Transport Guidance
- Default local dev: `websocket` (more stable across browsers)
- HTTP/3/WebTransport: targeted testing path
- Firefox WebTransport behavior is currently not a stable baseline

## Definition Of Done For Realtime Changes
- Works after fresh login and after browser reload.
- No infinite init retry loop.
- Init reaches ready with correlated step responses.
- Duplicate/late responses do not break state.
- Legacy bootstrap duplicates do not trigger re-init.
- No regressions for sender-keys handshake flow.
