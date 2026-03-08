# ADR: Data Sync Standard (Realtime Stack)

## Status
Accepted

## Context
The stack has multiple state layers:
- browser-local cache (`IndexedDB`)
- realtime transport/cache infrastructure (`Redis`)
- persistent database (`MySQL`)

Without a strict contract, multi-device behavior becomes inconsistent.

## Decision
### 1) Source of truth
- `MySQL` is the canonical persistence layer for all cross-device business data.
- `Redis` is transient only (pub/sub, queue, presence, replay/cache), never canonical.
- `IndexedDB` is client-local cache and offline acceleration, never canonical.

### 2) Write path
- All writes go through backend handlers (WebSocket/WebTransport or API endpoint).
- Backend persists to MySQL first.
- After successful persistence, backend emits fanout events to user sessions.

### 3) Read/init path
- Client requests snapshot data explicitly (`request -> response`).
- Snapshot response is loaded from MySQL.
- Incremental realtime events apply after snapshot.

### 4) Correlation
- Client request/response messages use `request_id`.
- Session-aware flows additionally carry `session_id` and `client_instance_id`.
- Event handlers must ignore mismatched/late correlated responses.

### 5) Local cache
- Client caches server state in IndexedDB.
- On connect/reconnect, server snapshot refreshes cache.
- Cache miss must never block server-driven truth recovery.

### 6) Conflict handling
- Use explicit monotonic metadata (`updated_at` or version fields).
- Backend decides final state; client never resolves conflicts autonomously across devices.

## Consequences
- Multi-device semantics are deterministic.
- Reconnect/state recovery remains robust.
- Local caches improve UX but cannot diverge permanently from server truth.
- Redis outages or warmup phases do not redefine business truth.
