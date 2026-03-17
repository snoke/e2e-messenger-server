# Offline Delivery

## Scenario
- Sender is online.
- Recipient is offline.
- Message must be persisted and retrievable later.

## Flow
1. Sender sends `chat_send`.
2. Symfony persists CHK ciphertext.
3. Recipient later reconnects and requests history.
4. Recipient decrypts history using CHK.

## Notes
- No live MLS delivery is possible while offline.
- History is the source of truth for offline delivery.

Related:
- `docs/workflows/history-reload.md`
- `docs/crypto/chk.md`
