# Plugin: Calls

## Responsibilities
- Call signaling and session control.
- Join/leave, mute, camera, invite.
- Optional media E2EE using MLS-protected control messages.
- MLS key agreement uses **X‑Wing (X25519 + ML‑KEM‑768)**.

## Media Path
- Signaling over realtime.
- Media over LiveKit WebRTC.

## Key Files
- LiveKit integration in frontend and backend call actions.

Related:
- [`docs/ops/tech-debt.md`](../ops/tech-debt.md)
- [`docs/workflows/message-send-receive.md`](../workflows/message-send-receive.md)
