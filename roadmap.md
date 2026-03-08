Wenn du einmal eine Client-seitige Crypto-Layer + Key-Identity-System gebaut hast (Public-Key-Identity, E2E-Encryption, Key-Exchange, AEAD), dann kannst du daraus ziemlich viele Produkte ableiten. Das ist im Grunde eine Zero-Knowledge-Plattform. 🔐
Diese Produkte nennen wir bei uns plugins.

💬 Kommunikation

1. E2E Messenger
	•	dein ursprüngliches Projekt
	•	Text / Voice / Files

2. Secure Email Gateway
	•	E2E-verschlüsselte Mail zwischen Nutzern
	•	ähnlich wie Proton Mail
	•	Keys = Benutzeridentität

3. Encrypted Voice / Video Calls
	•	WebRTC + E2E Keys
	•	zusätzlicher Layer über Transport

4. Anonymous Drop Box
	•	jemand kann dir Dateien senden ohne Account
	•	Public Key = Empfangsadresse

⸻

📁 Zero-Knowledge Storage

5. Encrypted Cloud Drive User Storage
	•	Client verschlüsselt Dateien
	•	Storage: S3 / object store
	•	ähnlich wie Tresorit
	
7. Encrypted File Sharing
	•	temporäre Links
	•	Key-based access


6. Secure Backup
	•	verschlüsselte Geräte-Backups
	•	Schlüssel nur lokal


⸻

🔑 Secrets & Identity

9. Passwort-Manager
	•	Keys lokal generiert
	•	Sync über verschlüsselten Storage

Beispiel:
Bitwarden

10. Secret Vault für Entwickler
	•	API Keys
	•	Zertifikate
	•	Tokens

11. Secure Notes
	•	verschlüsselte Notizen
	•	Markdown / Docs

12. Key-Identity Accounts
	•	Login über Public Key
	•	kein Passwort nötig

    ===
    subnotes:
    ===
    aktuell ist Encrypted Voice / Video Calls als unterteil vom Messenger implementiert, 
    dies soll künftig ein eigenes plugin sein.
    der Messenger behällt die funktion in der ui aber integriert, indem er dort wieder das Voice / Video Calls plugin nutzt.
	Änhlich soll dann Anonymous Drop Box und Encrypted File Sharing wiederum
	das plugin "Encrypted Cloud Drive User Storage" nutzen