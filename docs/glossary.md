# Glossary

This glossary defines core terms used across the documentation.

## A
- **Access Boundary**: The point where a user gains the right to decrypt. In chat, accept is the access boundary.
- **Action (Symfony)**: Realtime handler invoked for a specific command.

## B
- **BEB (Background Event Bridge)**: Always-on layer that converts realtime frames into background events for notifications.
- **Broker**: Redis streams used for realtime inbox/outbox transport.

## C
- **CHK (Conversation History Key)**: Per-conversation key used to encrypt stored message history.
- **Conversation Ready**: Per-conversation crypto readiness state (`conversation_key_ready`).

## D
- **Device KEK**: Device-bound key-encryption key used to unwrap UVK on known devices.
- **Domain Owner**: The plugin or service responsible for a domain’s state and commands.

## E
- **Epoch**: MLS epoch. Indicates a specific live key state for MLS encryption.

## F
- **Fetch**: Recovery path for CHK wraps. Blocked for pending members.

## G
- **Gateway**: Rust component that routes realtime traffic and enforces routing rules.
- **Global Crypto Ready**: Login/vault readiness state (`crypto_ready`).

## I
- **Invite**: Prepares membership and CHK wrap but does not grant access.

## K
- **Key Wrap**: Encrypted representation of a key using another key.

## L
- **Live Transport**: MLS-encrypted realtime delivery of messages.

## M
- **MLS (Message Layer Security)**: Live transport encryption for group messaging.

## N
- **Notification Center**: Client-side delivery authority for notifications.

## O
- **Operation Scope**: Scope that controls processing and network activity.

## P
- **Pending Member**: Invitee who has not accepted. No access to CHK.

## R
- **Realtime Router**: Frontend component that routes inbound frames to modules.

## S
- **Scope Key**: Opaque identifier used for MLS signal routing without exposing conversation_id.
- **Session Epoch**: MLS epoch indicator for a conversation.

## U
- **UVK (User Vault Key)**: Root key for user-bound storage encryption.

## W
- **Wrap Algorithm**: Algorithm used to wrap keys, e.g., `user_ecdh_p256_hkdf_sha256_aes_gcm_256`.