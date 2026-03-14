# 1. Architekturüberblick

## 1.1 Status nach P0/P1/P2

Stand jetzt ist das Routing-Modell konsistent auf **vier Klassen** vereinheitlicht:
- `preauth`
- `gateway_local`
- `relay_hotpath`
- `backend_control`

Wesentliche Ergebnisse:
- Eine zentrale Registry als Single Source of Truth existiert (`gateway/rust-http3-gateway/src/routes.rs`).
- Die Registry hat jetzt zwei getrennte Achsen: `routing_class` und `message_type`.
- Implizite produktive Fallback-Routen wurden entfernt.
- Unbekannte Commands werden am Gateway explizit abgelehnt.
- `chat_message_send`, `chat_typing_state`, `presence_state` sind eindeutig klassifiziert (`backend_control`) und laufen auch zur Laufzeit so.
- Presence-Fanout ist backend-kontrolliert und kontakt-scoped statt globalem Blind-Broadcast.
- Legacy `call_*` bleibt aus Kompatibilitätsgründen aktiv, ist aber explizit `deprecated` markiert.
- Vertragstests/Drift-Checks sind ergänzt (Registry, Runtime-Verhalten, kritische Commands).

## 1.2 Einordnung gegen Zielbild

| Achse | Aktueller Stand | Bewertung |
|---|---|---|
| Command-Taxonomie | 4 Klassen sauber implementiert | hoch |
| Nachrichtensemantik | 5 Semantik-Typen explizit im Registry-Feld `message_type` | hoch |
| Registry/Runtime-Konsistenz | weitgehend synchronisiert | hoch |
| Hotpath explizit | für `file_transfer_*` klar umgesetzt | hoch |
| Implizite Routen | entfernt | hoch |
| Presence-Scope | kontakt-scoped Fanout serverseitig erzwungen | mittel-hoch |
| Minimal-blind Gateway | weiterhin nicht erreicht | niedrig |
| Soziale Graph-Sichtbarkeit im Gateway | weiterhin indirekt vorhanden | niedrig |

Gesamtnähe zum besprochenen Modell **nach P0/P1/P2**: **ca. 65–75%**.

# 2. Komponenten-Inventar

| Komponente | Zweck | Verantwortlichkeit | Autorisierung | Kontakt/Presence-Sicht |
|---|---|---|---|---|
| `frontend/src/app/core/messaging/services/client/wsClient.ts` | WS-Transport Client | Send/Receive über Gateway | nein | ja |
| `frontend/src/app/core/messaging/services/client/wtClient.ts` | WT-Transport Client | Send/Receive über Gateway | nein | ja |
| `frontend/src/app/core/messaging/services/messenger/**/*.ts` | Client-Orchestrierung | Chat/Group/Presence/Calls/MLS-Flows | lokal nur Guard-Logik | ja |
| `frontend/src/app/core/messaging/crypto/group/*` | MLS im Client | Group-State, Encrypt/Decrypt, Welcome/Commit Apply | nein | indirekt |
| `gateway/rust-http3-gateway/src/routes.rs` | Command-Registry | Command-Klassifikation + Dispatch-Plan + Drift-Checks | technisch/routingnah | indirekt |
| `gateway/rust-http3-gateway/src/gateway_core.rs` | Runtime-Router | Registry-basierte Annahme/Ablehnung, Relay, Backend-Weitergabe | technisch | ja |
| `gateway/rust-http3-gateway/src/preauth.rs` | Preauth-Schicht | Auth/Register/Identity Bootstrap | ja (preauth) | minimal |
| `gateway/rust-http3-gateway/src/state.rs` | Verbindungszustand | Connection-/Subject-Tabellen, Pending Delivery | nein (aber routing-kritisch) | ja |
| `gateway/rust-http3-gateway/src/broker.rs` | Outbox-Ingress/Egress | Redis Outbox Dispatch | nein | ja |
| `gateway/rust-http3-gateway/src/http_api.rs` | internes Gateway API | Connection-Introspection, Publish | API-Key gated | ja |
| `symfony/src/Void/Interface/Realtime/MessageHandlerCollection.php` | Backend Handler-Registry | Typ -> Handler Mapping | indirekt (delegiert) | abhängig vom Handler |
| Symfony Plugin-Handler (Chat/Calls/Contact/Storage/MLS/...) | Control-Plane Fachlogik | Policy, Persistenz, Membership, MLS-Orchestrierung | **ja** | **ja** |
| `symfony/src/Repository/ContactRepository.php` | Kontakt-Fanout-Datenbasis | accepted-Contacts für Presence-Audience | indirekt | **ja** |
| Redis Streams (`ws.inbox`, `ws.outbox`, `ws.events`) | Event-Bus | Asynchroner Austausch Gateway<->Backend | nein | ja |
| Datenbanken/Storage (MySQL, Blob-Storage, ggf. OPFS/IDB clientseitig) | Persistenz | Domain-Daten, KeyPackages, Nachrichten, Dateien | n/a | ja |

# 3. Command-Katalog

## 3.1 Verbindliche Routing-Klassen (Registry)

Quelle: `gateway/rust-http3-gateway/src/routes.rs` (`COMMAND_REGISTRY`).

| Routing-Klasse | Anzahl Commands |
|---|---|
| `preauth` | 5 |
| `gateway_local` | 1 |
| `relay_hotpath` | 11 |
| `backend_control` | 77 |
| **Gesamt** | **94** |

## 3.2 Verbindliche Nachrichtensemantik (Registry)

| Nachrichtensemantik (`message_type`) | Anzahl Commands |
|---|---|
| `technical` | 6 |
| `signal` | 8 |
| `query` | 25 |
| `command` | 55 |
| `event` | 0 *(inbound Registry absichtlich verboten)* |
| **Gesamt** | **94** |

## 3.3 Vollständige Command-Liste nach Routing-Klasse

### `preauth`
- `auth`
- `auth_login_request`
- `auth_register_request`
- `auth_identity_request`
- `dropbox_public_auth`

### `gateway_local`
- `ping`

### `relay_hotpath`
- `file_transfer_offer`
- `file_transfer_accept`
- `file_transfer_reject`
- `file_transfer_handshake`
- `file_transfer_handshake_ack`
- `file_transfer_welcome`
- `file_transfer_file_key`
- `file_transfer_file_key_ack`
- `file_transfer_chunk`
- `file_transfer_complete`
- `file_transfer_cancel`

### `backend_control`
- `bootstrap_request`
- `online_request`
- `users_request`
- `mls_key_package_publish`
- `mls_key_package_fetch`
- `contact_unblock`
- `contacts_request`
- `contact_profiles_request`
- `attachment_upload_init`
- `attachment_upload_chunk`
- `attachment_upload_finalize`
- `audit_timeline_request`
- `audit_timeline_export_request`
- `attachment_download_chunk`
- `attachment_list_request`
- `attachment_delete_request`
- `user_storage_upload_init`
- `user_storage_upload_payload`
- `user_storage_upload_finalize`
- `user_storage_download`
- `user_storage_list_request`
- `user_storage_delete_request`
- `user_storage_share_link_create`
- `user_storage_share_links_request`
- `user_storage_share_link_revoke`
- `user_storage_share_info_request`
- `user_storage_share_download`
- `contact_add`
- `contact_accept`
- `contact_block`
- `contact_profile_upsert`
- `contact_profile_delete`
- `deadman_config_request`
- `deadman_config_upsert`
- `dropbox_endpoints_request`
- `dropbox_endpoint_upsert`
- `dropbox_endpoint_delete`
- `dropbox_messages_request`
- `dropbox_message_delete`
- `dropbox_public_info_request`
- `dropbox_public_submit`
- `chat_conversations_request`
- `chat_conversation_open`
- `chat_messages_request`
- `group_create`
- `group_add`
- `group_leave`
- `group_membership_accept`
- `history_clear`
- `identity_profile_request`
- `identity_profile_upsert`
- `key_trust_list_request`
- `key_trust_upsert`
- `key_trust_delete`
- `mls_commit`
- `mls_welcome_request`
- `mls_welcome_ack`
- `presence_state`
- `chat_typing_state`
- `chat_message_read`
- `call_token_request`
- `call_session_create`
- `call_session_invite`
- `call_session_join`
- `call_session_leave`
- `call_session_media_key`
- `call_session_mute`
- `call_session_camera`
- `call_session_token_request`
- `call_invite` *(deprecated)*
- `call_join` *(deprecated)*
- `call_leave` *(deprecated)*
- `call_mute` *(deprecated)*
- `call_camera` *(deprecated)*
- `call_media_key` *(deprecated)*
- `chat_message_send`

## 3.4 Kritische Konsolidierungen (P0/P1)

- Vorher inkonsistent, jetzt explizit registriert:
  - `group_membership_accept`
  - `file_transfer_file_key`
  - `file_transfer_file_key_ack`
- Legacy-Call-Bereich ist explizit in Registry enthalten und als deprecated markiert.

## 3.5 Runtime-Ablehnungsmodell

- Nicht registrierte Commands -> `gateway_command_error` mit `unsupported_command`.
- `preauth`-Commands auf Runtime-Channel -> `preauth_only_command`.
- `relay_hotpath` ohne Ziel (`to`/`recipients`) -> `invalid_relay_targets`.
- Semantik-Guardrails in Registry-Validierung:
  - `preauth`/`gateway_local` müssen `technical` sein.
  - `backend_control`/`relay_hotpath` dürfen nicht `technical` sein.
  - `event` ist für inbound Commands nicht zulässig.

# 4. Command-Flow-Analyse

## 4.1 Effektive Pfade pro Klasse

- `preauth`:
  - nur initiale Auth-Auflösung in `preauth.rs`.
  - nicht im normalen Runtime-Router erlaubt.
- `gateway_local`:
  - rein lokal im Gateway (`ping`), kein Backend, kein Relay.
- `relay_hotpath`:
  - primäre Zustellung Gateway -> Ziel-Subjects.
  - im aktuellen Set primär `file_transfer_*`.
- `backend_control`:
  - Gateway -> Symfony (Inbox) -> Outbox/Event -> Clients.
  - gilt explizit auch für `chat_message_send`, `chat_typing_state`, `presence_state`.

## 4.2 Semantik pro kritischem Command (Auszug)

- `chat_message_send`: `backend_control` + `command`
- `chat_typing_state`: `backend_control` + `signal`
- `presence_state`: `backend_control` + `signal`
- `contacts_request`: `backend_control` + `query`
- `file_transfer_offer/chunk/complete`: `relay_hotpath` + `command`
- `auth_login_request`: `preauth` + `technical`
- `ping`: `gateway_local` + `technical`

## 4.3 Bewertung

Gegenüber dem vorherigen Zustand ist der zentrale Drift beseitigt:
- kein "als Fastpath deklariert, aber backend-first implementiert" mehr.
- `chat_message_send`, `chat_typing_state`, `presence_state` sind bewusst backend_control, nicht mehr Mischrealität.

Offen bleibt die strategische Frage, ob diese drei Commands künftig wieder in den Hotpath sollen. Aktuell ist das Modell konsistent, aber latenzseitig konservativ.

# 5. Datenfluss-Analyse

## 5.1 Identität/Auth

- `preauth` Commands werden am Gateway entgegengenommen, an Backend-Auth-Endpunkte angebunden.
- Gateway sieht notwendige Auth-Payloads im Preauth-Fenster.

## 5.2 Kontakt-/Beziehungsdaten

- Liegen weiterhin primär im Backend (ContactBook, Group Membership).
- Gateway sieht sie indirekt über Message-Metadaten (`to`, `recipients`, `conversation_id`, Subjects).

## 5.3 Presence

- Aktuell über backend_control (`presence_state`, `online_request` etc.).
- Globales `presence_state` (ohne `conversation_id`) wird nur an accepted Kontakte + Self verteilt.
- `presence` Snapshots bei Connect/Disconnect sind ebenfalls kontakt-scoped pro Empfänger.
- Gateway hat technische Sicht auf online Connections.

## 5.4 Datei-Transfer

- Steuer- und Chunk-Flows liegen im `relay_hotpath`.
- Backend ist nicht zustellungsblockierend.
- Gateway sieht Transfer-Metadaten, aber nicht notwendigerweise Klartextdateien.

## 5.5 Calls

- Call-Session-Steuerung überwiegend backend_control (`call_session_*`).
- Legacy `call_*` noch vorhanden, deprecate-markiert.

# 6. Trust-Boundary-Analyse

## 6.1 Sichtbarkeit sensibler Metadaten

- Gateway sieht weiterhin:
  - Sender/Empfänger-Bezüge über Subjects/Zielattribute
  - Conversation-/Transfer-/Session-IDs
  - Connection- und Routing-Metadaten
- Backend sieht zusätzlich:
  - Kontaktgraph, Membership, Presence, Persistenzdaten

## 6.2 Notwendigkeit vs Zielmodell

- Für das aktuelle Betriebsmodell ist diese Sichtbarkeit teilweise technisch notwendig.
- Gegen ein streng "minimal blind" Ziel bleibt das eine Abweichung.

# 7. Gateway-Verhaltensanalyse

## 7.1 Was jetzt sauber ist

- Routing hängt an der Registry (kein implizites produktives Fallback).
- Runtime trennt `preauth`, `gateway_local`, `relay_hotpath`, `backend_control` explizit.
- Unknown Commands werden früh und klar verworfen.
- Startup validiert Registry-Konsistenz.

## 7.2 Was weiterhin nicht minimal-blind ist

- Gateway hält globale Connection-/Subject-Zuordnung.
- Gateway kann aus Routing-Metadaten Peer-Beziehungen indirekt erkennen.
- Gateway bietet interne Introspection-Endpunkte.

# 8. Relay-Pfad vs Backend-Kontrollpfad

## 8.1 Saubere Trennung (nach P1)

- `relay_hotpath`: ausschließlich `file_transfer_*` inkl. `file_transfer_file_key*`.
- `backend_control`: Chat, Presence, Typing, MLS-Orchestrierung, Contacts, Groups, Calls.

## 8.2 Konsequenz

- Pfadtrennung ist jetzt technisch eindeutig und testbar.
- Die Trennung ist aktuell konservativ zugunsten Control-Plane bei zentralen Realtime-Events.

# 9. Hot-Path Blocking Analyse

## 9.1 Aktueller Zustand

- Für `relay_hotpath`-Commands ist Backend nicht zustellungsblockierend.
- Für `backend_control`-Commands ist Backend Teil des synchronen Pfads by design.

## 9.2 Interpretation

- Das ist kein Drift mehr, sondern ein expliziter Architekturentscheid.
- Risiko bleibt: Ausfall/Last im Backend beeinflusst direkt Chat/Typing/Presence-Latenz.

# 10. MLS-Gruppen-Lifecycle

- MLS-Orchestrierung bleibt backend_control (`mls_*`, Group-Membership-bezogene Commands).
- `group_membership_accept` ist jetzt eindeutig registriert und in Handler-Map vorhanden.
- Datei-Transfer nutzt separaten Hotpath für Nutzdaten/Transfer-Steuerung; die Control-Seite (Policy/Membership/Session-Management) bleibt backendseitig.
- Calls laufen weiterhin mit Session-Control im Backend und getrennten Media-Pfaden.

# 11. Autorisierungsmodell

## 11.1 Quelle der Autorität

- Backend bleibt autoritative Quelle für fachliche Policy, Membership und Persistenz.

## 11.2 Gateway-Rolle

- Gateway macht technische Guards und Routing-Entscheidungen gemäß Registry.
- Kein implizites Fach-Fallback mehr.

## 11.3 Offene Grenze

- Bei `relay_hotpath` gibt es technische Zielauflösung über Subjects, aber keine vollwertige Fachpolicy im Gateway (gewollt im aktuellen Scope).

# 12. Abweichungsbericht

## A1 (gelöst): Route-Drift zwischen Tabelle und Runtime

- Vorher: deklariert vs implementiert widersprüchlich.
- Jetzt: Registry + Runtime konsistent.

## A2 (gelöst): Implizite/unregistrierte produktive Commands

- Vorher: einzelne Commands nur implizit.
- Jetzt: registrierungspflichtig, unknown wird abgelehnt.

## A3 (teilgelöst): Legacy `call_*`

- Jetzt: explizit vorhanden + deprecated markiert + Backend-Mapping vorhanden.
- Offen: vollständige Entfernung in späterem Schritt.

## A4 (offen): Gateway ist nicht minimal blind

- Grund: globale Connection-/Subject-Sicht und ableitbarer Graph.
- Status: bewusst außerhalb P0/P1/P2.

## A5 (offen): Chat/Typing/Presence als backend_control

- Konsistent umgesetzt, aber nicht hotpath-first.
- Kann später bewusst umgestellt werden, falls Latenzanforderung steigt.

## A6 (gelöst): Presence-Globalbroadcast

- Vorher: Presence konnte global an alle Online-Users verteilt werden.
- Jetzt: kontakt-scoped Fanout über accepted Kontakte (plus Self), serverseitig erzwungen.

## A7 (offen): Betriebsnachweis

- Vertragstests sind implementiert, konnten lokal in dieser Session mangels Toolchain (`cargo`, `php`) nicht ausgeführt werden.

# 13. Konzeptueller Restrukturierungsplan (nächste sinnvolle Schritte)

1. Legacy-Call-Cleanup finalisieren
- Telemetrie auf `call_*` auswerten.
- Danach harte Entfernung der Legacy-Commands.

2. Explizite Entscheidung zu `chat_message_send`/`chat_typing_state`/`presence_state`
- Entweder bewusst backend_control belassen.
- Oder gezielt zu relay_hotpath migrieren mit klaren Guards und Backend-Nachlauf.

3. Guard-Modell pro `relay_hotpath` konkretisieren
- Dokumentieren, welche minimalen technischen Preconditions je Command gelten.

4. Drift-Schutz im CI erzwingen
- Registry-/Routing-Tests verbindlich im Build (sobald Toolchain in CI/Lokalumgebung vollständig ist).

5. Mittelfristig (außerhalb P0/P1/P2)
- Gateway-Metadatenfläche reduzieren (Richtung minimal-blind), ohne Routing-Klarheit wieder zu verlieren.
