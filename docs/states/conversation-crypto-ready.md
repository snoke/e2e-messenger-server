# Conversation Crypto Ready

Conversation readiness is **per conversation** and depends on a CHK being available and usable.

## States
- `pending_key_init`: waiting for CHK wrap or unwrap
- `crypto_ready`: CHK available, history decryptable
- `crypto_error`: key failure or invariant violation

## Entry Conditions
- `pending_key_init` is set when a conversation opens without a ready CHK.
- `crypto_ready` is set after successful unwrap.
- `crypto_error` is set when unwrap fails or wrap is missing at accept time.

## UI Effects
- `pending_key_init`: message input disabled, history hidden, status message shown
- `crypto_ready`: full chat UI enabled
- `crypto_error`: input disabled, error state shown

## Related
- Invite/accept flow: [`docs/workflows/invite-accept.md`](../workflows/invite-accept.md)
- CHK lifecycle: [`docs/crypto/chk.md`](../crypto/chk.md)