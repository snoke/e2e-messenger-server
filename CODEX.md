# CODEX.md

## Harte Leitplanken (verbindlich)

- Bevorzuge bestehende zentrale Stellen vor neuer Parallel-Logik.
- Refactoring vor Neuimplementierung.
- Keine impliziten Routing- oder Security-Fallbacks.
- Keine Parallelpfade für dieselbe Fachfunktion.
- Keine fachliche Kernlogik im Gateway.
- Neue Klassen nur mit klarer Verantwortung und erkennbarem Mehrwert.

## Arbeitsweise

- Erst Architektur und bestehende Flows lesen, dann ändern.
- Kleine, überprüfbare Schritte statt großer Umbauten.
- Kompatibilität des bestehenden Wire-Protokolls standardmäßig erhalten.
- Nur abstrahieren, wenn es echten Entkopplungs- oder Wiederverwendungsgewinn gibt.
- Copy-Paste-Varianten vermeiden.