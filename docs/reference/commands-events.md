# Commands & Events Reference

This is a **reference index**; authoritative lists live in the gateway registry.

## Source of Truth
- `gateway/rust-http3-gateway/src/project/command_registry.rs`
- `gateway/rust-http3-gateway/src/routes.rs`

## How to Add a Command
1. Add the command to `COMMAND_REGISTRY` with routing class and message type.
2. If relay, add to `RELAY_AUTHORIZATION_REGISTRY`.
3. Implement Symfony action and handler.
4. Update frontend domain service.

## Message Types
- `command`
- `query`
- `signal`
- `technical`

## Naming Rules
- Commands: `<domain>_<verb>`
- Queries: `<domain>_<noun>_request`
- Responses: `*_ok`, `*_error`, `*_state`, `*_committed`

Related:
- Realtime standard: `docs/architecture/realtime-architecture.md`
- Scope model: `docs/reference/scopes.md`
