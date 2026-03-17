# DDD/Hexagonal Refactoring Plan (Symfony Backend)

This is a historical planning document. For current backend structure, see:
- [`docs/architecture/backend.md`](../architecture/backend.md)

## Status

- `MessageHandlerCollection` wurde von einer monolithischen, hardcodierten Handler-Megamap auf modulare Registries umgestellt.
- Pro Kontext existiert jetzt eine eigene `*MessageHandlerRegistry` mit klarer Command-Zuordnung.
- Registries werden über einen gemeinsamen Registry-Tag zusammengesetzt; doppelte Command-Registrierungen werden beim Boot explizit abgelehnt.
- Der Schritt reduziert Kopplung am zentralen Entry-Point, ohne Wire-Protokoll oder Command-Namen zu ändern.
- `AnonymousDropbox` wurde auf dünne Interface-Handler + Application-Actions umgestellt.
- `ContactBook` wurde auf dünne Interface-Handler + Application-Actions umgestellt.
- `AuditTimeline`, `DeadManSwitch`, `Identity`, `KeyTrustCenter`, `Calls`, `Chat` und `UserStorage` wurden ebenfalls auf dünne Interface-Handler + Application-Actions umgestellt.
- `IdentityAuth` wurde vollständig unter `Plugins/IdentityAuth` konsolidiert (kein separates Top-Level-Modul mehr).

### Fortschritt nach Modul

- Core/Void Realtime Dispatch: **fertig (modulare Registry)**
- AnonymousDropbox: **fertig (Interface dünn, Application-Actions)**
- ContactBook: **fertig (Interface dünn, Application-Actions)**
- UserStorage: **fertig (Interface dünn, Application-Actions)** (Backend-Domäne; UI ersetzt durch Vue-Storage/Vue-Finder)
- Chat: **fertig (Interface dünn, Application-Actions)**
- Calls: **fertig (Interface dünn, Application-Actions)**
- AuditTimeline / DeadManSwitch / Identity / KeyTrust: **fertig (Interface dünn, Application-Actions)**
- IdentityAuth: **fertig (Plugin-Konsolidierung)**

Hinweis:
- Dieser Stand zieht die Realtime-Fachlogik aus den Interface-Handlern in Application-Actions.
- Nächster architektonischer Schritt bleibt optional: feingranulare Domain-Extraktion (Policies/VO/Aggregates) aus den Actions.
- UI-Hinweis: Das frühere Frontend-Plugin `UserStorage` wurde entfernt; UI läuft jetzt über Vue-Storage/Vue-Finder.

## 1. Ziel und Scope

### Ziel
Die aktuelle pluginbasierte Struktur wird schrittweise in eine saubere, modulare DDD/Hexagonal-Architektur überführt:
- fachliche Regeln in `Domain`
- Use-Case-Orchestrierung in `Application`
- Framework-/Transport-Code in `Interface`
- technische Adapter in `Infrastructure`

### Nicht-Ziel (in diesem Plan)
- Kein Big-Bang-Rewrite
- Kein Wire-Protokoll-Redesign
- Keine Änderung der 4 Routing-Klassen im Gateway

---

## 2. Ist-Zustand (Kurzdiagnose)

### Beobachtungen
- Viele Realtime-Handler in `Interface/Realtime/MessageHandler` enthalten Fachlogik, Persistenz und Publisher-Aufrufe.
- Es gibt einen zentralen, stark gekoppelten Dispatcher (`MessageHandlerCollection`) mit sehr vielen Handler-Abhängigkeiten.
- Plugin-`Domain` ist schwach ausgeprägt (sehr wenige echte Domain-Objekte/Services).
- Zwischen Schichten werden häufig ungetypte Arrays und Framework-Events durchgereicht.

### Messbare Indikatoren (Stand aktuell)
- Realtime-Handler: `67`
- Plugin-`Domain`-Dateien: `1`
- Plugin-`Application`-Dateien: `11`

### Hauptproblem
Hexagonal ist benannt, aber die fachliche Kernlogik sitzt vielfach am Framework-Rand.

---

## 3. Zielarchitektur (Soll)

## 3.1 Modulzuschnitt
Ein Modul entspricht einem Bounded Context (nicht nur ein Ordner):
- `Chat`
- `ContactBook`
- `Calls`
- `UserStorage`
- `AnonymousDropbox`
- `Identity`
- `KeyTrust`

Empfohlener Aufbau pro Modul:

```text
symfony/src/Modules/<Context>/
  Domain/
    Model/
    Service/
    Policy/
    Event/
    ValueObject/
  Application/
    Command/
    Query/
    Handler/
    Dto/
    Port/
  Infrastructure/
    Persistence/Doctrine/
    Realtime/
    Crypto/
  Interface/
    Realtime/
    Http/
    Cli/
```

## 3.2 Schichtregeln
- `Interface` kennt Framework, mappt Input, ruft Application-Handler auf.
- `Application` kennt Use Cases, Ports und Transaktionsgrenzen.
- `Domain` kennt keine Framework-Details.
- `Infrastructure` implementiert Ports.

## 3.3 Message-Semantik
Pro eingehendem Typ klar trennen:
- `command` (Write)
- `query` (Read)
- `signal` (ephemer)
- `technical` (Transport/Auth)

---

## 4. Refactoring-Prinzipien

- Strangler-Pattern: bestehende Handler bleiben zunächst als Fassade bestehen.
- Erst extrahieren, dann verschieben.
- Verhalten kompatibel halten, bis Contract-Tests grün sind.
- Kein neuer Parallelpfad pro Fachfunktion.
- Ports zuerst definieren, Adapter danach umhängen.

---

## 5. Schritt-für-Schritt Plan

## Phase 0 — Baseline einfrieren

### Aufgaben
- Aktuellen Command-Katalog als Referenz fixieren (`type -> owner module -> semantic type`).
- Für jeden Handler klassifizieren: `adapter-only` vs `contains-domain-logic`.
- ADR für Zielstruktur und Schichtregeln schreiben.

### Ergebnis
- Architekturvertrag + Inventar als gemeinsame Referenz.

### Akzeptanzkriterium
- Jeder vorhandene Message-Typ ist einem Modul und einer Semantik zugeordnet.

---

## Phase 1 — Modulrahmen einziehen

### Aufgaben
- Neues `Modules/`-Layout anlegen (zunächst leer/leichtgewichtig).
- Gemeinsame Application-Bausteine anlegen:
  - `CommandBus` (leichtgewichtig)
  - `QueryBus` (leichtgewichtig)
  - Basistypen für Result/Errors/RequestContext
- Port-Schnittstellen für Realtime-Publish, Presence, Repositories definieren.

### Ergebnis
- Technischer Rahmen für inkrementelle Migration.

### Akzeptanzkriterium
- Keine Verhaltensänderung, nur strukturelle Vorarbeit.

---

## Phase 2 — Pilotmodul (AnonymousDropbox)

### Aufgaben
- Realtime-Handler werden dünn:
  - Input normalisieren
  - in Application-Command/Query mappen
  - Antwort mappen
- Businessregeln aus Handlern nach `Application`/`Domain` verschieben.
- Doctrine-/Publisher-Aufrufe nur noch über Ports.

### Ergebnis
- Erstes vollständig hexagonalisiertes Modul.

### Akzeptanzkriterium
- Kein fachlicher Write-Flow mehr direkt im Interface-Handler.

---

## Phase 3 — ContactBook und KeyTrust/Identity

### Aufgaben
- Contact-Policy (add/accept/block/unblock) in Domain/Application ziehen.
- Profile-/Trust-Querys als echte Query-Handler trennen.
- Realtime-Antwortformat kompatibel halten.

### Ergebnis
- Mittleres Kernmodell sauber modularisiert.

### Akzeptanzkriterium
- Kontaktregeln liegen nicht mehr in Realtime-Adaptern.

---

## Phase 4 — UserStorage

### Aufgaben
- Upload-Lifecycle (`init/chunk/finalize/resume`) in Application-Use-Cases.
- Quota-/Validation-/Errorregeln zentral in Domain/Application.
- Realtime-Handler nur noch Transport-Mapping.

### Ergebnis
- Schwergewichtiger Write-Bereich entkoppelt.

### Akzeptanzkriterium
- Kein direkter Infrastrukturzugriff aus Interface-Handlern.

---

## Phase 5 — Chat (inkl. typing/read/messages)

### Aufgaben
- Use-Case-Schnitt je Message-Typ:
  - `chat_message_send`
  - `chat_typing_state`
  - `chat_message_read`
  - `chat_messages_request`
- Membership/Freeze/Visibility-Regeln in Domain-Policies.
- Publisher-Zielauflösung als Application-Service (über Ports) kapseln.

### Ergebnis
- Größter Realtime-Bereich strukturell bereinigt.

### Akzeptanzkriterium
- Chat-Handler enthalten keine Mitgliedschafts- oder Freeze-Policy mehr.

---

## Phase 6 — Calls + MLS-berührte Flows

### Aufgaben
- `call_session_*` in dedizierte Application-Use-Cases schneiden.
- MLS-Orchestrierung als klarer Domain/Application-Service mit Ports.
- Harte Invariante dokumentieren: Transport-Autorisierung ersetzt keine MLS-/Key-Policy.

### Ergebnis
- Sicherheitskritische Flows konsistent geschichtet.

### Akzeptanzkriterium
- Kryptografische Policy bleibt klar von Transport-/Adapterlogik getrennt.

---

## Phase 7 — Dispatcher dekomponieren

### Aufgaben
- `MessageHandlerCollection` ersetzen durch modulare Registry:
  - `ModuleMessageRegistry` je Modul
  - zentrale Komposition ohne riesige Constructor-Liste
- Optional: automatische Registry-Validierung beim Boot.

### Ergebnis
- Geringere Kopplung und bessere Wartbarkeit.

### Akzeptanzkriterium
- Keine monolithische Handler-Megamap mehr.

---

## 6. Definition of Done (gesamt)

- Interface-Handler sind dünne Adapter (Mapping/Validation/Dispatch).
- Fachregeln liegen in Domain/Application.
- Infrastrukturzugriffe laufen über Ports.
- Jeder Message-Typ hat klaren Owner-Kontext und Semantik (`command/query/signal/technical`).
- Bestehendes Wire-Verhalten bleibt kompatibel (außer explizit beschlossene Änderungen).

---

## 7. Risiken und Gegenmaßnahmen

### Risiko: Drift zwischen alter und neuer Struktur
- Gegenmaßnahme: Contract-Tests pro Message-Typ (input/output + side effects).

### Risiko: Zu breite Parallelstrukturen
- Gegenmaßnahme: pro Phase feste „Migrationsdone“-Kriterien und alte Pfade entfernen.

### Risiko: Sicherheitsregeln werden versehentlich verschoben
- Gegenmaßnahme: MLS-/Policy-Invarianten als Tests und ADR explizit festhalten.

---

## 8. Empfohlene Reihenfolge (pragmatisch)

1. Phase 0–1 sofort
2. Pilot: AnonymousDropbox
3. ContactBook + KeyTrust/Identity
4. UserStorage
5. Chat
6. Calls + MLS-nahe Flows
7. Dispatcher-Dekomposition

Diese Reihenfolge minimiert Risiko und schafft früh sichtbare Strukturgewinne.