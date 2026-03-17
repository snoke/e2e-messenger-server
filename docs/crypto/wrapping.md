# Wrapping & Distribution

## Wrapping Rules
- Wrapping is **client-side only**.
- Server never sees plaintext CHK.
- A wrap is user-specific, using the invitee's `user_key_public`.

## Algorithms
- User key wrapping: `user_ecdh_p256_hkdf_sha256_aes_gcm_256`.

## Wrapped CHK Payload
The wrapped payload is JSON with:
- `v`: version
- `epk`: ephemeral public key
- `nonce`: AES-GCM nonce
- `ciphertext`: wrapped CHK bytes

Example shape:

```json
{"v":1,"epk":"...","nonce":"...","ciphertext":"..."}
```

## Distribution Paths
- Invite-time pre-provisioning is the normal path.
- Fetch is recovery only, blocked for pending members.

## Related
- CHK: [`docs/crypto/chk.md`](chk.md)
- Keys & vault: [`docs/crypto/keys-and-vault.md`](keys-and-vault.md)