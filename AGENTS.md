# AGENTS.md
# Architektur- und Sicherheitsregeln für Codex / Agenten

Dieses Projekt folgt einer MLS-first Sicherheitsarchitektur sowie einer
Domain Driven Design / Hexagonal Architecture Backend-Struktur auf Basis
moderner Symfony-Best-Practices.

Der Agent darf keine Änderung implementieren, die diese Regeln verletzt.

Alle Änderungen müssen diese Architektur vereinfachen oder stärken.

------------------------------------------------------------
GRUNDPRINZIPIEN
------------------------------------------------------------

• Sicherheit vor Bequemlichkeit
• Einfachheit vor Cleverness
• Domänenmodell vor Frameworklogik
• Eine Lösung pro Problem, keine Parallelpfade
• Explizite Modelle statt impliziter Seiteneffekte

------------------------------------------------------------
TEIL 1 — KRYPTOGRAFIE- UND MLS-ARCHITEKTUR
------------------------------------------------------------

1. Keine neuen Kryptopfade
Der Agent darf keine alternativen Kryptopfade einführen.
Interne Kommunikation erfolgt ausschließlich über MLS.

2. Interne Kommunikation ist immer eine MLS-Gruppe
Alle internen Kommunikationskontexte sind MLS-Gruppen.

3. 1:1-Chats sind Gruppen
Direct-Chats werden immer als Gruppe mit zwei Teilnehmern modelliert.

4. Kryptografische Mitglieder sind Geräte
MLS-Membership erfolgt auf Device-/Client-Ebene.
User sind nur logische Identitäten.

5. Keine stillen Fallbacks
Wenn MLS nicht möglich ist, darf kein automatischer Fallback erfolgen.

Unzulässig sind:
- Legacy-Fallbacks
- Double-Ratchet-Fallbacks
- Prekey-Fallbacks
- unverschlüsselte Alternativen

6. Public-Ingress ist separate Sicherheitsdomäne
Public Dropbox oder anonyme Einsendungen sind kein MLS-Kontext.

Sie verwenden eigene Envelope-Verschlüsselung.

7. Control Plane und Data Plane sind getrennt
MLS regelt nur:

- Membership
- Gruppenzustand
- Commit / Epoch
- Schlüsselverteilung

Blob-Transport und Dateidaten gehören nicht zur Control Plane.

8. Dateien haben eigene File Keys
Dateien dürfen niemals direkt mit Gruppenschlüsseln verschlüsselt werden.

9. Storage verwendet Key-Graph-Modell

Schlüsselstruktur:

ProjectKey
  ↓
FolderKey
  ↓
FileKey

10. Keine MLS-Gruppe pro Datei
Der Agent darf nicht automatisch eine neue MLS-Gruppe pro Datei erzeugen.

11. Membership-Änderungen sind Events
Join, Remove, Update müssen explizite Ereignisse sein.

Implizite Seiteneffekte sind verboten.

12. Server ist kein Klartext-Vertrauensanker
Der Server darf keine geheimen Inhalte kennen müssen,
wenn diese clientseitig geschützt werden können.

13. Architektur darf nicht in String-Labels versteckt werden
Felder wie

crypto_profile
mode
strategy
type

dürfen keine versteckten Architekturentscheidungen tragen.

14. Keine unnötige Systemkomplexität
Änderungen dürfen keine zusätzlichen Modi,
Zustände oder Varianten erzeugen ohne zwingenden Grund.

15. Private Keys verlassen nie das Gerät
Private Schlüssel dürfen niemals im Klartext übertragen
oder serverseitig gespeichert werden.

16. Recovery-Material wird niemals im Klartext gespeichert
Recovery Codes und Key Backups müssen verschlüsselt sein.

17. Sicherheitsänderungen müssen Failure-Szenarien prüfen

Mindestens:

- Geräteverlust
- Replay-Angriffe
- Commit-Race-Conditions
- doppelte Membership
- teilweise Zustellung

18. Legacy-Sicherheitslogik wird entfernt
Wenn ein Sicherheitsmechanismus ersetzt wird,
muss der alte Code entfernt oder deaktiviert werden.

19. Sicherheitsinvarianten müssen serverseitig geprüft werden
Der Server darf sich nicht ausschließlich auf Client-Logik verlassen.

20. Architektur muss einfach erklärbar bleiben

Die Sicherheitsarchitektur muss in wenigen Sätzen erklärbar sein:

Alle internen Teilnehmerbeziehungen sind MLS-Gruppen.
Geräte sind kryptografische Mitglieder.
Dateien verwenden Envelope-Key-Graph-Verschlüsselung.
Public-Ingress-Flows sind separate Sicherheitsdomänen.

Wenn eine Änderung dieses Modell komplizierter macht,
darf sie nicht implementiert werden.

------------------------------------------------------------
TEIL 2 — SYMFONY / DOMAIN DRIVEN DESIGN ARCHITEKTUR
------------------------------------------------------------

21. Domäne vor Framework
Geschäftslogik gehört niemals in:

- Controller
- Doctrine Repository
- Event Subscriber
- Messenger Handler

Geschäftslogik gehört in Domain- oder Application-Layer.

22. Objektorientierung ist Pflicht
Neue Funktionalität muss objektorientiert modelliert werden.

Prozedurale Helferketten oder God-Services sind unzulässig.

23. Hexagonale Architektur einhalten

Code ist klar zu trennen in:

Domain
Application
Infrastructure
Interface

24. Domain kennt kein Symfony
Domain-Code darf keine Abhängigkeiten auf Symfony haben.

Unzulässig:

Request
Response
Controller
Messenger
EntityManager
Serializer

25. Domain kennt keine Infrastruktur
Die Domain kennt keine Datenbank,
kein HTTP und keine externen APIs.

Nur Interfaces / Ports sind erlaubt.

26. Use Cases gehören in Application Layer
Jeder fachliche Anwendungsfall wird als Application Service modelliert.

Beispiele:

OpenConversation
AddGroupMember
SubmitDropboxMessage

27. Messenger Handler bleiben dünn
Handler dürfen nur delegieren.

Keine Geschäftslogik im Handler.

28. Entry Points(Controller/EventListener) bleiben dünn

Sie dürfen nur:

- Request entgegennehmen
- DTO erzeugen
- Use Case aufrufen
- Response zurückgeben

29. Route Attributes statt routes.yaml
Neue Routen werden mit PHP Attributes definiert.

30. Constructor Injection statt Container-Zugriff
Abhängigkeiten werden per Konstruktor injiziert.

Service Locator ist verboten.

31. Value Objects statt primitiver Datentypen

Beispiele:

ConversationId
DeviceId
WorkspaceId
CryptoProfile

Primitive Strings sind zu vermeiden.

32. Entities schützen ihre Invarianten
Entities dürfen keine passiven Datencontainer sein.

Setter-Wüsten sind verboten.

33. Keine anämischen Doctrine Entities
Entities müssen Verhalten enthalten,
nicht nur Getter und Setter.

34. Repository Interfaces gehören zur Domain
Interfaces werden in Domain oder Application definiert.

Implementierungen gehören in Infrastructure.

35. Infrastructure implementiert Ports
Adapter für:

- Datenbank
- Mail
- HTTP APIs
- Queue
- Storage

liegen ausschließlich in Infrastructure.

36. Keine untypisierten Arrays zwischen Schichten
Statt Arrays sollen verwendet werden:

DTOs
Commands
Queries
Value Objects

37. Commands und Queries sind explizit

Beispiele:

CreateWorkspaceCommand
GetConversationQuery

Nicht:

handle(array $data)

38. Keine Businesslogik in Doctrine Lifecycle Hooks

Unzulässig:

prePersist
postLoad
preUpdate

für Geschäftslogik.

39. Transaktionen gehören in den Application Layer
Transaktionsgrenzen müssen explizit gesetzt werden.

40. Architekturklarheit vor Cleverness
Keine unnötigen Meta-Abstraktionen,
Framework-Spielereien oder übergenerische Basisklassen.

Lesbarkeit und Domänenklarheit haben Vorrang.

------------------------------------------------------------
TEIL 3 — DUPLIKATE, OBSOLETES UND SERVICE-SCHNITT
------------------------------------------------------------

41. Keine duplizierte Fachlogik
Bestehende fachliche Logik darf nicht an anderer Stelle kopiert oder leicht abgewandelt neu implementiert werden.

Wenn ähnliche Logik bereits existiert, muss der Agent:
- die bestehende Implementierung finden
- prüfen, ob sie erweitert werden kann
- die Logik zentralisieren statt zu duplizieren

42. Bestehende Logik erweitern statt parallel nachbauen
Wenn ein ähnlicher Service, Use Case, Resolver, Factory oder Mapper bereits existiert,
darf kein zweiter fast gleicher Baustein eingeführt werden.

Bestehende zentrale Stellen sind zu bevorzugen, sofern sie architektonisch passend sind.

43. Obsolet gewordener Code ist zu entfernen
Wenn eine neue Implementierung eine alte ersetzt,
muss die alte Implementierung entfernt oder hart deaktiviert werden.

Unzulässig sind:
- tote Legacy-Pfade
- ungenutzte Helper
- veraltete alternative Services
- „vorsichtshalber behaltene“ Altlogik

44. Keine parallelen Wahrheiten
Für einen fachlichen Ablauf darf es nicht mehrere konkurrierende Implementierungen geben.

Es muss immer klar sein:
- welche Klasse zuständig ist
- welcher Service der führende Einstiegspunkt ist
- welche Logik obsolet ist

45. Verantwortlichkeiten intelligent auslagern
Wenn Logik wächst oder mehrfach gebraucht wird,
muss sie in einen passend benannten Service, Use Case, Domain Service oder Value Object ausgelagert werden.

Nicht auslagern in:
- generische Helper-Klassen
- Utility-Sammelklassen
- statische Globalfunktionen

46. Auslagerung nur mit klarer Verantwortung
Neue Services dürfen nur entstehen, wenn ihre Verantwortung klar benennbar ist.

Unzulässig sind unscharfe Klassen wie:
- CommonHelper
- DataManager
- AppService
- GeneralUtils
- Processor
ohne klaren fachlichen Fokus

47. Keine künstliche Service-Explosion
Nicht jede Kleinigkeit rechtfertigt einen neuen Service.

Der Agent muss vor Auslagerung prüfen:
- ist es echte wiederverwendbare Fachlogik?
- verbessert es Lesbarkeit und Architektur?
- verhindert es Duplikation?
- ist die Verantwortung klar?

48. Keine Copy-Paste-Variation
Wenn Code nur kopiert wird, um kleine Unterschiede einzubauen,
muss stattdessen ein gemeinsames Modell, ein sauberer Service oder ein klarer Erweiterungspunkt geschaffen werden.

49. Refactoring vor Neuimplementierung
Bevor neue Logik hinzugefügt wird, muss geprüft werden,
ob bestehender Code durch Refactoring in eine elegantere gemeinsame Form überführt werden kann.

50. Jede neue Klasse braucht einen klaren Mehrwert
Der Agent darf keine neue Klasse, keinen neuen Service und keine neue Abstraktion einführen,
wenn dadurch nur bestehende Logik umbenannt oder verteilt wird, ohne die Architektur wirklich zu verbessern.

------------------------------------------------------------
TEIL 5 — FRONTEND/BACKEND PLUGIN-SPIEGELUNG (DDD)
------------------------------------------------------------

61. Fachliche Plugins sind Bounded Contexts
Jede größere fachliche Funktion wird als Plugin bzw. Modul
(Bounded Context) modelliert.

Beispiele:

Conversation
Group
Call
Dropbox
Storage
Device

Diese Module definieren klare fachliche Grenzen.

62. Frontend und Backend spiegeln fachliche Plugins

Wenn ein Plugin Backendlogik benötigt, muss es sowohl im
Backend als auch im Frontend in eigener Domäne existieren.

Die Ordnerstruktur muss fachlich gespiegelt sein.



63. Gleiche Namen für gleiche fachliche Kontexte

Frontend und Backend müssen dieselbe Ubiquitous Language
für Plugins verwenden.

Unzulässig:

Backend: PublicInbox
Frontend: AnonymousUpload
API: ExternalSubmit

Erlaubt:

Conversation
Group
Call
Dropbox
Device
Workspace

64. Plugins enthalten vollständige Schichten

Jedes Plugin soll klar getrennte Schichten besitzen.

Backend:

Domain
Application
Infrastructure
Interface

Frontend:

domain
application
infrastructure
ui

65. Keine fachliche Logik außerhalb eines Plugins

Neue Geschäftslogik darf nicht in generischen Ordnern landen.

Unzulässig:

services/
helpers/
utils/
common/

Wenn eine Funktion zu einem fachlichen Kontext gehört,
muss sie im entsprechenden Plugin liegen.

66. Infrastruktur darf pluginübergreifend sein

Gemeinsame Infrastruktur darf zentral liegen.

Beispiele:

http client
websocket transport
crypto primitives
storage adapters

Fachlogik jedoch nicht.

67. Plugins sind isolierte Bounded Contexts

Plugins dürfen nur über definierte Schnittstellen miteinander
interagieren.

Direkte Imports zwischen Domain-Layern verschiedener Plugins
sind zu vermeiden.

68. Backend und Frontend müssen dieselbe Domänensprache sprechen

Domainbegriffe müssen identisch sein z.B.:

Conversation
Message
Member
Device
Workspace
FileKey
DropboxSubmission

69. Neue Plugins müssen bewusst eingeführt werden

Der Agent darf kein neues Plugin erzeugen, ohne vorher zu prüfen:

- existiert bereits ein passender Kontext?
- gehört die Funktion zu einem bestehenden Plugin?

70. Änderungen an einem Plugin müssen beide Seiten berücksichtigen

Wenn ein Plugin fachlich geändert wird, muss geprüft werden,
ob entsprechende Anpassungen im gespiegelt vorhandenen
Frontend- oder Backend-Modul notwendig sind.

------------------------------------------------------------
TEIL 4 — TRANSPORT-ARCHITEKTUR (WEBSOCKET-ONLY GATEWAY)
------------------------------------------------------------

51. Frontend kommuniziert ausschließlich über das WebSocket-Gateway

Das Frontend darf ausschließlich über das zentrale WebSocket-Gateway
mit dem Backend kommunizieren.

HTTP-basierte API-Aufrufe zwischen Frontend und Symfony sind verboten.

Unzulässig sind insbesondere:

fetch()
axios
XMLHttpRequest
REST-API-Aufrufe
GraphQL über HTTP

Alle Anwendungsfälle müssen über WebSocket-Nachrichten erfolgen.

52. Gateway ist der einzige Kommunikationskanal

Das WebSocket-Gateway ist der einzige Entry Point
für Client → Backend Kommunikation.

Alle Nachrichten müssen über das Gateway laufen.

Der Agent darf keine zusätzlichen Kommunikationskanäle einführen.

53. Backend-Logik darf keine HTTP-API für das Frontend bereitstellen

Das Symfony-Backend stellt keine REST- oder HTTP-API
für das Frontend bereit.

HTTP darf ausschließlich verwendet werden für:

- statische Assets
- Initiale Anwendungsauslieferung
- optionale externe Integrationen

Nicht für interne Frontend-Kommunikation.

54. Jede Client-Aktion ist eine Gateway-Nachricht

Alle Interaktionen zwischen Frontend und Backend
werden als explizite Nachrichten modelliert.

Beispiele:

OpenConversation
SendChatMessage
AddGroupMember
SubmitDropboxMessage

Diese Nachrichten werden über das WebSocket-Gateway
an entsprechende Application-Use-Cases weitergeleitet.

55. Gateway ist ein Adapter der Hexagon-Architektur

Das WebSocket-Gateway gehört zur Interface-Schicht.

Es darf nur:

- Nachrichten entgegennehmen
- DTOs erzeugen
- Application Use Cases aufrufen
- Ergebnisse zurücksenden

Es darf keine Geschäftslogik enthalten.

56. Keine direkte Infrastrukturkopplung im Frontend

Frontend-Code darf nicht direkt mit Backend-Endpunkten
oder Datenbanken interagieren.

Alle Backendinteraktionen müssen über:

GatewayClient
WebSocketTransport
oder entsprechende Infrastrukturadapter erfolgen.

57. Nachrichten sind explizit typisiert

Gateway-Nachrichten müssen klar definierte Typen besitzen.

Beispiele:

SendChatMessage
OpenConversation
AddDevice
SubmitDropboxMessage

Unzulässig sind unstrukturierte Nachrichten wie:

{ action: "doSomething", payload: {...} }

58. Keine versteckten Netzwerkaufrufe

Der Agent darf keine Netzwerkaufrufe in:

UI-Komponenten
Composables
Utility-Funktionen

verstecken.

Alle Netzwerkkommunikation muss über
klar definierte Gateway-Adapter erfolgen.

59. Netzwerktransport gehört zur Infrastructure-Schicht

Im Frontend liegt WebSocket-Transport ausschließlich in:

infrastructure/gateway/
oder
infrastructure/transport/

UI, Domain und Application dürfen keine direkten
Transportdetails kennen.

60. Architektur-Invariante

Die Transportarchitektur lautet:

Frontend
  → WebSocket Gateway
  → Symfony Entry Point
  → Application Use Case

Es existiert kein alternativer Kommunikationspfad.