# Roadmap

This roadmap lists **current priorities** and desired next steps. It does not assert completed work.

## Immediate Priorities
1. Stabilize MLS/CHK flows with automated regression tests (invite/accept/history, multi-device).
2. Harden inactive chat notifications (BEB + notification center) with end-to-end tests.
3. Align bootstrap/init flows to contacts-only directory and remove legacy `users` paths.

## Short-Term
- Formalize conversation state machine (MLS ready vs CHK ready) with explicit UI gating.
- Improve diagnostics for `conversation_key_missing` and vault unlock failures.
- Expand smoke tests for chat history and offline delivery.

## Medium-Term
- CHK rotation on membership changes (optional security hardening).
- Improve device approval / recovery UX for identity auth.
- Centralized policy layer for key trust and E2EE requirements.

## Long-Term
- WebTransport production hardening.
- Push notification integration (native mobile).