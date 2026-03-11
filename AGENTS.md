# AGENTS.md
# Architektur- und Sicherheitsregeln für Agenten

Dieses Projekt verfolgt MLS-first Security, Command-Registry-basiertes Routing
und eine DDD/Hexagonal-Ausrichtung.

## 1) Harte Regeln (verbindlich)

### 1.1 Security & Kryptografie

- Keine neuen Kryptopfade für interne Kommunikation.
- Interne Kommunikation ist MLS-basiert; keine stillen Kryptofallbacks.
- 1:1-Chats werden als Gruppen modelliert.
- Kryptografische Membership ist device-basiert.
- Dateien nutzen eigene File Keys; keine direkte Verschlüsselung mit Gruppenschlüsseln.
- Keine automatische MLS-Gruppe pro Datei.
- Private Schlüssel verlassen das Gerät nicht im Klartext.
- Recovery-Material wird nie im Klartext gespeichert.

### 1.2 Gateway-Routing & Registry

- Es gibt eine zentrale Command-Registry als Single Source of Truth.
- Jeder Command hat genau eine Routing-Klasse:
  - `preauth`
  - `gateway_local`
  - `relay_hotpath`
  - `backend_control`
- Keine impliziten Routing-Fallbacks.
- Unbekannte / nicht registrierte Commands werden abgelehnt.
- Neue Commands nur mit Registry-Eintrag und passenden Tests/Checks.

### 1.3 Architektur-Invarianten

- Keine fachliche Kernlogik im Gateway.
- Gateway darf nur technische Aufgaben übernehmen (Annahme, Guards, Routing, Relay, Weiterleitung).
- `backend_control` bleibt fachlich autoritativ im Backend (Policy, Persistenz, Membership).
- Presence bleibt `backend_control`; kein blindes Global-Broadcasting.
- Für globales `presence_state` gilt kontakt-scoped Fanout (Policy serverseitig).
- Keine Parallelpfade für dieselbe Fachfunktion.
- Refactoring vor Neuimplementierung.

## 2) Zielbild (Richtungsregeln, nicht harter Ist-Zwang)

Diese Punkte sind Architekturziele und gelten als Leitplanken für neue Arbeit:

- DDD/Hexagonal sauberer ausprägen:
  - Domain/Application/Infrastructure/Interface klar trennen.
  - Domainlogik aus Framework-Rändern herausziehen.
- Handler dünn halten; Orchestrierung klar begrenzen.
- DTO/VO-gestützte Flows bevorzugen.
- Ungetypte Arrays zwischen internen Schichten schrittweise reduzieren.
- Frontend-/Backend-Plugin-Sprache konsistent halten.
- Kommunikation des Clients primär über Gateway-Transporte (WebSocket/WebTransport),
  keine fachlichen Bypässe.

## 3) Präzisierungen

- `type` / `mode` / `crypto_profile` sind als explizite Wire-Metadaten erlaubt.
- Diese Felder dürfen nicht als versteckte Ersatz-Policy oder implizite Architekturquelle missbraucht werden.
- Handler dürfen validieren und orchestrieren.
- Handler dürfen keine unkontrollierte fachliche Kernlogik ansammeln.
- Wire- und Transport-Payloads dürfen weiterhin JSON/Arrays verwenden;
  die Regel „weniger Arrays“ zielt auf interne Schichtgrenzen.

## 4) Änderungs-Checkliste für Agenten

Vor jeder größeren Änderung prüfen:

1. Verletzt die Änderung eine harte Regel aus Abschnitt 1?
2. Erzeugt sie einen neuen Parallelpfad oder impliziten Fallback?
3. Ist der Command sauber in der Registry klassifiziert?
4. Bleibt die Trennung zwischen technischer Gateway-Logik und fachlicher Backend-Logik erhalten?
5. Macht die Änderung das Zielbild aus Abschnitt 2 klarer oder unschärfer?
