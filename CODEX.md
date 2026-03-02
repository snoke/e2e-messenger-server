# CODEX.md — Symfony Realtime Stack (HTTP/3 + E2EE)

This file is a fast on‑ramp for a new Codex model. It summarizes the project, architecture, crypto design, and current status.

## What This Repo Is
A self‑hosted realtime stack for Symfony with **HTTP/3 WebTransport** and **end‑to‑end encryption**. The gateway is **blind by design**: it forwards encrypted events and never sees plaintext.

Key goals:
- WebTransport over HTTP/3 (QUIC) instead of WebSocket
- Broker‑first “core” mode (Redis streams)
- E2EE with Double Ratchet
- Optional post‑quantum KEX (Kyber768)

## Project Layout (Top-Level)
- `frontend/` — Vue/Vite messenger UI (submodule)
- `gateway/rust-http3-gateway/` — Rust HTTP/3 WebTransport gateway (submodule, current)
- `gateway/gateway-rust/` — legacy WS gateway (kept but not used)
- `symfony/` — Symfony backend (JWT auth, DB, consumers)
- `scripts/` — helper scripts (dev keys, smoke tests, etc.)
- `docker-compose.yaml` — base services
- `docker-compose.realtime-core.yaml` — core mode services (Redis, consumer)
- `docker-compose.brokers.yaml` — extra brokers (e.g. RabbitMQ)
- `frontend/docker-compose.yaml` — Vite dev container

## Runtime Architecture (Core Mode)
**Core mode = broker‑first**

Flow:
1. **Frontend** opens WebTransport session to the gateway (`https://localhost:4433/`).
2. **Gateway (Rust HTTP/3)** terminates TLS/QUIC and forwards events to Redis streams.
3. **Symfony** consumes Redis inbox/outbox and handles persistence / API.
4. **Gateway** pushes events back to clients.

Redis streams used by gateway:
- `ws.inbox`  — incoming from clients
- `ws.outbox` — outgoing to clients

Symfony is the producer/consumer, the gateway is transport‑only.

## Transport: WebTransport (HTTP/3)
- Client: `frontend/src/Messenger/services/client.ts`
- Gateway: `gateway/rust-http3-gateway/src/*`
- Auth: first frame `{type:"auth", token:"..."}`
- Framing: JSON events over a bidirectional stream

Dev certs:
- `./gateway/rust-http3-gateway/scripts/gen_dev_certs.sh`
- WebTransport requires cert pin in dev via `VITE_WT_CERT_HASH`

## E2EE Overview
Encryption lives entirely in the frontend.

Key files:
- `frontend/src/Messenger/crypto/engine.ts` — Double Ratchet + session mgmt
- `frontend/src/Messenger/crypto/prekeys.ts` — identity + signed prekeys
- `frontend/src/Messenger/crypto/types.ts` — profile metadata
- `frontend/src/Messenger/crypto/strategies/*` — KEX strategies
- `frontend/src/Messenger/services/messenger.ts` — orchestration entrypoint
- `frontend/src/Messenger/services/messenger.handshake.ts` — handshake state machine/coordinator
- `frontend/src/Messenger/services/messenger.pipeline.ts` — inbound decrypt policy + buffering/reprocessing
- `frontend/src/Messenger/services/messenger.transport.ts` — normalized send helpers (open/chat/typing)

### Crypto Profiles
Defined in `frontend/src/Messenger/crypto/types.ts`:
- `x25519_chacha20_hkdf_dr`
- `x25519_kyber768_chacha20_hkdf_dr`

Suites:
- KEX: X25519 (optionally + Kyber768)
- AEAD: ChaCha20‑Poly1305
- KDF: HKDF‑SHA256 (concat for Kyber)
- Ratchet: Double Ratchet

### Identity + Prekeys
Storage is **local browser storage** (per device):
- Identity key: Ed25519 (signs signed prekeys)
- Signed prekeys: X25519 (+ optional Kyber) stored as a **ring (last 3)**
- One‑time prekeys: not implemented (optional future)

`prekey_bundle` includes:
- `identity_pub`
- `signed_prekey_pub`
- `signed_prekey_id`
- `signature`
- `kyber_prekey_pub` (when Kyber profile)

### Handshake Messages
Core E2EE events:
- `crypto_init`  — initiator sends KEX public(s)
- `crypto_reply` — receiver responds with KEX reply
- `prekey_bundle` — server side lookup when peer is offline

### Offline Messaging Design (Target)
- When peer offline, initiator requests a **prekey bundle** and bootstraps session.
- Ratchet state persisted locally to allow decrypt after reconnection.

## Current State / Known Issues
E2EE is functional in-session. Current design is conversation-first with strict epoch semantics.

### Latest fixes (2026-03-02)
- **Gateway frame truncation fixed**:
  - File: `gateway/rust-http3-gateway/src/webtransport_server.rs`
  - Change: switched bidirectional stream read from single `read(...)` to `read_to_end(...)`.
  - Why: large `crypto_init` / `crypto_reply` payloads (Kyber) were truncated, parsed as `type:"raw"`, and never reached Symfony as real crypto events.
- **Messenger service decoupling**:
  - Files: `frontend/src/Messenger/services/messenger.handshake.ts`, `frontend/src/Messenger/services/messenger.pipeline.ts`, `frontend/src/Messenger/services/messenger.transport.ts`, `frontend/src/Messenger/services/messenger.ts`
  - Handshake state machine, inbound decrypt pipeline, and send transport were separated from the monolithic orchestrator.
- **Strict E2EE invariants**:
  - Decrypt policy now enforces `conversation_id + session_epoch` as primary gate.
  - Silent legacy/fallback decrypt paths were reduced/removed in history and live message flow.
- **Deterministic recovery flow**:
  - Explicit transitions: `established -> stale -> rekeying -> established`.
  - Buffered inbound messages are retried after a successful state transition via established-version gating (no ad-hoc reset loops).
- **WebTransport STOP_SENDING handling**:
  - File: `frontend/src/Messenger/services/client.ts`
  - Read loops now handle `STOP_SENDING` gracefully to avoid uncaught promise errors in console.
- **History behavior hardened**:
  - File: `frontend/src/Messenger/services/messenger.ts`
  - Messages without `session_epoch` are dropped from decrypt attempts.
  - History decrypt failures are buffered + recovered through defined state-machine transitions.

### Still important when testing
- If DB `messages` / `conversations` is cleared but browser storage is kept, ratchet/session mismatch is expected.
- For clean E2EE tests after DB resets: clear browser local storage for both users.
- Use debug logs in `messenger.ts` (`handshake.*`, `decrypt.*`, `messages.*`) to classify failures:
  - transport delivery,
  - handshake state machine,
  - ratchet/session mismatch.

## Message/Event Types (Gateway → Client)
Common payload types:
- `auth_ok`
- `presence`, `presence_state`
- `users`, `contacts`, `conversations`, `messages`
- `chat`, `typing`, `read`
- `crypto_init`, `crypto_reply`, `prekey_bundle`

## How To Run (Dev)
From repo root:
```
./scripts/gen_dev_keys.sh
./gateway/rust-http3-gateway/scripts/gen_dev_certs.sh

CERT_HASH=$(openssl x509 -in gateway/rust-http3-gateway/certs/dev_cert.pem -outform der | openssl dgst -sha256 -binary | base64)

VITE_WT_CERT_HASH="$CERT_HASH" \
  docker compose -f docker-compose.yaml \
                 -f docker-compose.realtime-core.yaml \
                 -f frontend/docker-compose.yaml \
                 up --build
```

Endpoints:
- API: `http://localhost:8180/api/ping`
- WebTransport: `https://localhost:4433/`
- Frontend: `http://localhost:5173/auth/login`

## Development Notes
- Terminator/WebSocket mode is deprecated in this repo.
- The HTTP/3 gateway is the active path.
- If changing E2EE logic, **keep an eye on prekey bundle flow** and local state persistence.
- Known UX gap: conversation start is not yet “compose + send first message in one step”; currently conversation creation/handshake happens first.
