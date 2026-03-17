# Crypto Matrix

| Use Case | Algorithm | Key | Scope | Server Visibility |
|---|---|---|---|---|
| Live chat transport | MLS | MLS epoch keys | Conversation (live) | Ciphertext only |
| History storage | AES-GCM | CHK | Conversation (history) | Ciphertext only |
| CHK wrapping | ECDH + HKDF + AES-GCM | User key | User | Wrapped only |
| Vault encryption | AES-KW / AES-GCM | UVK | User | Wrapped only |

Notes:
- MLS and CHK are separate domains.
- Server never sees plaintext keys.
