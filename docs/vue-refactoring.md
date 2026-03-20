# Vue Refactoring Rules (verbindlich)

## Grundregel

`.vue`-Dateien sind ausschließlich UI-Adapter.

Sie sind verantwortlich für:
- Rendering
- User-Interaction
- Binding von State an UI

Sie sind **nicht** verantwortlich für:
- Business-Logik
- Orchestrierung
- IO
- Storage
- Crypto
- komplexe State-Maschinen

---

## 1. Trennung von UI und Logik

Logik, die unabhängig von Vue existieren kann, **muss** in `.ts`-Dateien ausgelagert werden.

Verboten in `.vue`:
- Netzwerk-Requests (HTTP, WebSocket Commands)
- Storage-Zugriffe (OPFS, IndexedDB)
- Crypto-Operationen
- Retry-/Timeout-/Queue-Logik
- Chunking / Transfer-Logik
- komplexe Event-Orchestrierung

Erlaubt in `.vue`:
- Aufruf von Services / Runtime-Funktionen (nur Aufruf, keine Implementierung)
- UI-State (z. B. modalOpen, selectedTab)

---

## 2. Keine Business-Logik in Vue

Business-Logik **darf nicht** in `.vue` implementiert werden.

Beispiele (verboten):
- Entscheidungslogik über Datenflüsse
- Key-Handling / Crypto-Flows
- History-/Message-Orchestrierung
- File-Transfer-Logik

Diese Logik **muss** in dedizierten `.ts`-Modulen liegen.

---

## 3. Watcher-Regel

Watcher **dürfen keine Business-Logik enthalten**.

Verboten:
- Netzwerk-Requests in Watchern
- State-Maschinen in Watchern
- indirekte Trigger-Ketten

Watcher sind ausschließlich erlaubt für:
- UI-Synchronisation
- klar isolierte, lokale Reaktionen

---

## 4. Kein IO in Vue

`.vue`-Dateien **dürfen keine IO-Operationen enthalten**.

Verboten:
- fetch / API Calls
- WebSocket Command Construction
- OPFS / IndexedDB Zugriff
- direkte Nutzung von Crypto APIs

Alle IO **muss** über dedizierte Service-/Runtime-Module laufen.
Der UI‑Layer darf IO nur **triggern**, nicht implementieren.

---

## 5. Component ist kein Orchestrator

Eine Vue-Komponente **darf keine Runtime-Steuerung übernehmen**.

Verboten:
- Koordination mehrerer Flows
- Retry-/Ack-/Timeout-Handling
- Session-/Conversation-State-Maschinen
- Dedupe-Logik

Wenn solche Logik existiert, **muss** sie in ein Runtime-Modul ausgelagert werden.

---

## 6. Verbindliche Modulstruktur bei Refactors

Große Komponenten **müssen** entlang klarer Verantwortungen zerlegt werden.

Erlaubte Zielstruktur (Beispiel):

- `Component.vue`
  - UI + Binding

- `componentRuntime.ts`
  - Orchestrierung / Flow-Steuerung

- `componentState.ts`
  - In-Memory State / Maps / State-Machine

- `componentActions.ts`
  - explizite Actions (z. B. sendMessage, startTransfer)

- `componentStorage.ts`
  - Storage IO

- `componentCrypto.ts`
  - Crypto-Logik

- `componentInbound.ts`
  - Event-Handling

- `componentOutbound.ts`
  - Send-/Dispatch-Logik

Nicht jede Komponente braucht alle Module,
aber die Struktur **muss konsistent zu bestehenden Patterns sein**.
Für kleine Komponenten gilt die Struktur als Guideline, nicht als Pflicht.

Zusatzregeln:
- **Single Runtime Entry**: genau eine Runtime/Facade pro Feature.
- **State‑Module bleiben dumm**: nur State/Maps/Refs/Transitions, keine IO/Crypto/Side‑Effects.
- **Inbound/Outbound trennen**: Event‑Handling und Send/Dispatch nicht mischen.

---

## 7. Runtime Thinness (bei extrahierten Runtimes)

Eine Runtime/Facade koordiniert Ablaufreihenfolge und delegiert.
Sie darf keine eigenständigen fachlichen Entscheidungsblöcke implementieren.

Wenn eine Funktion in der Runtime:
- eigene Entscheidungslogik enthält (Policy, Gating, Retry, State‑Transitions)
- oder unabhängig testbar wäre

dann gehört sie in ein eigenes Modul.

Große Closures mit eigener Verantwortung dürfen nicht in der Runtime verbleiben.

---

## 8. Composable-Regel

`useXxx()`-Composables **dürfen keine Domain- oder Runtime-Logik enthalten**.

Verboten:
- Storage-Zugriff
- Crypto
- komplexe Orchestrierung
- Netzwerk-Logik

Composables sind ausschließlich erlaubt für:
- Vue-Reaktivität
- UI-nahe State-Verknüpfung

Alles andere gehört in `.ts`-Module.
Kurz: `useXxx()` bindet UI‑State, es **entscheidet nicht** über Business‑Flows.

---

## 9. Keine versteckten Datenflüsse

Datenflüsse **müssen explizit sein**.

Verboten:
- implizite State-Änderungen über Watcher-Ketten
- mehrere konkurrierende Schreibpfade
- Seiteneffekte ohne klaren Einstiegspunkt

Jede Mutation muss:
- nachvollziehbar
- eindeutig zuordenbar
sein.

---

## 10. Template-Regel

Templates dürfen keine Logik enthalten.

Verboten:
- komplexe Ausdrücke
- Inline-Transformationen (map/filter/reduce)
- verschachtelte Entscheidungslogik

Erlaubt:
- einfache Bindings
- einfache Formatierungen
- vorberechnete Werte aus `.ts` oder computed

---

## 11. Refactor-Regel für Vue

Ein Refactor **muss**:

1. Verantwortungen trennen
2. Logik aus `.vue` entfernen
3. IO/Storage/Crypto extrahieren
4. `.vue` auf UI reduzieren

Verboten:
- nur Methoden innerhalb derselben `.vue` aufzuteilen
- ohne echte Verantwortungs-Trennung

---

## 12. Refactor Completeness (Vue)

Ein Refactor gilt als unvollständig, wenn:
- die Hauptdatei weiterhin mehrere klar trennbare fachliche Blöcke enthält
- oder große Closures mit eigener Verantwortung bestehen bleiben

In diesem Fall muss der Refactor weitergeführt werden,
auch wenn die Datei bereits deutlich kleiner geworden ist.

---

## 13. Größe ist kein Ziel

Ziel ist:
- klare Verantwortungen
- keine Mischlogik

Eine große Datei ist erlaubt,
wenn sie ausschließlich UI enthält.

Eine kleine Datei ist falsch,
wenn sie mehrere Schichten mischt.

---

## 14. Testbarkeit

Alle nicht-triviale Logik **muss außerhalb von Vue existieren**.

Grund:
- isolierte Tests
- reproduzierbares Verhalten
- Framework-Unabhängigkeit

Vue-Dateien dürfen keine Logik enthalten,
die nur über UI testbar ist.

---

## 15. Verbotene Patterns

❌ Business-Logik in `.vue`  
❌ IO in `.vue`  
❌ Crypto in `.vue`  
❌ State-Maschinen in `.vue`  
❌ Watcher als Orchestrator  
❌ Composables als God-Objects  
❌ parallele Logikpfade in UI und Service  

---

## 16. Kernaussage

`.vue` ist Adapter, nicht Systemkern.

Alle relevanten Systementscheidungen passieren außerhalb von Vue.
