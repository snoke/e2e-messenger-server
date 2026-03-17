# Tech Debt: Call- vs. Chat-Krypto, MLS-Optionen und User-Flow-Folgen

## 1) Wie Calls es aktuell löst

**Kurzfassung**
- LiveKit transportiert Media-Streams.
- Optionales Media-E2EE läuft über Insertable Streams (SFrame-ähnlich).
- **Media-Keys werden über MLS-geschützte Control-Conversations verteilt**.
- Keine Persistenz von Media-Keys; alles ist **live/ephemeral**.

**Details (vereinfacht)**
- Beim Call wird ein Media-Key erzeugt.
- Der Media-Key wird **per MLS verschlüsselt** (`call_media_key`) über den Control-Conversation-Kanal gesendet.
- Empfänger entschlüsseln live und aktivieren E2EE für Streams.
- **Es gibt keine History/Storage-Anforderung** für Media-Keys.

**Implikation**
- Das Modell ist **sauber für Live**.
- Es ist **nicht geeignet für History** oder späte Geräte/Reloads.

## 2) Wie Chat es aktuell löst

**Kurzfassung**
- MLS bleibt **Live-Transport** (Realtime).
- History/Storage wird **mit CHK** verschlüsselt.
- **CHK wird user-bound** und serverseitig als Wrap gespeichert.
- **Invite pre‑provisioniert** den Wrap; **Accept liefert ihn direkt** zurück.
- `conversation_key_fetch` ist **Recovery**, nicht Normalfall.

**Details (vereinfacht)**
- Live-Message: MLS encrypt → Realtime Transport.
- Storage-Message: CHK encrypt → DB.
- CHK wird pro Member **gewrappt** und serverseitig gespeichert.
- **Invite** erzeugt den Wrap; **Accept** liefert ihn zurück.
- Neue Geräte nutzen `conversation_key_fetch` **nur als Recovery**.

**Implikation**
- History ist **stabil und reload/device-unabhängig**.
- MLS-State muss **nicht** für History erhalten bleiben.
- **Accept = Access + Key‑Delivery** (kein post‑accept Race).

## 3) Was wäre ein Umbau auf MLS-only History?

### Option A: History komplett mit MLS (keine CHK)

**Aufwand**: Sehr hoch.

**Probleme**
- MLS-Keys sind **ephemeral** und epoch-basiert.
- Nach Reload / Device-Wechsel fehlen die alten Secrets → **History nicht lesbar**.
- Das ist das bekannte Problem: **“Desired gen in the past”**.

**Folge**
- Man müsste MLS-States/Secrets langfristig speichern → bricht Forward Secrecy.
- Oder alte Epochen persistent sichern → extrem komplex.

### Option B: Storage-Keys pro MLS-Epoch

**Aufwand**: Hoch bis sehr hoch.

**Vorteile**
- Besserer Schadensradius (Rotation bei Membership-Changes).

**Nachteile**
- Du brauchst dennoch **persistente Epoch-Keys**, sonst History weg.
- Verteilung + Persistenz wird komplexer als 1 CHK.

**Fazit**
- Ohne Persistenz bleibt das alte Problem.
- Mit Persistenz baust du effektiv wieder CHK-ähnliche Logik.

### Option C: MLS nur für Key-Distribution, Storage-Keys persistent user-bound (Hybrid)

**Aufwand**: Mittel.

**Modell**
- MLS transportiert Storage-Keys live (schneller Pfad).
- **Source of Truth bleibt persistente Wraps** (serverseitig, user-bound).

**Bewertung**
- Funktioniert, solange MLS **nicht** die einzige Quelle ist.
- Für neue Devices bleibt `conversation_key_fetch` der sichere Weg.

## 4) User-Flow-Folgen (Signup, Sign-in, Device Change, Reload)

### Current (CHK + user-bound)

**Signup**
- Device-Key Auth → Session
- UVK/Vault init
- User Key erzeugen + sichern
- CHK wird bei Invite vorbereitet und bei Accept geliefert

**Sign-in**
- Device-Key Auth → Session
- Vault fetch → UVK unlock
- User Key unwrap → Accept liefert CHK (Fetch nur Recovery)

**Device Change**
- Neues Device auth
- Vault unlock → User Key verfügbar
- `conversation_key_fetch` (Recovery) → History lesbar

**Reload**
- Session + Vault unlock
- CHK fetch (Recovery) → History lesbar

**Ergebnis**
- **History ist stabil und user-bound**.

### MLS-only History (Option A)

**Signup/Sign-in**
- Session ok, aber History hängt an MLS-State

**Device Change / Reload**
- **History fehlt**, weil MLS-Secrets nicht persistiert.

**Ergebnis**
- **User-Flow bricht** (History nicht verlässlich).

### MLS + Epoch-Keys (Option B)

**Device Change / Reload**
- Nur ok, wenn alle Epoch-Keys **persistiert & verteilt** werden.

**Ergebnis**
- Komplexer als CHK, gleiche Persistenz-Anforderung.

### Hybrid (Option C)

**Device Change / Reload**
- Funktioniert, wenn serverseitige Wraps verfügbar sind.

**Ergebnis**
- Stable, aber MLS ist nur „schneller Pfad“, nicht Source of Truth.

## 5) Gibt es „smarte“ Lösungen?

**Kurz: Nur wenn Persistenz garantiert bleibt.**

Smarte/tragfähige Varianten:
- **CHK pro Conversation** (status quo, invite‑preprovisioniert) → simpel, stabil.
- **CHK-Rotation bei Membership** → höherer Aufwand, besserer Schadensradius.
- **Hybrid (MLS live + persistente Wraps)** → ok, aber Source of Truth bleibt Persistenz.

Nicht smart/robust:
- **MLS-only History ohne Persistenz** → History bricht bei Reload/Device-Wechsel.
- **MLS-States langfristig speichern** → Forward Secrecy verwässert, hoher Aufwand.

## 6) Fazit / Empfehlung

- Calls ist sauber, **weil es nur Live-Keys braucht**.
- Chat braucht **persistente Storage-Keys** für History.
- MLS-only History würde den User-Flow verschlechtern.
- Der aktuelle CHK-Ansatz ist **architektonisch korrekt**.
- Optionaler Ausbau: **CHK-Rotation bei Membership-Changes**.