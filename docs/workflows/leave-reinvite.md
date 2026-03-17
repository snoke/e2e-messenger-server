# Leave / Re-invite

## Leave
1. Member sends `group_leave`.
2. Server marks membership inactive.
3. Server deletes member's CHK wrap.
4. Member can no longer fetch or decrypt history.

## Re-invite
1. Owner sends `group_add` again.
2. Owner pre-provisions a new CHK wrap.
3. Accept returns the new wrap.

## Notes
- Re-invite creates a fresh wrap.
- Old wraps must be removed to prevent stale access.

Related:
- [`docs/crypto/chk.md`](../crypto/chk.md)
- [`docs/workflows/invite-accept.md`](invite-accept.md)