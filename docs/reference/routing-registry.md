# Routing Registry

Authoritative routing is defined in the gateway registry.

## Source of Truth
- `gateway/rust-http3-gateway/src/routes.rs`
- `gateway/rust-http3-gateway/src/project/command_registry.rs`

## Registry Invariants
- Unknown commands are rejected.
- Routing class must match domain intent.
- Relay commands must define explicit authorization guards.

## Validation
- When a new command is added, update registry tests or lint checks.
- Ensure frontend and backend agree on command names.

Related:
- `docs/reference/commands-events.md`
