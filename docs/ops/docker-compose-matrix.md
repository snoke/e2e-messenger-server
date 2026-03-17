# Docker Compose Matrix

| Use Case | Compose Files | Notes |
|---|---|---|
| Default WS dev | `docker-compose.yaml` + `docker-compose.websocket.yaml` | Recommended for local dev |
| WS core mode | `docker-compose.yaml` + `docker-compose.websocket.yaml` + `docker-compose.realtime-core.yaml` | Requires consumer |
| HTTP/3 / WebTransport | `docker-compose.yaml` + `docker-compose.http3.yaml` | Requires cert setup |

Notes:
- Overlays are additive and must be combined with base compose.
- `frontend` may be optional if running UI separately.
