# Engineering Standards

Dieses Dokument definiert, wie Tasks geplant, umgesetzt, validiert und abgeschlossen werden. Ziel ist **klare Architektur, nachvollziehbare Änderungen und verlässliche Releases**.

---

## Prinzipien

1. Fix root cause, not symptoms.
2. Remove workarounds after fixing the root cause.
3. One clear flow per behavior. No parallel logic.
4. Every change must be understandable in isolation.
5. Prefer simplicity over cleverness.
6. Consistency beats optimization.

---

## Project Guardrails (verbindlich)

Diese Regeln spiegeln die projektweiten Leitplanken wider (siehe `CODEX.md` und `AGENTS.md`).

1. **MLS‑first / Security**
   - Keine neuen Kryptopfade für interne Kommunikation.
   - Keine stillen Kryptofallbacks.
2. **Command‑Registry als Single Source of Truth**
   - Jeder Command ist registriert und einer Routing‑Klasse zugeordnet.
   - Unbekannte Commands werden abgelehnt.
3. **Gateway bleibt technisch**
   - Keine fachliche Kernlogik im Gateway.
4. **Authoritative Backend**
   - Kein fachlicher Bypass am Backend vorbei (siehe `docs/workflows/workflow-protocol.md`).
5. **Keine Parallelpfade**
   - Refactor vor Neuimplementierung.
   - Prefer deletion over addition.
6. **Wire‑Kompatibilität**
   - Bestehendes Wire‑Protokoll standardmäßig erhalten.
7. **Storage‑Regel**
   - Storage ist file‑only; Chunking ist **nur** für Transfer‑Flows.

---

## Task Classification

Jeder Task muss vor Beginn klassifiziert werden.

### Bugfix
1. Verhalten ist falsch, inkorrekt oder regressiv.
2. Ziel ist Wiederherstellung des erwarteten Verhaltens.

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

👉 Wenn mehrere Kategorien betroffen sind → aufteilen.

---

## Task Lifecycle

Jeder Task folgt diesem Ablauf:

### 1. Understand
- Was ist das Problem wirklich?
- Was ist die Root Cause?
- Welche Teile des Systems sind betroffen?
- Relevante Leitplanken lesen (z. B. `CODEX.md`, `AGENTS.md`, `docs/workflows/...`).

### 2. Define
- Was ist die Ziel-Behavior?
- Was ist explizit **nicht** Teil dieses Tasks?

### 3. Plan
- Welche minimalen Änderungen lösen das Problem?
- Gibt es bestehende Patterns, die genutzt werden sollten?

### 4. Implement
- Keine Workarounds
- Kein paralleler Codepfad
- Keine halben Lösungen

### 5. Validate
- Funktioniert der Flow vollständig?
- Gibt es Seiteneffekte?
- Sind alte Bugs wirklich weg?

### 6. Cleanup
- Alte Logik entfernen
- Dead Code löschen
- Temporäre Fixes entfernen

### 7. Commit
- Nur vollständige, funktionierende Änderungen committen
- Commit muss eigenständig verständlich sein
- Commit‑Format gemäß `docs/commit-standards.md`

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
✅ Entweder lösen oder entfernen  

---

### 4. Keep Changes Minimal
❌ „Ich mach das schnell noch mit“  
✅ Jeder Change hat klaren Scope  

---

### 5. Prefer Deletion Over Addition
- Wenn möglich: Code entfernen statt erweitern

---

## Architecture Consistency

1. Ähnliche Probleme → gleiche Lösung  
2. Keine neuen Patterns ohne Grund  
3. Bestehende Struktur respektieren  
4. Cross-repo Änderungen synchron halten  
5. Authoritative Flow beibehalten (Client → Gateway → Backend → Events)

---

## Multi-Repo Workflow

Repos: frontend, symfony, gateway

### Reihenfolge:
1. Änderungen pro Repo committen  
2. Repos einzeln pushen  
3. Parent Repo Submodule aktualisieren  

### Regeln:
- Keine gemischten Changes zwischen Repos  
- Konsistente Commit Messages  
- Keine gebrochenen Zwischenzustände  

---

## Definition of Done (Task Level)

Ein Task ist **nur dann fertig**, wenn:

1. Root Cause identifiziert und gelöst ist  
2. Kein Workaround mehr existiert  
3. Keine redundante Logik übrig ist  
4. Code konsistent mit Architektur ist  
5. Änderung vollständig getestet wurde  
6. Dokumentation aktualisiert ist (falls nötig)  
7. Commit(s) sauber und verständlich sind  

---

## Validation & Testing

1. Jede Änderung muss validiert werden  
2. Tests müssen dokumentiert werden (oder explizit „not run“ inkl. Begründung)  

Beispiele:
- Tests: manual login flow
- Tests: API request via curl
- Tests: not run (refactor, no behavior change)

---

## Anti-Patterns (Verboten)

❌ Quick fix ohne Root Cause  
❌ Dead Code behalten „für später“  
❌ Mehrere konkurrierende Lösungen  
❌ Unklare oder gemischte Commits  
❌ Halb implementierte Features  
❌ Magische Nebenwirkungen  

---

## Good Practices

✅ Kleine, vollständige Changes  
✅ Explizite Logik  
✅ Klare Datenflüsse  
✅ Konsistente Patterns  
✅ Verständliche Commit-History  

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
