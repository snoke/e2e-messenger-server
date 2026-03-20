# User Storage: File-Only Storage (No Chunking)

Status: Binding standard for UserStorage and Vue-Finder uploads.

## Motivation
UserStorage persists **whole encrypted files only**. Chunking is reserved for
file transfer flows. This removes partial chunk state, simplifies recovery, and
prevents chunk artifacts from being stored in cloud backends.

## Hard Cut (No Legacy Support)
- **No legacy chunk support.**
- **No resume logic.**
- **No migration.**
- Existing storage is expected to be reset (empty).

## Storage Layout (Backend)
Each attachment is stored as a **single ciphertext file** plus metadata:

- `users/<ownerHash>/files/<attachmentId>/meta.json`
- `users/<ownerHash>/files/<attachmentId>/payload.b64`

There are **no** per-chunk files or `chunks/` directories for UserStorage.

If the primary backend is remote (Dropbox, Google Drive, etc.), uploads are
staged locally and flushed on finalize. The staged file is still a **single**
payload file (no chunk files).

## Realtime Protocol (UserStorage)
The protocol is file-only and uses **file payload** naming:

- `user_storage_upload_init`
  - Returns `attachment_id`, optional quota fields.
- `user_storage_upload_payload`
  - Sends the **entire ciphertext** as one payload.
- `user_storage_upload_finalize`
  - Marks the file ready and flushes to primary storage if needed.
- `user_storage_download`
  - Returns the single ciphertext payload.
- `user_storage_share_download`
  - Returns the single ciphertext payload for a share token.

## Frontend Behavior
- UserStorage uploads encrypt **one payload** and send `user_storage_upload_payload` once.
- Downloads fetch **one payload** and decrypt it.
- No chunk sizing, no chunk indexes, no resume or missing-chunk checks.

## Key Wrapping (OPFS Managed Files)
Local OPFS managed files (e.g., VueFinder/UserStorage UI and FileTransfer persist)
use per-file keys wrapped by the **User Vault Key (UVK)**. This keeps files
readable across device sessions. Legacy device-bound wrapping is not supported.

## Exception: Transfer Temp Files
Chunked **temporary** files are allowed in OPFS **only** for transfer flows
(e.g., live file transfer). UserStorage itself does not use chunked storage.
