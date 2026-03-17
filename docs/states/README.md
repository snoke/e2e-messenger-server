# State Models

This section documents global and per-conversation states that are critical to runtime correctness.

## Files
- Global readiness: `docs/states/global-crypto-ready.md`
- Conversation readiness: `docs/states/conversation-crypto-ready.md`
- Matrix overview: `docs/states/state-matrix.md`

## Principles
- Global readiness is about login/vault.
- Conversation readiness is about CHK availability.
- These must never be conflated.
