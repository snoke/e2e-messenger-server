# Plugin Catalog (Current State)

Dieses Dokument beschreibt den aktuellen Stand der Desktop-Plugins:
- Was sie heute koennen
- Wie sie arbeiten
- Welches Security-Modell gilt
- Wo der Scope aktuell endet
- Was als naechstes sinnvoll ist

## Gemeinsame Leitlinien

- Transport: Realtime ueber WebSocket/WebTransport (keine neue REST-Abhaengigkeit fuer Plugin-Workflows).
- Source of Truth fuer synchronisierte Daten: MySQL; Redis als Queue/Realtime-Bus.
- Client-Storage: IndexedDB fuer lokale Keys, Caches und lokale Metadaten.
- Crypto-Grundsatz: Klartext nur auf dem Client; Server verarbeitet primar Ciphertext/Metadaten.

## 1) Audit Timeline

- Funktionen: Event-Timeline, Filter (Typ/Kategorie/Severity), Live-Stream, Verlauf laden.
- Funktionsweise: `audit_timeline_request` + `audit_event` ueber Realtime.
- Security: Payload-Sanitizing/Redaction serverseitig (sensitive Felder werden maskiert).
- Scope-Ende: Keine manipulationssichere Signaturkette pro Event.
- Ausbau: Hash-Chain/Signaturen, SIEM-Export, Retention/Policy pro Tenant.

## 2) Anonymous Dropbox

- Funktionen: Oeffentliche Dropbox-Endpunkte, anonyme verschluesselte Abgabe, Inbox fuer Owner.
- Funktionsweise: Public-Flow ueber Realtime (`dropbox_public_auth`, `dropbox_public_info_request`, `dropbox_public_submit`).
- Security: Hybrid-Verschluesselung (RSA-OAEP + AES-GCM), privater Dropbox-Key lokal in IndexedDB.
- Scope-Ende: Kein starkes Anti-Abuse/Rate-Limit/Captcha auf Produktniveau.
- Ausbau: Ablaufdatum/One-Time-Links, optional signierte Sender-Claims, Abuse-Controls.

## 3) Calls

- Funktionen: Live Audio/Video Calls (LiveKit), Join/Leave/Invite, Mute/Camera, Desktop-Entry.
- Funktionsweise: Call-Signaling ueber Realtime; Media ueber WebRTC/LiveKit.
- Security: Optionale zusaetzliche Media-E2EE-Schicht (SFrame/Insertable Streams) mit Key-Exchange ueber MLS-Control-Channel.
- Scope-Ende: Browser-Kompatibilitaet fuer Encoded Transforms bleibt Runtime-abhaengig; kein vollstaendiger PQ-WebRTC-Handshake.
- Ausbau: Striktere Capability-Negotiation pro Teilnehmer, harte Policy (required/optional), bessere Diagnostik.

## 4) Chat

- Funktionen: Direct/Group Chat, Gruppenverwaltung, Delivery-States (`pending/sent/delivered/read`), Attachments.
- Funktionsweise: Realtime Message-Pipeline + MLS-Orchestrierung fuer Group-E2EE.
- Security: E2EE mit MLS-Modus, Forward-Secrecy/Post-Compromise-Security-Pfad im Gruppenkontext.
- Scope-Ende: Edge-Cases bei Membership/History (Add/Join) brauchen weiterhin harte E2E-Regressionstests.
- Ausbau: formale State-Machine fuer Membership/History, explizite Test-Matrix fuer Add/Join/Replay.

## 5) Device Key Manager

- Funktionen: Device-Keys erzeugen, benennen, loeschen, Signatur-Challenges.
- Funktionsweise: Lokale Key-Verwaltung in IndexedDB, ECDSA P-256 Signatur fuer Identity-Auth.
- Security: Private Keys bleiben clientseitig (nicht ueber Netz exportiert).
- Scope-Ende: Kein Hardware-Key/TEE-Binding, kein zentrales Lifecycle-Policy-Management.
- Ausbau: WebAuthn/Secure-Enclave, verpflichtende Rotation, device-bound Attestation.

## 6) Key Trust Center

- Funktionen: Fingerprints verwalten, Trust-Status setzen (verified/unverified/revoked), Notizen.
- Funktionsweise: Realtime Requests (`key_trust_list_request`, `key_trust_upsert`, `key_trust_delete`) plus lokale UI.
- Security: Fingerprint-Ableitung aus Public Keys; server-synchronisierte Trust-Daten.
- Scope-Ende: Verification ist aktuell primar manuell (kein out-of-band Proof-Workflow integriert).
- Ausbau: QR/Fingerprint-Compare Flow, Policy-Engine (z. B. unknown key blocken), Audit-Verknuepfung.

## 7) Password Manager

- Funktionen: Passwort-Eintraege erstellen/bearbeiten, verschluesselt speichern, Cloud-Sync.
- Funktionsweise: Lokaler Vault-Key + verschluesselter Blob in UserStorage (`.vault/password-manager`).
- Security: AES-GCM auf Client-Seite vor Upload; Server sieht nur Ciphertext.
- Scope-Ende: Kein Browser-Autofill, kein Sharing/Delegation, einfache Recovery-Key-Handhabung.
- Ausbau: non-extractable Key-Modell, bessere Recovery-UX, Generator/Breach-Checks, Versionierung.

## 8) Secret Vault

- Funktionen: API-Keys/Zertifikate/Tokens als Secret-Records verwalten und syncen.
- Funktionsweise: Wie Password Manager, eigener Vault-Bereich (`.vault/secret-vault`).
- Security: Lokale Verschluesselung vor Sync, separater Vault-Key pro Plugin.
- Scope-Ende: Kein fein-granulares ACL/Approval/Rotation-Workflow.
- Ausbau: Ablaufdaten/Rotation-Reminder, per-Secret Access-Control, Environments/Scopes.

## 9) Identity

- Funktionen: Profilwerte pflegen, aktive Sessions/Clients anzeigen, Avatar im Profilordner verwalten.
- Funktionsweise: Profil ueber Realtime (`identity_profile_request` / `identity_profile_upsert`); Client-Liste ueber Realtime (`online_request`).
- Security: Optional clientseitig verschluesseltes Profil-Payload; Session/Client-Transparenz vorhanden.
- Scope-Ende: Kein vollstaendiger Policy-/Approval-Flow fuer Profilaenderungen.
- Ausbau: feinere Profilrechte, Audit-Verknuepfung, weiterfuehrende Device-Binding-Optionen.

## 10) Notes

- Funktionen: Notizen erstellen/oeffnen/bearbeiten, Markdown/TXT, Speicherung in UserStorage.
- Funktionsweise: Editor + verschluesselte Dateiablage ueber Realtime UserStorage-Flow.
- Security: Note-Inhalte werden clientseitig verschluesselt hochgeladen.
- Scope-Ende: Kein kollaboratives Editing/CRDT, kein vollwertiger Docs-Editor-Stack.
- Ausbau: Rich-Editor (z. B. Tiptap/ProseMirror), Version-History, Vorlagen, Freigabe-Modelle.

## 11) Vue-Storage (Vue-Finder)

- Funktionen: Datei-/Ordner-UI ueber alle Storage-Adapter (Cloud/UserStorage, OPFS, lokale Quellen).
- Funktionsweise: Vue-Finder UI + Adapter-Layer; Cloud-Adapter nutzt den UserStorage Realtime-Flow (`user_storage_*`).
- Security: Clientseitige Verschluesselung pro Adapter; Chunk-Integrity-Checks bei Cloud/UserStorage.
- Scope-Ende: Kein vollstaendiges Sharing/Linking/Quota-Produktniveau.
- Ausbau: resumable Uploads, Quotas, sichere Share-Links, Hintergrund-Sync.

## 12) ContactBook

- Funktionen: Kontakte anfragen/annehmen/blockieren/unblocken, Profildaten pflegen.
- Funktionsweise: Realtime fuer Kontaktzustand + Profile Requests; lokale Cache-Schicht in IndexedDB.
- Security: Zustandsaenderungen und Profile laufen ueber authentifizierten Realtime-Kanal.
- Scope-Ende: Kein externes Discovery/Adressbuch-Import, keine Team-Rollen/Policies.
- Ausbau: Kontaktgruppen/Tags, Import/Export, Policy-Regeln (z. B. Blocklisten-Defaults).

## 13) About VØID

- Funktionen: App-Version, Build-Nummer, Commit, Build-Zeit und Runtime-Mode anzeigen.
- Funktionsweise: Read-only Desktop-Plugin als Modal-Inhalt.
- Security: Keine sensitiven Nutzdaten; nur Build-Metadaten.
- Scope-Ende: Keine Diagnostics/Logs/Healthchecks integriert.
- Ausbau: Support-Bundle-Export (Version + Feature-Flags + Browser-Capabilities).

## Priorisierte naechste Schritte (empfohlen)

- Cross-plugin Security-Policy Layer: zentrale Regeln fuer Key-Trust, required E2EE, unknown-key Verhalten.
- Einheitliche Recovery/Rotation-Flows: Device Key Manager + Vault-Plugins konsolidieren.
- E2E-Testplan als Pflicht-Gate: Add/Join/History, multi-device read semantics, invite/dropbox flows.
- Telemetrie fuer Zuverlaessigkeit: Timeout-Klassen pro Request-Type, Retry/Backoff-Standards.
