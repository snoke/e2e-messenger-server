# Engineering Standards

Dieses Dokument definiert, wie Tasks geplant, umgesetzt, validiert und abgeschlossen werden. Ziel ist **klare Architektur, nachvollziehbare Änderungen und verlässliche Releases**.

---

## Prinzipien

1. Fix root cause, not symptoms.
2. Remove workarounds after fixing the root cause.
3. One clear flow per behavior. No parallel logic.
4. Every change must be understandable in isolation and justified in context.
5. Prefer simplicity over cleverness.
6. Explicit over implicit.
7. Consistency beats optimization.

---

## Project Guardrails (verbindlich)

Diese Regeln spiegeln die projektweiten Leitplanken wider (siehe `CODEX.md` und `AGENTS.md`).

1. **MLS-first / Security**
   - Keine neuen Kryptopfade für interne Kommunikation.
   - Keine stillen Kryptofallbacks.

2. **Command Registry als Single Source of Truth**
   - Jeder Command ist registriert und einer Routing-Klasse zugeordnet.
   - Unbekannte Commands werden abgelehnt.

3. **Gateway bleibt technisch**
   - Keine fachliche Kernlogik im Gateway.

4. **Authoritative Backend**
   - Kein fachlicher Bypass am Backend vorbei (siehe `docs/workflows/workflow-protocol.md`).

5. **Keine Parallelpfade**
   - Refactor vor Neuimplementierung.
   - Prefer deletion over addition.

6. **Wire-Kompatibilität**
   - Bestehendes Wire-Protokoll standardmäßig erhalten.

7. **Storage-Regel**
   - Storage ist file-only.
   - Chunking ist nur für Transfer-Flows erlaubt.

---

## Task Classification

Jeder Task muss vor Beginn klassifiziert werden.

### Bugfix
1. Verhalten ist falsch, inkorrekt oder regressiv.
2. Ziel ist die Wiederherstellung des erwarteten Verhaltens.

### Feature
1. Neue Capability, neuer Flow oder neue Schnittstelle.
2. Jede neue Datenverarbeitung oder API zählt als Feature.

### Refactor
1. Kein verändertes Verhalten.
2. Verbesserung von Struktur, Lesbarkeit oder Wartbarkeit.

### Ops / Infra
1. Deployment, CI/CD, Config, Infrastruktur.
2. Kein direkter Einfluss auf Business-Logik.

### Docs
1. Nur Dokumentation.
2. Keine Code-Änderung.

👉 Wenn mehrere Kategorien betroffen sind, müssen sie getrennt behandelt oder in getrennte Changes aufgeteilt werden.

---

## Execution Mode

Jeder Task muss explizit in einem Modus ausgeführt werden:

- Analyze only
- Plan only
- Implement
- Validate
- Cleanup only

Regeln:
- In `Analyze only` und `Plan only` darf keine Implementierung erfolgen.
- In `Implement` dürfen keine unnötigen Architekturänderungen ohne klaren Bedarf eingeführt werden.
- Der aktuelle Modus muss vor Beginn des Tasks klar sein.

---

## Task Lifecycle

Jeder Task folgt diesem Ablauf:

### 1. Understand
- Was ist das Problem wirklich?
- Was ist die Root Cause?
- Welche Teile des Systems sind betroffen?
- Welche Leitplanken sind relevant (`CODEX.md`, `AGENTS.md`, `docs/workflows/...`)?

### 2. Define
- Was ist die Ziel-Behavior?
- Was ist explizit **nicht** Teil dieses Tasks?

### 3. Plan
- Welche minimalen Änderungen lösen das Problem?
- Welche bestehenden Patterns müssen genutzt werden?
- Welche bestehenden Pfade müssen ersetzt statt ergänzt werden?

### 4. Implement
- Keine Workarounds als Endzustand.
- Kein paralleler Codepfad.
- Keine halben Lösungen.

### 5. Validate
- Funktioniert der Flow vollständig?
- Gibt es Seiteneffekte?
- Ist der ursprüngliche Fehler wirklich weg?
- Ist kein neuer Parallelpfad entstanden?

### 6. Cleanup
- Alte Logik entfernen.
- Dead Code löschen.
- Temporäre Fixes entfernen.
- Übergangslogik aktiv auf Entbehrlichkeit prüfen.

---

## Change Rules

### 1. No Parallel Paths
❌ Zwei Implementierungen gleichzeitig  
✅ Eine klare Quelle der Wahrheit

---

### 2. No Hidden Behavior
❌ Implizite Side Effects  
✅ Explizite Logik und klare Datenflüsse

---

### 3. No Temporary Fixes Left Behind
❌ TODO bleibt bestehen  
✅ Übergangslogik wird entfernt oder sauber abgeschlossen

---

### 4. Transitional Logic Rule
Temporäre Guards, Fallbacks, Retry-Schleifen, Debug-Logs, Übergangspfade und Hotfixes,
die während der Ursachenanalyse oder Stabilisierung eingeführt wurden,
müssen nach Lösung der Root Cause aktiv auf Entbehrlichkeit geprüft und entfernt werden.

Ein Task gilt nicht als abgeschlossen, solange unnötige Übergangslogik aktiv ist.

---

### 5. Primary Flow Rule
Für jedes Verhalten soll es genau einen regulären Pfad geben.
Fallbacks dürfen nur klar begrenzte Ausnahmefälle abdecken und dürfen nicht faktisch Teil des Normalbetriebs werden.

Wenn ein Primärpfad repariert oder eingeführt wurde,
müssen frühere Übergangs- oder Fallback-Pfade aktiv zurückgebaut oder stillgelegt werden.

---

### 6. Single Runtime Entry Rule
Für jeden fachlichen Flow gibt es genau **eine** Runtime/Facade als Einstiegspunkt.
Keine zweite „Neben-Runtime“ oder Parallel-Orchestrierung.

---

### 7. Orchestrator Thinness Rule
Eine Runtime/Facade koordiniert Ablaufreihenfolge und delegiert.
Sie darf keine eigenständigen fachlichen Entscheidungsblöcke implementieren.

Wenn eine Funktion in der Runtime:
- eigene Entscheidungslogik enthält (Policy, Gating, Retry, State-Transitions),
- eigenständig fachlich benennbar ist,
- oder unabhängig testbar wäre,

dann gehört sie in ein eigenes Modul.

Der Orchestrator darf enthalten:
- Reihenfolge von Aufrufen,
- Delegation an Module,
- einfache lineare Flow-Steuerung,
- Komposition von Dependencies.

Der Orchestrator darf **nicht** enthalten:
- fachliche Policy-Logik,
- Gating-Logik,
- Retry-Strategien,
- komplexe State-Transitions über mehrere fachliche Bereiche,
- eigenständige Crypto-, IO- oder Event-Workflows.

---

### 8. Sub-Runtime Requirement
Wenn eine Runtime mehr als einen eigenständigen Fachfluss enthält
(z. B. Session-Lifecycle + Key-Handshake + Token-Flow),
muss jeder Fachfluss als eigenes Modul oder Sub-Runtime gekapselt werden.

Indikatoren dafür sind:
- mehrere große Closures,
- mehrere unterschiedliche Trigger-Arten,
- mehrere unabhängige State-Bereiche,
- mehrere klar trennbare Mini-Flows.

Die zentrale Runtime bleibt die einzige Entry-Facade, aber nicht der Logik-Träger.

---

### 9. State Purity Rule
State-Module enthalten nur State, Maps, Refs und Transition-Logik.
Keine IO, keine Crypto, keine Side Effects.

---

### 10. State Access Budget
Eine Runtime darf nicht breit und unstrukturiert auf viele State-Maps, Sets oder Refs zugreifen.
State-Zugriff muss entlang klarer fachlicher Grenzen erfolgen
(z. B. über dedizierte State-Module oder Facades pro Fachfluss).

Wenn eine Runtime direkten Zugriff auf mehrere unabhängige State-Bereiche hat,
ist sie ein Refactor-Kandidat.

Warnsignal:
Wenn eine Runtime mehr als wenige unabhängige State-Container direkt nutzt,
ist sie mit hoher Wahrscheinlichkeit zu zentral und muss weiter aufgeteilt werden.

---

### 11. Inbound/Outbound Separation
Inbound-Event-Handling und Outbound-Dispatch dürfen nicht vermischt werden.

Inbound-Logik (Event-Handling) und Outbound-Logik (Dispatch/Send)
dürfen nicht im selben Modul implementiert werden,
wenn sie eigenständige Verantwortungen darstellen.

Eine Runtime darf beide aufrufen, aber nicht selbst implementieren,
wenn dafür bereits eigene fachliche Module existieren oder klar abgrenzbare Module entstehen können.

Jeder Pfad muss klar erkennbar sein.

---

### 12. Large Closure Rule
Lokale Funktionen oder Closures, die eigenständige fachliche Verantwortung tragen
oder größer als ca. 60–80 LOC sind, müssen ausgelagert werden.

Ausnahmen sind nur zulässig, wenn die Trennung den Flow künstlich zersplittert
und keinen Architekturgewinn bringt.

---

### 13. Mini-Flow Rule
Wenn mehrere Funktionen zusammen einen klaren Ablauf bilden
(z. B. initialize → wait → apply → broadcast),
dann ist dies ein eigener fachlicher Flow
und gehört in ein eigenes Modul oder eine Sub-Runtime.

Diese Logik darf nicht verteilt in der zentralen Runtime verbleiben.

---

### 14. Keep Changes Minimal
❌ „Ich mach das schnell noch mit“  
✅ Jeder Change hat klaren Scope

---

### 15. Prefer Deletion Over Addition
- Wenn möglich: Code entfernen statt erweitern.

---

### 16. Refactor Rule
Ein Refactor verändert kein Verhalten.

Wenn Verhalten, Flow, Datenmodell, Persistenz oder externe Schnittstellen verändert werden,
ist es kein reiner Refactor mehr und muss als Bugfix oder Feature klassifiziert werden.

Zusatz:
Refactors dürfen bestehende Wire-Formate, Manifests, Header oder Protokollverhalten nicht still verändern.

---

### 17. Refactor Completeness Rule
Ein Refactor gilt als unvollständig, wenn:
- die Hauptdatei weiterhin mehrere klar trennbare fachliche Blöcke enthält,
- große Closures mit eigener Verantwortung bestehen bleiben,
- der Orchestrator weiterhin selbst fachliche Entscheidungen implementiert,
- oder die Datei zwar kleiner geworden ist, aber strukturell weiterhin ein ausgedünnter Monolith bleibt.

Ein Refactor darf nicht als abgeschlossen gelten, nur weil:
- die Datei kleiner geworden ist,
- Teile ausgelagert wurden,
- oder erste Hilfsmodule entstanden sind.

Maßgeblich ist, ob die verbleibende Datei noch eigenständige fachliche Blöcke enthält.
In diesem Fall muss der Refactor weitergeführt werden.

---

## Architecture Consistency

1. Ähnliche Probleme müssen mit ähnlichen Mustern gelöst werden.
2. Keine neuen Patterns ohne klaren Grund.
3. Bestehende Struktur respektieren.
4. Cross-repo Änderungen synchron halten.
5. Authoritative Flow beibehalten (Client → Gateway → Backend → Events).

---

## Refactoring Guidelines (Soft Rules)

Ziel dieser Regeln ist es, Dateien modular, nachvollziehbar und wartbar zu halten,
ohne sinnvolle Orchestratoren künstlich zu zersplittern.

### 1. Soft Size Guardrail
- **Allgemeine Dateien:** Zielbereich ca. **500–800 LOC**
- **Runtimes/Orchestrators:** Zielbereich ca. **200–500 LOC**
- Dateien oberhalb dieser Bereiche sind **Refactor-Kandidaten**
- Das ist **keine harte Verbotsregel**, sondern ein Signal zur Prüfung

Diese Bereiche sind keine Zielgröße, sondern eine Orientierung nach oben.
Kleinere Dateien sind grundsätzlich vorzuziehen, solange:
- die Verantwortungsgrenzen klar bleiben
- keine künstliche Fragmentierung entsteht
- der Orchestrator nicht an Lesbarkeit verliert

- LOC umfasst auch Kommentare und Leerzeilen; Ziel ist Lesbarkeit, nicht kosmetische Kürzung

Ausnahme:
- Orchestratoren mit stark gekoppelten, sequenziellen Abläufen dürfen darüber liegen,
  wenn die Trennung den Flow künstlich fragmentieren würde.

Beispiele:
- LiveKit ↔ E2EE ↔ Signaling
- Chunk → Encrypt → Send → Ack → Finalize → Store

Sehr kleine, klar abgegrenzte Module (ca. 50–150 LOC) sind ein optimaler Zielzustand.

Diese entstehen als Ergebnis sauberer Verantwortungs-Trennung,
nicht durch künstliches Aufsplitten.

Wenn eine Datei deutlich größer wird, ist das ein Signal,
dass mehrere Verantwortungen vermischt sind.

Wenn eine Datei sehr klein ist, aber keine klare eigenständige Rolle hat,
ist sie wahrscheinlich unnötig fragmentiert.

---

### 2. Eine Runtime / ein Orchestrator pro Feature

- Pro fachlichem Flow gibt es genau einen zentralen Orchestrator / Runtime Entry.
- Diese Datei darf die Reihenfolge eines komplexen Flows koordinieren.
- Zusätzliche Logik wird in Hilfsmodule ausgelagert, nicht in konkurrierende Neben-Runtimes.

Ziel:
- zentraler Ablauf bleibt lesbar
- Detailverantwortungen werden ausgelagert
- kein Parallelpfad entsteht

---

### 3. State / IO / Crypto / Inbound / Outbound trennen

Wenn eine Datei mehrere dieser Verantwortungen mischt, ist sie ein Refactor-Kandidat.

Typische Zielmodule:
- `SomethingState.ts`
- `SomethingIO.ts`
- `SomethingCrypto.ts`
- `SomethingInbound.ts`
- `SomethingOutbound.ts`
- `SomethingUtils.ts`
- `SomethingRuntime.ts`

Die Trennung muss entlang **echter Verantwortungen** erfolgen,
nicht entlang künstlicher Dateisplits.

---

### 4. Orchestrator bleibt, Details gehen raus

Der zentrale Orchestrator darf enthalten:
- Ablaufreihenfolge,
- Koordination zwischen Modulen,
- Delegation,
- Komposition von Dependencies,
- klaren Einstiegspunkt.

Der Orchestrator darf **nicht unnötig enthalten**:
- Storage-Implementierung,
- Crypto-Implementierung,
- Chunk-Operationen,
- Request-/Command-Bau,
- Parsing-/Normalization-Details,
- große Inbound-/Outbound-Handlerblöcke,
- fachliche Policy- oder Retry-Entscheidungen.

Faustregel:
Der Orchestrator ruft Module auf, er implementiert sie nicht selbst.

---

### 5. Inbound und Outbound nicht mischen

- Eingehende Event-Verarbeitung gehört in eigene Inbound-Handler.
- Ausgehende Dispatch-/Send-Logik gehört in eigene Outbound-Module.
- Der Orchestrator verbindet beide.

Das verhindert:
- unklare Side Effects,
- zyklische Logik,
- schwer lesbare Runtime-Dateien.

---

### 6. Extract-First bei großen Blöcken

Kandidaten für Extraktion:
- Funktionen > ca. **60–80 LOC**
- mehrere logisch getrennte Unterphasen in einer Funktion
- wiederverwendete Mapping-, Parsing- oder Validation-Logik
- Blöcke mit eigener Verantwortlichkeit
- größere `switch`- oder Event-Router-Zweige
- gruppierte Funktionen, die gemeinsam einen Mini-Flow bilden

Nicht jede große Funktion muss ausgelagert werden,
aber sie muss aktiv auf Extraktionspotenzial geprüft werden.

---

### 7. Module dürfen nicht zu Mischcontainern werden

Ein ausgelagertes Modul braucht eine klare Rolle.

Schlecht:
- `utils + io + crypto` in einer Datei
- `state + effects`
- `handlers + storage + retry`

Gut:
- klare, fachlich stabile Verantwortung
- Dateiname erklärt die Rolle
- Logik ist isolierbar verständlich

---

### 8. Keine Fragmentierung um der Fragmentierung willen

Refactoring dient nicht dazu, möglichst viele kleine Dateien zu erzeugen.

Eine Extraktion ist nur sinnvoll, wenn sie:
- Verantwortung trennt,
- Wiederverwendung verbessert,
- Testbarkeit erhöht,
- den Orchestrator sichtbar entlastet,
- die Dateiarchitektur klarer macht.

Wenn eine Trennung nur mehr Import-Lärm und Kontextwechsel erzeugt,
ohne echte Verantwortungsgrenze, dann ist sie nicht sinnvoll.

---

### 9. Begründete Ausnahmen sind erlaubt

Wenn Logik im Orchestrator bleibt, muss das kurz begründbar sein
(z. B. im PR/Commit-Body oder per knapper Kommentar-Notiz).

Typische zulässige Begründungen:
- „stark gekoppelte Sequenz“
- „Trennung würde Ablauf künstlich zersplittern“
- „nur einmaliger zentraler Flow ohne stabile Unterverantwortung“
- „inline behalten, weil sonst mehr Fragmentierung als Klarheit entsteht“

Wichtig:
Ausnahmen sind erlaubt,
aber sie müssen bewusst sein und dürfen nicht aus Bequemlichkeit entstehen.

---

### 10. Refactor-Erfolg nicht nur an LOC messen

Ein Refactor ist nicht automatisch gut, nur weil die Datei kleiner wurde.

Ein Refactor ist gelungen, wenn:
- Verantwortungen klarer getrennt sind,
- der Orchestrator sichtbar schlanker ist,
- keine Parallelpfade entstanden sind,
- die Struktur konsistent zu bestehenden Patterns ist,
- die Datei leichter verständlich ist,
- und verbleibende Fachblöcke bewusst und begründet zentral geblieben sind.

LOC ist ein Signal, nicht das Ziel.

---

### 11. Low-Risk First

Refactors sollen in dieser Reihenfolge gedacht werden:

1. Constants / Types / Utils
2. reine State-Container
3. Parser / Mapper / Validation
4. IO / Crypto / Storage
5. Inbound / Outbound
6. Runtime / Orchestrator final verschlanken

So bleibt der Refactor kontrollierbar und reviewbar.

---

### 12. Einheitliche Muster über ähnliche Dateien

Ähnliche Probleme müssen ähnlich gelöst werden.

Wenn in einem Feature bereits ein gutes Muster existiert
(z. B. `Runtime + State + IO + Crypto + Inbound + Outbound`),
dann muss dieses Muster bevorzugt wiederverwendet werden,
statt pro Datei eine neue persönliche Struktur zu erfinden.

---

## Definition of Done (Task Level)

Ein Task ist **nur dann fertig**, wenn:

1. Root Cause identifiziert und gelöst ist
2. Kein Workaround mehr existiert
3. Keine redundante Logik übrig ist
4. Code konsistent mit der Architektur ist
5. Änderung vollständig getestet wurde
6. Dokumentation aktualisiert ist (falls nötig)
7. Tests/Validierung dokumentiert sind (oder explizit `not run` inkl. Begründung)

---

## Validation & Testing

1. Jede Änderung muss validiert werden.
2. Bei Bugfixes müssen der zuvor kaputte Flow **und** der Ziel-Flow validiert werden.
3. Validierung muss zeigen:
   - Fehler behoben
   - Ziel-Flow ok
   - kein neuer Parallelpfad
4. Tests müssen dokumentiert werden (oder explizit `not run` inkl. Begründung).

Beispiele:
- `Tests: manual login flow`
- `Tests: API request via curl`
- `Tests: not run (refactor, no behavior change)`

---

## Anti-Patterns (verboten)

❌ Quick fix ohne Root Cause  
❌ Dead Code behalten „für später“  
❌ Mehrere konkurrierende Lösungen  
❌ Halb implementierte Features  
❌ Magische Nebenwirkungen  
❌ Ausgedünnte Monolithen als „fertige Refactors“ behandeln  

---

## Good Practices

✅ Kleine, vollständige Changes  
✅ Explizite Logik  
✅ Klare Datenflüsse  
✅ Konsistente Patterns  
✅ Dünne Runtimes / Facades  
✅ Klare fachliche Modulgrenzen  

---

## Optional: Task Template

Für größere Tasks:

Type: fix | feat | refactor | ops | docs

Context:
...

Problem:
...

Root cause:
...

Solution:
...

Non-goals:
...

Risks:
...

Validation:
...