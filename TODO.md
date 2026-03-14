# TODO

FEATURES FIRST - THIS TODO IS DUE WHEN FEATURES ARE FINAL.

## Stand (Ist)
- Scope-Architektur und Realtime-Standard dokumentiert (`Scopes.MD`, `docs/RealtimeCommunicationArchitecture.md`, `Signals.md`).
- Generischer MLS‑Signal‑Gate ist eingeführt und in **File‑Transfer** aktiv (`fileTransferService.ts`).
- Chat/Conversations/Send nutzen **noch** keine einheitliche Gate‑Logik (nur ad‑hoc Epoch‑Checks).

## Plan (Nächste Schritte)
1. **Chat‑Realtime** (`frontend/src/app/core/messaging/services/messenger/realtime/chat.ts`)
   - MLS‑Signals über Gate führen (ready / stale / future / defer‑replay).
2. **Conversations‑Realtime** (`frontend/src/app/core/messaging/services/messenger/realtime/conversations.ts`)
   - Epoch‑Handling vereinheitlichen (stale/future standardisieren).
3. **Outbound Send** (`frontend/src/app/core/messaging/services/messenger/send.ts`)
   - Epoch‑Wahl + deferred send über Gate standardisieren.
4. Smoke‑Tests: Typing/Read/Meta + MLS‑Epoch‑Wechsel + Recovery‑Pfad.

## Perspektive (Später)
- Gate als **generisches MLS‑Context‑Utility** für weitere Operation‑Scopes.
- Einheitliche Telemetrie: `ready / stale / future / defer / replay` über alle Domänen.
- Contract‑Tests für Signals (Payload‑Form, Scope‑Grenzen, Routing).
