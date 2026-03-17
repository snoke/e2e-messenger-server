# Known Errors

| Error | Meaning | Fix |
|---|---|---|
| `user_vault_fetch_timeout` | Consumer not responding | Start `symfony-consumer` |
| `conversation_key_missing` | CHK wrap missing | Invite pre-provision failed |
| `mls.welcome.apply.failed` | MLS state mismatch | Rejoin or clear MLS state |
| `Secure channel initializing…` stuck | CHK not applied | Check accept response for wrap |
