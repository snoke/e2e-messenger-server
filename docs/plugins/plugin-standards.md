# Plugin Standards

These rules apply to all frontend plugins.

## Core Rules
- Plugins do not access websocket directly.
- Each plugin has a single domain service for realtime ingress/egress.
- Only the owning plugin mutates domain state.
- Notifications only delegate, never execute domain logic.

## Required Structure
- UI components
- Domain service
- Optional adapters

## Scope Use
- UI scopes are visibility only.
- Operation scopes drive processing.

Related:
- `docs/reference/scopes.md`
- `docs/architecture/frontend.md`
