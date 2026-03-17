# Local Development

## Quick Start (Recommended)
Start the full realtime stack (includes Redis + consumer):

```
docker compose -f docker-compose.yaml -f docker-compose.websocket.yaml -f docker-compose.realtime-core.yaml up -d --build symfony gateway frontend symfony-consumer redis
```

Then open the frontend at `http://localhost:5173`.

## Quick Start (Minimal / Manual)
If you do not include [`docker-compose.realtime-core.yaml`](../../docker-compose.realtime-core.yaml), you **must** run these separately:
- `redis`
- `symfony-consumer`

Example (manual services already running):
```
docker compose -f docker-compose.yaml -f docker-compose.websocket.yaml up -d --build symfony gateway frontend
```

## Required Services (WebSocket default)
- `gateway`
- `symfony`
- `symfony-consumer`
- `redis`
- `mysql`
- `frontend`

## Common Commands
- Logs: `docker compose -f [docker-compose.yaml](../../docker-compose.yaml) -f [docker-compose.websocket.yaml](../../docker-compose.websocket.yaml) logs -f symfony`.
- Consumer logs: `docker compose -f [docker-compose.yaml](../../docker-compose.yaml) -f [docker-compose.websocket.yaml](../../docker-compose.websocket.yaml) logs -f symfony-consumer`.

## Notes
- `symfony-consumer` is required for realtime command handling.
- If consumer is down, requests like `user_vault_fetch` will time out.