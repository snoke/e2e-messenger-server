# Component Ownership & Source of Truth

This document defines **who owns which data** and **where truth lives**. It prevents implicit coupling between components.

## Ownership Matrix

| Domain | Source of Truth | Runtime Owner | Notes |
|---|---|---|---|
| Auth Session | Symfony + Gateway | Gateway | JWT + connection auth state. |
| Vault State | Client + Symfony | Client | Server stores wraps only; client decrypts. |
| Conversations | Symfony | Symfony | Membership, roles, epochs, persistence. |
| MLS Live State | Client | Client | Device-local MLS state only. |
| CHK Wraps | Symfony (wrapped) | Client (plaintext) | Server stores wraps, client unwraps. |
| Notifications | Symfony + Client | Client | Server emits feed; client decides delivery channels. |
| Realtime Transport | Gateway | Gateway | Routing only, no domain truth. |
| Presence | Symfony (policy) | Gateway + Symfony | Gateway sees connections, Symfony applies contact scoping. |

## Rules
- Server never stores plaintext secrets.
- Gateway never mutates domain state.
- Client never mutates membership or persistence state directly.

## Related
- `docs/overview/system-overview.md`
- `docs/crypto/README.md`
- `docs/architecture/realtime-architecture.md`
