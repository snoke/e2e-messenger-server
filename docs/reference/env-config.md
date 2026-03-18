# Environment / Config Reference

This file consolidates runtime configuration entry points.

## Source of Truth
- [`docker-compose.yaml`](../../docker-compose.yaml)
- [`docker-compose.websocket.yaml`](../../docker-compose.websocket.yaml)
- [`docker-compose.realtime-core.yaml`](../../docker-compose.realtime-core.yaml)
- [`docker-compose.http3.yaml`](../../docker-compose.http3.yaml)

## Common Environment Variables
- `WS_GATEWAY_BASE_URL`
- `WS_GATEWAY_API_KEY`
- `VITE_REALTIME_TRANSPORT`
- `LIVEKIT_URL`
- `VITE_LIVEKIT_URL`
- `VITE_WS_URL`
- `WEBAUTHN_RP_ID` (e.g., `localhost` for dev)

## Notes
- Local dev typically uses WebSocket overlay.
- Core mode requires `symfony-consumer`.
- HTTP/3 mode requires certs and WebTransport support.
- WebAuthn requires a secure context (HTTPS or localhost).
