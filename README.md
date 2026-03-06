# Symfony Realtime Stack

Self-hosted realtime messenger stack for Symfony with end-to-end encryption, Redis stream core, and selectable transport (`websocket` or `http3/webtransport`).

## Current State (March 2026)
- Core mode is broker-first: client events go through gateway -> Redis (`ws.inbox`) -> Symfony consumer.
- Outbound events go Symfony -> Redis (`ws.outbox`) -> gateway -> clients.
- Group crypto default is `sender_keys` (MLS hooks still exist but are not the default path).
- Client init uses a sequential contract (`users -> contacts -> conversations`) with `request_id` correlation.
- Legacy `bootstrap_snapshot/bootstrap_done` can still arrive and are treated as compatibility events only.

## Architecture
- `frontend/`: Vue/Vite messenger client (E2EE, transport adapters, init orchestrator)
- `gateway/rust-http3-gateway/`: Rust gateway for WebSocket and WebTransport
- `symfony/`: Symfony API + demo coordinator + realtime consumer
- `redis`: broker backbone for realtime inbox/outbox/events
- `mysql`: app persistence
- `coturn` + `livekit`: calls/media stack

## Quick Start

### 1. Init submodules
```bash
git submodule update --init --recursive
```

### 2. Create dev JWT keys
```bash
./scripts/gen_dev_keys.sh
```

### 3. (Only for HTTP/3) Create dev certs
```bash
./gateway/rust-http3-gateway/scripts/gen_dev_certs.sh
```

### 4. Start stack

Recommended local default (WebSocket):
```bash
docker compose -f docker-compose.yaml -f docker-compose.realtime-core.yaml -f docker-compose.websocket.yaml up -d
```

HTTP/3 / WebTransport:
```bash
docker compose -f docker-compose.yaml -f docker-compose.realtime-core.yaml -f docker-compose.http3.yaml up -d
```

Optional for Chromium WebTransport cert pin:
```bash
CERT_HASH=$(openssl x509 -in gateway/rust-http3-gateway/certs/dev_cert.pem -outform der | openssl dgst -sha256 -binary | base64)
export VITE_WT_CERT_HASH="$CERT_HASH"
```

### 5. Open services
- Frontend: `http://localhost:5173/auth/login`
- Symfony API ping: `http://localhost:8180/api/ping`
- Gateway internal API: `http://localhost:8081/health`
- WebSocket endpoint: `ws://localhost:8080/ws`
- WebTransport endpoint: `https://127.0.0.1:4433/`
- phpMyAdmin: `http://localhost:8181`
- LiveKit signaling: `ws://localhost:7880`

## Transport Matrix (Local Dev)
- `Chrome + WebSocket`: stable (recommended default)
- `Firefox + WebSocket`: stable
- `Chrome + HTTP/3 WebTransport`: usable for targeted tests
- `Firefox + HTTP/3 WebTransport`: experimental/unstable, not default for daily dev

## Realtime Init Contract
The client owns initialization as a step-by-step state machine:
1. `users_request` -> `users` (+ optional `users_done`)
2. `contacts_request` -> `contacts` (+ optional `contacts_done`)
3. `conversations_request` -> `conversations` (+ optional `conversations_done`)

Rules:
- exactly one init step in flight
- every step request carries `request_id`
- responses must echo `request_id`
- retries resend the same `request_id`
- legacy bootstrap events must not restart init or trigger handshake flows

## Known Caveats
- Unread handling is currently message/read-event driven; there is no dedicated server-side channel-state snapshot API yet.
- If a backend response misses `request_id`, the client intentionally ignores it during init.
- Duplicate connect/auth log lines can happen during hot-reload/browser reload phases; one active client instance per tab is expected after settle.

## Useful Commands
Tail gateway logs:
```bash
docker compose -f docker-compose.yaml -f docker-compose.realtime-core.yaml -f docker-compose.websocket.yaml logs -f gateway
```

Stop stack:
```bash
docker compose -f docker-compose.yaml -f docker-compose.realtime-core.yaml -f docker-compose.websocket.yaml down
```

## Repository Layout
- `docker-compose*.yaml`: base + overlays (`realtime-core`, `websocket`, `http3`)
- `scripts/`: keygen, smoke checks, helper scripts
- `docs/archive/`: old docs kept for reference only
