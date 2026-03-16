import asyncio
import base64
import hashlib
import json
import os
import random
import string
import sys
import time
from dataclasses import dataclass
from collections import deque
from typing import Any, Callable, Dict, Optional
from urllib.parse import urlencode, urlparse, urlunparse, parse_qsl
from urllib.request import Request, urlopen

try:
    import websockets
except Exception as exc:
    print("missing dependency:", exc, file=sys.stderr)
    print("install: pip install -r scripts/requirements.txt", file=sys.stderr)
    sys.exit(2)

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except Exception as exc:
    print("missing dependency:", exc, file=sys.stderr)
    print("install: pip install -r scripts/requirements.txt", file=sys.stderr)
    sys.exit(2)

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8180")
WS_URL = os.getenv("WS_URL", "ws://localhost:8180/ws")
PASSWORD = os.getenv("TEST_USER_PASSWORD", "test123123")
TIMEOUT = float(os.getenv("SMOKE_TIMEOUT", "15"))
DEBUG = os.getenv("SMOKE_DEBUG", "0") == "1"
CRYPTO_PROFILE = "MLS_256_XWING_CHACHA20POLY1305_SHA512_MLDSA87"
WIRE_SUITE = "mls_chacha20"
STORAGE_SUITE = "chk_aesgcm_v1"
WRAP_ALG = "smoke_aesgcm_v1"
CHK_LEN = 32
NONCE_LEN = 12


def rand_suffix(size: int = 6) -> str:
    return "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(size))


def debug(msg: str) -> None:
    if DEBUG:
        print(f"[smoke-debug] {msg}", file=sys.stderr)


def http_register(email: str, password: str, name: str) -> str:
    payload = json.dumps({"email": email, "password": password, "name": name}).encode("utf-8")
    req = Request(
        f"{API_BASE}/api/register",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(req, timeout=TIMEOUT) as response:
        data = json.loads(response.read().decode("utf-8"))
    token = data.get("token")
    if not token:
        raise RuntimeError(f"register failed: {data}")
    return token


def http_login(email: str, password: str) -> str:
    payload = json.dumps({"email": email, "password": password}).encode("utf-8")
    req = Request(
        f"{API_BASE}/api/login_check",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(req, timeout=TIMEOUT) as response:
        data = json.loads(response.read().decode("utf-8"))
    token = data.get("token")
    if not token:
        raise RuntimeError(f"login failed: {data}")
    return token


def unwrap(raw: str) -> Dict[str, Any]:
    data = json.loads(raw)
    if isinstance(data, dict) and data.get("type") == "event" and isinstance(data.get("payload"), dict):
        return data["payload"]
    return data if isinstance(data, dict) else {}


@dataclass
class ClientMeta:
    device_id: str
    client_instance_id: str
    session_id: str
    device_label: str


class WsClient:
    def __init__(self, email: str, token: str, meta: ClientMeta):
        self.email = email
        self.token = token
        self.meta = meta
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
        self.reader_task: Optional[asyncio.Task] = None
        self.history = deque(maxlen=300)

    async def connect(self) -> None:
        url_parts = urlparse(WS_URL)
        query = dict(parse_qsl(url_parts.query))
        query.update(
            {
                "token": self.token,
                "client_instance_id": self.meta.client_instance_id,
            }
        )
        url = urlunparse(
            (
                url_parts.scheme,
                url_parts.netloc,
                url_parts.path,
                url_parts.params,
                urlencode(query),
                url_parts.fragment,
            )
        )
        self.ws = await websockets.connect(url, ping_interval=None)
        self.reader_task = asyncio.create_task(self._reader())
        await self.wait_for(lambda p: p.get("type") == "auth_ok")
        await self.send({"type": "session_ready", "request_id": f"ready-{self.meta.session_id}"})
        await self.wait_for(lambda p: p.get("type") == "session_ready_ok")

    async def close(self) -> None:
        if self.reader_task:
            self.reader_task.cancel()
        if self.ws:
            await self.ws.close()

    async def _reader(self) -> None:
        assert self.ws is not None
        async for msg in self.ws:
            payload = unwrap(msg)
            self.history.append(payload)
            await self.queue.put(payload)

    async def send(self, payload: Dict[str, Any]) -> None:
        assert self.ws is not None
        base = {
            "session_id": self.meta.session_id,
            "client_instance_id": self.meta.client_instance_id,
            "device_id": self.meta.device_id,
            "device_label": self.meta.device_label,
        }
        data = {**base, **payload}
        await self.ws.send(json.dumps(data))

    async def wait_for(self, predicate: Callable[[Dict[str, Any]], bool], timeout: float = TIMEOUT) -> Dict[str, Any]:
        deadline = asyncio.get_running_loop().time() + timeout
        while True:
            remaining = deadline - asyncio.get_running_loop().time()
            if remaining <= 0:
                raise TimeoutError(f"{self.email} timed out waiting for event")
            payload = await asyncio.wait_for(self.queue.get(), timeout=remaining)
            if predicate(payload):
                return payload


def dump_recent(client: WsClient, label: str, limit: int = 15) -> None:
    items = list(client.history)[-limit:]
    print(f"[smoke-debug] recent events for {label}:", file=sys.stderr)
    for entry in items:
        try:
            print(json.dumps(entry), file=sys.stderr)
        except Exception:
            print(str(entry), file=sys.stderr)


async def wait_for_chat_sent(client: WsClient, conversation_id: int, client_message_id: str) -> None:
    await client.wait_for(
        lambda p: p.get("type") == "chat_sent"
        and int(p.get("conversation_id", 0)) == conversation_id
        and p.get("client_message_id") == client_message_id
    )


def build_cipher_payload(text: str) -> Dict[str, Any]:
    ciphertext = base64.b64encode(text.encode("utf-8")).decode("ascii")
    nonce = base64.b64encode(os.urandom(12)).decode("ascii")
    return {
        "ciphertext": ciphertext,
        "nonce": nonce,
        "suite": WIRE_SUITE,
        "header": {"dh": "mls"},
        "crypto_profile": CRYPTO_PROFILE,
    }

def derive_wrap_key(email: str) -> bytes:
    return hashlib.sha256(f"smoke-wrap:{email}".encode("utf-8")).digest()


def wrap_chk(email: str, chk: bytes) -> str:
    key = derive_wrap_key(email)
    nonce = os.urandom(NONCE_LEN)
    cipher = AESGCM(key).encrypt(nonce, chk, None)
    return base64.b64encode(nonce + cipher).decode("ascii")


def unwrap_chk(email: str, wrapped: str) -> bytes:
    raw = base64.b64decode(wrapped.encode("ascii"))
    nonce = raw[:NONCE_LEN]
    cipher = raw[NONCE_LEN:]
    key = derive_wrap_key(email)
    return AESGCM(key).decrypt(nonce, cipher, None)


def encrypt_storage(chk: bytes, plaintext: str) -> Dict[str, str]:
    nonce = os.urandom(NONCE_LEN)
    cipher = AESGCM(chk).encrypt(nonce, plaintext.encode("utf-8"), None)
    return {
        "ciphertext": base64.b64encode(cipher).decode("ascii"),
        "nonce": base64.b64encode(nonce).decode("ascii"),
        "suite": STORAGE_SUITE,
    }


def decrypt_storage(chk: bytes, ciphertext: str, nonce: str) -> str:
    cipher_bytes = base64.b64decode(ciphertext.encode("ascii"))
    nonce_bytes = base64.b64decode(nonce.encode("ascii"))
    plain = AESGCM(chk).decrypt(nonce_bytes, cipher_bytes, None)
    return plain.decode("utf-8")


async def main() -> int:
    stamp = int(time.time())
    alice_email = f"alice{stamp}@test.de"
    bob_email = f"bob{stamp}@test.de"
    carol_email = f"carol{stamp}@test.de"

    alice_token = http_register(alice_email, PASSWORD, "Alice")
    bob_token = http_register(bob_email, PASSWORD, "Bob")
    carol_token = http_register(carol_email, PASSWORD, "Carol")

    alice_meta = ClientMeta(
        device_id=f"device-{stamp}-alice-{rand_suffix()}",
        client_instance_id=f"ci-{rand_suffix(12)}",
        session_id=f"session-{stamp}-alice-{rand_suffix()}",
        device_label="smoke-alice",
    )
    bob_meta = ClientMeta(
        device_id=f"device-{stamp}-bob-{rand_suffix()}",
        client_instance_id=f"ci-{rand_suffix(12)}",
        session_id=f"session-{stamp}-bob-{rand_suffix()}",
        device_label="smoke-bob",
    )
    carol_meta = ClientMeta(
        device_id=f"device-{stamp}-carol-{rand_suffix()}",
        client_instance_id=f"ci-{rand_suffix(12)}",
        session_id=f"session-{stamp}-carol-{rand_suffix()}",
        device_label="smoke-carol",
    )

    alice = WsClient(alice_email, alice_token, alice_meta)
    bob = WsClient(bob_email, bob_token, bob_meta)
    carol = WsClient(carol_email, carol_token, carol_meta)

    await asyncio.gather(alice.connect(), bob.connect(), carol.connect())

    await alice.send(
        {
            "type": "group_create",
            "name": "Smoke Group",
            "members": [f"user:{bob_email}", f"user:{carol_email}"],
            "crypto_profile": CRYPTO_PROFILE,
            "request_id": f"group-create-{rand_suffix()}",
        }
    )
    group_created = await alice.wait_for(lambda p: p.get("type") == "group_created")
    conversation_id = int(group_created["conversation_id"])
    session_epoch = int(group_created["session_epoch"])

    chk = os.urandom(CHK_LEN)
    recipients = [
        {"email": alice_email, "wrapped_chk": wrap_chk(alice_email, chk)},
        {"email": bob_email, "wrapped_chk": wrap_chk(bob_email, chk)},
        {"email": carol_email, "wrapped_chk": wrap_chk(carol_email, chk)},
    ]
    await alice.send(
        {
            "type": "conversation_key_init",
            "conversation_id": conversation_id,
            "recipients": recipients,
            "wrap_alg": WRAP_ALG,
            "key_version": 1,
            "request_id": f"convkey-init-{rand_suffix()}",
        }
    )
    await alice.wait_for(lambda p: p.get("type") == "conversation_key_init_ok")

    for client, email in ((alice, alice_email), (bob, bob_email), (carol, carol_email)):
        await client.send(
            {
                "type": "conversation_key_fetch",
                "conversation_id": conversation_id,
                "request_id": f"convkey-fetch-{rand_suffix()}",
            }
        )
        fetch = await client.wait_for(lambda p: p.get("type") == "conversation_key_fetch_ok")
        fetched = unwrap_chk(email, fetch["wrapped_chk"])
        if fetched != chk:
            print(f"smoke test failed: CHK mismatch for {email}", file=sys.stderr)
            return 1

    await bob.send(
        {
            "type": "group_membership_accept",
            "conversation_id": conversation_id,
            "request_id": f"accept-{rand_suffix()}",
        }
    )
    await bob.wait_for(
        lambda p: p.get("type") == "group_membership_accept_ok"
        and int(p.get("conversation_id", 0)) == conversation_id
    )

    await carol.send(
        {
            "type": "group_membership_accept",
            "conversation_id": conversation_id,
            "request_id": f"accept-{rand_suffix()}",
        }
    )
    await carol.wait_for(
        lambda p: p.get("type") == "group_membership_accept_ok"
        and int(p.get("conversation_id", 0)) == conversation_id
    )

    bob_msg_id = f"local-{rand_suffix(8)}"
    await bob.send(
        {
            "type": "chat_message_send",
            "conversation_id": conversation_id,
            "session_epoch": session_epoch,
            "client_message_id": bob_msg_id,
            "request_id": f"msg-{rand_suffix()}",
            **build_cipher_payload("live-msg-from-bob"),
            "storage": {
                **encrypt_storage(chk, "msg-from-bob"),
                "key_version": 1,
            },
        }
    )
    await wait_for_chat_sent(bob, conversation_id, bob_msg_id)

    carol_msg_id = f"local-{rand_suffix(8)}"
    await carol.send(
        {
            "type": "chat_message_send",
            "conversation_id": conversation_id,
            "session_epoch": session_epoch,
            "client_message_id": carol_msg_id,
            "request_id": f"msg-{rand_suffix()}",
            **build_cipher_payload("live-msg-from-carol"),
            "storage": {
                **encrypt_storage(chk, "msg-from-carol"),
                "key_version": 1,
            },
        }
    )
    await wait_for_chat_sent(carol, conversation_id, carol_msg_id)

    alice_msg_id = f"local-{rand_suffix(8)}"
    await alice.send(
        {
            "type": "chat_message_send",
            "conversation_id": conversation_id,
            "session_epoch": session_epoch,
            "client_message_id": alice_msg_id,
            "request_id": f"msg-{rand_suffix()}",
            **build_cipher_payload("live-msg-from-alice"),
            "storage": {
                **encrypt_storage(chk, "msg-from-alice"),
                "key_version": 1,
            },
        }
    )
    await wait_for_chat_sent(alice, conversation_id, alice_msg_id)

    await bob.close()
    bob_token = http_login(bob_email, PASSWORD)
    bob = WsClient(bob_email, bob_token, bob_meta)
    await bob.connect()

    await bob.send(
        {
            "type": "conversation_key_fetch",
            "conversation_id": conversation_id,
            "request_id": f"convkey-fetch-{rand_suffix()}",
        }
    )
    fetch = await bob.wait_for(lambda p: p.get("type") == "conversation_key_fetch_ok")
    fetched = unwrap_chk(bob_email, fetch["wrapped_chk"])
    if fetched != chk:
        print("smoke test failed: CHK mismatch after relogin", file=sys.stderr)
        return 1

    await bob.send(
        {
            "type": "chat_messages_request",
            "conversation_id": conversation_id,
            "limit": 50,
            "request_id": f"msg-list-{rand_suffix()}",
        }
    )
    messages = await bob.wait_for(
        lambda p: p.get("type") == "messages"
        and int(p.get("conversation_id", 0)) == conversation_id
    )

    decrypted = []
    for item in messages.get("items", []):
        if not isinstance(item, dict):
            continue
        storage = item.get("storage")
        if not isinstance(storage, dict):
            continue
        ciphertext = storage.get("ciphertext")
        nonce = storage.get("nonce")
        if not isinstance(ciphertext, str) or not isinstance(nonce, str):
            continue
        try:
            plaintext = decrypt_storage(chk, ciphertext, nonce)
            decrypted.append(plaintext)
        except Exception:
            pass

    senders = {item.get("sender") for item in messages.get("items", []) if isinstance(item, dict)}
    expected = {alice_email, bob_email, carol_email}
    if not expected.issubset(senders):
        print("smoke test failed: missing senders", senders, file=sys.stderr)
        debug(f"conversation_id={conversation_id} session_epoch={session_epoch}")
        debug(f"messages.items.count={len(messages.get('items', []))}")
        if DEBUG:
            dump_recent(alice, "alice")
            dump_recent(bob, "bob")
            dump_recent(carol, "carol")
        return 1
    expected_texts = {"msg-from-alice", "msg-from-bob", "msg-from-carol"}
    if not expected_texts.issubset(set(decrypted)):
        print("smoke test failed: storage decrypt mismatch", decrypted, file=sys.stderr)
        debug(f"conversation_id={conversation_id} session_epoch={session_epoch}")
        if DEBUG:
            dump_recent(bob, "bob")
        return 1

    print("smoke test ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
