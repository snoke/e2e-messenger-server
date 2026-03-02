# SymfonyRealtime Stack (Configurable)

This stack provides bidirectional, highly scalable realtime transport for Symfony

## Why this stack exists
- Mercure / SSE are server→client only — forcing client updates creates massive overhead
- Pusher / SaaS solutions are convenient, but your data, presence, security, and GDPR compliance are hosted externally
- High connection counts make booting full Symfony per WebSocket message inefficient
- This architecture allows true E2E encryption with full self-hosting control (keys never leave the clients). The gateway payload stays blind by design — unlike many PHP-centric WS stacks (e.g., Swoole) that couple transport and business logic in the same runtime — while still keeping the integration Symfony-native.

## Modes & Routing
- `core` (broker-first): stateless HTTP/3 WebTransport gateway with Redis streaming; Symfony acts as producer/consumer
- Terminator/WebSocket mode is deprecated in this stack (kept only for legacy experiments).


## Quick Start
1. Clone this repo:
   ```
   git clone https://github.com/snoke/Symfony-Realtime-Stack.git
   cd Symfony-Realtime-Stack
   ```
2. Install submodules:
   ```
   # HTTP/3 gateway
   git submodule update --init gateway/rust-http3-gateway
   ```
   ```
   # Frontend (Vue) optional
   git submodule update --init frontend
   ```
3. Generate dev keys (RS256):
   ```
   ./scripts/gen_dev_keys.sh
   ```
4. Generate HTTP/3 dev certs:
   ```
   ./gateway/rust-http3-gateway/scripts/gen_dev_certs.sh
   ```
5. (Optional, recommended) Pin the dev cert for WebTransport:
   ```
   CERT_HASH=$(openssl x509 -in gateway/rust-http3-gateway/certs/dev_cert.pem -outform der | openssl dgst -sha256 -binary | base64)
   ```
6. Start (core mode + HTTP/3 gateway):

   ```
   VITE_WT_CERT_HASH="${CERT_HASH}" \
   docker compose -f docker-compose.yaml -f docker-compose.realtime-core.yaml -f frontend/docker-compose.yaml up --build
   ```

   Note: The HTTP/3 gateway is built directly from `gateway/rust-http3-gateway`.
   If you don't want the Vue UI, drop the `frontend/docker-compose.yaml` file.
7. Verify:
   - API: `http://localhost:8180/api/ping`
   - WebTransport endpoint (HTTP/3): `https://localhost:4433/`
   - Frontend (Vue): `http://localhost:5173/auth/login`
   - LiveKit signaling: `ws://localhost:7880`
   - TURN/STUN: `stun:localhost:3478`, `turn:localhost:3478`

## Calls (LiveKit SFU)
- SFU is provided by a dedicated `livekit` service (not the chat gateway).
- Room mapping is deterministic: `room_id = conversation_id`.
- Access token endpoint: `GET /api/calls/token?conversation_id={id}`.
- Symfony validates JWT + conversation membership before returning a short-lived LiveKit token.
- TURN/STUN uses coturn (`3478` + relay range) and is also passed to the frontend WebRTC config.

### Signaling Layer
- Chat/E2EE payloads remain unchanged.
- Call signaling is separated as dedicated realtime events:
  - `call_join`
  - `call_leave`
  - `call_mute`
  - `call_camera`

### Env Variables
- `LIVEKIT_URL` (e.g. `ws://localhost:7880` in dev, `wss://...` in prod)
- `LIVEKIT_API_KEY`
- `LIVEKIT_API_SECRET`
- `LIVEKIT_TOKEN_TTL`
- `VITE_LIVEKIT_URL`
- `VITE_WEBRTC_STUN_URL`
- `VITE_WEBRTC_TURN_URL`
- `VITE_WEBRTC_TURN_USERNAME`
- `VITE_WEBRTC_TURN_PASSWORD`
- `VITE_CHAT_MAX_VIDEO_SIZE_BYTES`
- `VITE_CHAT_MAX_VIDEO_DURATION_SECONDS`
- `CHAT_MAX_VIDEO_SIZE_BYTES`
- `CHAT_MAX_VIDEO_DURATION_SECONDS`

## Browser Flags (WebTransport)
Chrome / Edge:
- `chrome://flags` → enable `#webtransport-developer-mode` and `#enable-quic`

Firefox:
- WebTransport is still experimental. Use Firefox Nightly and set `network.webtransport.enabled=true`.

## Messenger E2EE State (Current)
- Frontend transport is WebTransport/HTTP3 only; legacy WS path is deprecated.
- E2EE session handling is **conversation-first** with strict `conversation_id + session_epoch`.
- Handshake orchestration is split into dedicated modules:
  - `frontend/src/Messenger/services/messenger.handshake.ts`
  - `frontend/src/Messenger/services/messenger.pipeline.ts`
  - `frontend/src/Messenger/services/messenger.transport.ts`
- Deterministic recovery flow on decrypt problems:
  - `established -> stale -> rekeying -> established`
- Buffered encrypted messages are reprocessed after recovery in a controlled, single-pass manner.

Known UX limitation:
- Starting a new chat currently opens the conversation + handshake first; an initial message cannot yet be atomically submitted in the same action before the peer session is established.
