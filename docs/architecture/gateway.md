# Gateway Architecture

## Scope
Rust gateway for realtime transport, routing, and relay. It is **not** authoritative for domain state.

## Key Responsibilities
- Authenticate connections (JWT).
- Enforce the command registry (routing class + message type).
- Route inbound frames to the correct backend path or relay.
- Fan out outbound events to the correct subjects.

## Routing Model
Routing classes are defined in [`gateway/rust-http3-gateway/src/routes.rs`](../../gateway/rust-http3-gateway/src/routes.rs).
- `preauth` for auth/bootstrap.
- `gateway_local` for technical messages.
- `relay_hotpath` for low-latency relays.
- `backend_control` for authoritative commands.

## Registry Rules
- Every command must be registered.
- Unknown commands are rejected.
- Relay commands must declare authorization rules.

## Runtime State
- Connection state is tracked in-memory.
- Subjects are derived from auth and membership.
- Gateway performs minimal validation only.

## Transport Modes
- WebSocket in dev.
- WebTransport (HTTP/3) in advanced setups.

## Related
- Routing registry: [`docs/reference/routing-registry.md`](../reference/routing-registry.md)
- Realtime standard: [`docs/architecture/realtime-architecture.md`](realtime-architecture.md)