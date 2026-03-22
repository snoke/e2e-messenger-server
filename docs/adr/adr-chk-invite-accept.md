# ADR: CHK Wrap Pre‑Provisioning at Invite + Atomic Accept

Status: **Accepted**

## Context
We had a race in the previous CHK distribution model:

- Bob could accept and fetch **before** his wrap was persisted.
- If Alice went offline after invite, Bob could be blocked indefinitely.
- Retry/fetch loops introduced unstable UX (“Secure channel initializing…”).

We require:
- `invite != access`
- `accept = access + key delivery`
- No server‑side CHK escrow or re‑wrapping
- No retry as the normal path

## Decision
**Invite pre‑provisions the invited member’s CHK wrap.**  
**Accept is atomic and must return the prepared wrap.**

Strict semantics:
1. Invite succeeds **only if** the member‑specific CHK wrap is created and persisted.
2. Accept returns the prepared wrap directly.
3. Pending members **cannot** fetch wraps.
4. If the wrap is missing at accept time, accept fails hard (invariant violation).

## Consequences
- No post‑accept race.
- Accept works even if the inviter is offline.
- Pending fetch is explicitly blocked.
- Any missing wrap becomes a **hard error**, not a recoverable retry state.

## Implementation Notes
- Wraps are stored in `conversation_key_records`.
- `group_add` requires `wrapped_chk`, `wrap_alg`, `key_version`.
- `group_membership_accept_ok` includes `wrapped_chk`, `wrap_alg`, `key_version`.
- `conversation_key_fetch` rejects pending members.
- Wraps are deleted on leave/remove, and re‑invite creates a new wrap.

**Key files**
- [`frontend/src/app/messaging/messenger/conversation.ts`](../../frontend/src/app/messaging/messenger/conversation.ts)
- [`frontend/src/app/messaging/messenger/conversationKeys.ts`](../../frontend/src/app/messaging/messenger/conversationKeys.ts)
- [`symfony/src/Plugins/Chat/Application/Realtime/Action/GroupAddAction.php`](../../symfony/src/Plugins/Chat/Application/Realtime/Action/GroupAddAction.php)
- [`symfony/src/Plugins/Chat/Application/Realtime/Action/GroupMembershipAcceptAction.php`](../../symfony/src/Plugins/Chat/Application/Realtime/Action/GroupMembershipAcceptAction.php)
- [`symfony/src/Plugins/Chat/Application/Realtime/Action/ConversationKeyFetchAction.php`](../../symfony/src/Plugins/Chat/Application/Realtime/Action/ConversationKeyFetchAction.php)
- [`symfony/src/Service/ConversationKeyService.php`](../../symfony/src/Service/ConversationKeyService.php)

## Validation / Tests
- Invite succeeds only if wrap exists.
- Accept fails if wrap missing.
- Pending fetch fails.
- Accept delivers wrap, client unwraps immediately.
- Invitee becomes conversation‑ready without retries.