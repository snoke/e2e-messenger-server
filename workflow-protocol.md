# Workflow Protocol (Realtime Fast Path + Authoritative Commit)

Status: Draft v1  
Scope: Client <-> Gateway <-> Symfony (WS/WT only, kein Client-HTTP)

## 1. Ziel

Wir kombinieren:

- **Low-Latency Online Delivery** (A -> Gateway -> B direkt, wenn B online)
- **Authoritative Commit** (Gateway -> Symfony -> Gateway -> Clients)
- **Fallback** auf klassischen Store-and-Forward-Flow, wenn Empfänger offline ist

Symfony bleibt **Source of Truth** für Persistenz, ACL, State, Policy, Audit.

## 2. Prinzipien

- Gateway ist **transport + routing + fast relay**, nicht Domain-Source-of-Truth.
- Symfony ist **authoritative** für `committed|rejected|state`.
- Clients arbeiten mit **2-Phasen-Semantik**:
  - `live_*` = schnell/provisorisch
  - `*_committed` = final/verbindlich
- Idempotenz und Dedupe sind Pflicht.

## 3. Terminologie

- `message_id`: global eindeutig pro Nachricht (Client-generiert, stabil).
- `request_id`: request/response Korrelation.
- `conversation_id`: fachliche Zielkonversation.
- `live`: vom Gateway direkt zugestellt, noch nicht autoritativ.
- `committed`: von Symfony persistiert und autorisiert.

## 4. Event-Klassen

### 4.1 Client -> Gateway (Command)

- `chat_send`
- `attachment_upload_*`
- `call_session_*`
- `group_*`

Pflichtfelder:

- `type`
- `request_id`
- `message_id` (bei chat/file/call signal)
- `conversation_id` (falls konversationsgebunden)
- `ts_client`

### 4.2 Gateway -> Client (Live/Optimistic)

- `chat_live`
- `chat_live_delivered` (optional, wenn B live-ack sendet)

### 4.3 Symfony -> Client (Authoritative)

- `chat_committed`
- `chat_rejected`
- `chat_delivered` (serverseitig bestätigt)
- `state_*` (z. B. membership/history/call state)

## 5. Flow-Definition

## 5.1 Online-Empfänger (Fast Path)

1. A sendet `chat_send` an Gateway.
2. Gateway:
   - bindet `request_id -> connection`
   - macht minimale Gültigkeitschecks (Schema, Subject)
   - relayed `chat_live` direkt an online Subjekte
   - schreibt Event parallel in `ws.inbox` für Symfony
3. B zeigt Nachricht als `provisional`.
4. Symfony verarbeitet, validiert ACL/Membership/Epoch, persistiert.
5. Symfony published:
   - `chat_committed` an alle relevanten User/Devices
   - oder `chat_rejected` an Sender (und optional Empfänger mit tombstone)
6. Clients mergen:
   - `live` + `committed` via `(conversation_id, message_id)`
   - `committed` überschreibt `provisional`

## 5.2 Offline-Empfänger

1. A sendet `chat_send`.
2. Gateway kann nicht live relayen.
3. Symfony persistiert und liefert später bei Reconnect über normalen Flow.
4. Sender erhält weiterhin `chat_committed` (oder `chat_rejected`).

## 6. Client-State-Maschine

Status pro Nachricht:

- `pending_send` -> lokal erstellt
- `live_sent` -> Gateway hat live gesendet (optional)
- `committed` -> Symfony bestätigt
- `rejected` -> Symfony abgelehnt

Regeln:

- UI zeigt nur `committed` als final.
- `live` ohne Commit nach Timeout markiert als `pending_review`.
- Duplicate-Events immer idempotent behandeln.

## 7. Dedupe / Idempotenz / Ordering

- Dedupe-Key: `(conversation_id, message_id)`.
- Symfony muss `message_id` unique pro conversation durchsetzen.
- Gateway darf at-least-once zustellen; Client muss dedupen.
- Reihenfolge ist final über Symfony (`server_ts`/`server_seq`), nicht über Live-Reihenfolge.

## 8. Security-Standard

- Payload-Inhalt bleibt E2E (ciphertext); Gateway bleibt blind.
- Trotzdem Domain-Checks in Symfony bleiben verbindlich.
- Für Fast-Path nur minimaler Gateway-Check:
  - sender subject vorhanden
  - target subject(s) vorhanden
  - optionale kurzlebige Membership-Capability (empfohlen)

Empfohlen:

- `conversation_capability` (JWT/signiertes Token von Symfony, short TTL, enthält `conversation_id`, `user_id`, `role`, `epoch`).
- Gateway akzeptiert Live-Relay nur mit gültiger Capability.

## 9. Interfaces & Orte

## 9.1 Frontend

- `frontend/src/interfaces/plugins/messenger.ts`
  - `sendCommand(cmd)`
  - `onLiveEvent(evt)`
  - `onAuthoritativeEvent(evt)`
- `frontend/src/app/core/messaging/services/*`
  - Merge-Logik `live -> committed`
  - Timeout/Retry für `pending_review`

## 9.2 Gateway

- `gateway/rust-http3-gateway/src/gateway_core.rs`
  - Ingress parsing + request route binding
- `gateway/rust-http3-gateway/src/state.rs`
  - request route / subject route / dedupe cache (kurzlebig)
- Neu: `gateway/rust-http3-gateway/src/fast_path.rs`
  - Live relay policy, capability verify, emit `chat_live`
- `gateway/rust-http3-gateway/src/broker.rs`
  - outbox authoritative dispatch (bestehend)

## 9.3 Symfony

- `symfony/src/Messenger/MessageHandler/ChatHandler.php`
  - final validation + persist + committed/rejected publish
- `symfony/src/Messenger/MessageHandler/*`
  - analog für files/call sessions
- Optional neu:
  - `ConversationCapabilityIssuer` (signierte short-lived capabilities)

## 10. Protokoll-Felder (Mindestset)

Gemeinsame Felder:

- `type`
- `request_id` (wenn command/response)
- `message_id` (bei message-artigen Events)
- `conversation_id`
- `ts`
- `protocol_version`

Wichtig:

- Client-Commands enthalten **keine** `subjects` (z. B. `chat` mit `conversation_id`).
- `subjects` werden serverseitig aufgeloest:
  - Gateway kennt pro Verbindung den eigenen Subject (`user:<user_id>`) aus Auth.
  - Symfony bestimmt Empfaenger-Subjects aus Domain-State (Conversation-Membership/ACL).
- Nur Outbound-Events (Symfony -> Gateway) enthalten `subjects` fuer die Verteilung.

Live Event:

```json
{
  "type": "chat_live",
  "protocol_version": 1,
  "conversation_id": 42,
  "message_id": "m_abc123",
  "from": "user:alice@test.de",
  "ciphertext": "...",
  "nonce": "...",
  "suite": "...",
  "ts": 1773000000
}
```

Commit Event:

```json
{
  "type": "chat_committed",
  "protocol_version": 1,
  "conversation_id": 42,
  "message_id": "m_abc123",
  "server_seq": 9912,
  "server_ts": 1773000001,
  "ts": 1773000001
}
```

Reject Event:

```json
{
  "type": "chat_rejected",
  "protocol_version": 1,
  "conversation_id": 42,
  "message_id": "m_abc123",
  "error": "membership_denied",
  "ts": 1773000001
}
```

## 11. Observability

Pflicht-Metriken:

- `fast_path_relay_count`
- `fast_path_relay_online_ratio`
- `commit_latency_ms` (ingress -> committed)
- `live_without_commit_timeout_count`
- `rejected_after_live_count`
- `duplicate_event_drop_count`

Pflicht-Logs:

- `request_id`, `message_id`, `conversation_id`, `connection_id`, `user_id`

## 12. Rollout-Plan

1. Phase A: Nur `chat_live` zusätzlich, Commit-Flow unverändert.
2. Phase B: Client-Merge + provisional UI aktivieren.
3. Phase C: Capability-Checks im Gateway.
4. Phase D: Ausrollen auf Attachments/Calls.

Kill-Switch:

- `FAST_PATH_ENABLED=false` schaltet sofort auf klassischen Flow zurück.

## 13. Testfälle (Minimum)

- Online A/B: live kommt < committed, kein Duplicate in UI.
- Offline B: kein live, später commit/sync korrekt.
- Reject nach live: UI markiert korrekt `rejected`.
- Reconnect/HMR: request routing bleibt stabil.
- Duplicate Inject: Client deduped zuverlässig.
- Multi-device pro User: Commit auf allen Devices konsistent.

---

Dieses Protokoll definiert bewusst nur Workflow- und Interface-Standards.  
Implementierungsdetails (Schema-Migrationen, konkrete Klassen, Feature-Flags) folgen in einem separaten `implementation-plan.md`.
