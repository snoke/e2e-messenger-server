# Legacy Architecture Analysis (Context Only)

This file preserves historical analysis. It is **not** a source of truth for the current system.

## Current Reality (Quick Summary)
- Routing is governed by the gateway registry (`routes.rs`, `command_registry.rs`).
- Realtime is broker-first: gateway → Redis streams → Symfony consumer.
- MLS is used for live transport; CHK is used for history.
- Invite pre‑provisions CHK wraps; accept delivers the wrap.

For authoritative details, see:
- `docs/architecture/realtime-architecture.md`
- `docs/overview/system-behavior.md`
- `docs/crypto/README.md`
