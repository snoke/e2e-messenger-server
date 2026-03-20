# Dev Status Snapshot (2026-03-07)

This is a historical snapshot. For current dev instructions and state, use:
- [`docs/ops/local-dev.md`](../ops/local-dev.md)
- [`docs/ops/docker-compose-matrix.md`](../ops/docker-compose-matrix.md)

## Repository

- Root repo: `e2e-messenger-server`
- Branch: `main`
- Root commit: `b774c91` (`disable consumer debug`)

## Submodules

- `frontend`: `dfdb642` (`MLS runtime hardening and secure store updates`)
- `symfony`: `64db9e6` (`Add membership state semantics for MLS group flow`)
- [`gateway/rust-http3-gateway`](../../gateway/rust-http3-gateway): `2fd5ccc`

## Current Runtime Defaults

- Chat protocol path: MLS (`ts-mls` adapter) for group content.
- Streaming media E2EE toggle is enabled in `.env`:
  - `VITE_CALL_MEDIA_E2EE_ENABLED=true`
- Active transport for local dev is typically WebSocket overlay; HTTP/3 (WebTransport) remains optional/experimental.

## Important Ops Change

- Symfony consumer runs without debug to avoid memory blowups from debug collectors:
  - command: `php -d memory_limit=512M bin/console ws:consume --no-debug`
  - root commit carrying this change: `b774c91`

## Recently Stabilized

- Sequential init flow hardening and request correlation handling.
- MLS group onboarding/membership semantics (`member_states`, membership status propagation).
- Frontend handling for pending memberships and guarded history auto-requests.
- Secure client storage migration path (WebCrypto-backed persistence updates).

## Known Open Validation Focus

- Group Add/Join/History semantics under reload and race conditions:
  - Inviter sends messages before invite acceptance.
  - Invitee transitions from pending to active and receives decryptable history from `history_visible_from`.
  - No premature `messages_request` side-effects while membership is pending.
- Cross-browser behavior for streaming E2EE profile fallback.

## Local Start (WebSocket stack)

```bash
docker compose -f docker-compose.yaml -f docker-compose.realtime-core.yaml -f docker-compose.websocket.yaml up -d
```

## Local Start (HTTP/3 stack)

```bash
docker compose -f docker-compose.yaml -f docker-compose.realtime-core.yaml -f docker-compose.http3.yaml up -d
```
