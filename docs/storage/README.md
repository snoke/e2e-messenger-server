# Storage

This section documents storage policies and formats.

## Files
- User storage (file-only): [docs/storage/user-storage-file-only.md](user-storage-file-only.md)

## Principles
- Storage payloads are always encrypted client-side.
- Server stores ciphertext and metadata only.
- OPFS managed files are encrypted with per-file keys wrapped by the **User Vault Key (UVK)**.
