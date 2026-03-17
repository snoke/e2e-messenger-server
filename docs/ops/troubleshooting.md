# Troubleshooting

## Common Symptoms
- `user_vault_fetch_timeout`
- `Secure channel initializing…`
- Missing notifications for inactive chats
- Messages visible in list but not in conversation view

## Checkpoints
- `symfony-consumer` logs
- `conversation_key_records` entries in DB
- WS logs for `group_membership_accept_ok` and `wrapped_chk`
- Frontend console logs for `[conversation_key]` and `[crypto_ready]`

## Fast Triage
1. Verify consumer is running.
2. Verify gateway and symfony containers are healthy.
3. Check WS logs for missing events.
4. Check DB for missing key wraps.

## Related
- Known errors: `docs/ops/known-errors.md`
- System behavior: `docs/overview/system-behavior.md`
