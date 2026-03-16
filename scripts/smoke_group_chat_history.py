import asyncio
import base64
import json
import os
import random
import string
import sys
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional
from urllib.parse import urlencode, urlparse, urlunparse, parse_qsl
from urllib.request import Request, urlopen

try:
    import websockets
except Exception as exc:
    print("missing dependency:", exc, file=sys.stderr)
    print("install: pip install -r scripts/requirements.txt", file=sys.stderr)
    sys.exit(2)

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8180")
WS_URL = os.getenv("WS_URL", "ws://localhost:8180/ws")
PASSWORD = os.getenv("TEST_USER_PASSWORD", "test123123")
TIMEOUT = float(os.getenv("SMOKE_TIMEOUT", "15"))
CRYPTO_PROFILE = "MLS_256_XWING_CHACHA20POLY1305_SHA512_MLDSA87"
WIRE_SUITE = "mls_chacha20"


def rand_suffix(size: int = 6) -> str:
    return "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(size))


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

    await bob.send(
        {
            "type": "chat_message_send",
            "conversation_id": conversation_id,
            "session_epoch": session_epoch,
            "request_id": f"msg-{rand_suffix()}",
            **build_cipher_payload("msg-from-bob"),
        }
    )
    await carol.send(
        {
            "type": "chat_message_send",
            "conversation_id": conversation_id,
            "session_epoch": session_epoch,
            "request_id": f"msg-{rand_suffix()}",
            **build_cipher_payload("msg-from-carol"),
        }
    )
    await alice.send(
        {
            "type": "chat_message_send",
            "conversation_id": conversation_id,
            "session_epoch": session_epoch,
            "request_id": f"msg-{rand_suffix()}",
            **build_cipher_payload("msg-from-alice"),
        }
    )

    await bob.close()
    bob_token = http_login(bob_email, PASSWORD)
    bob = WsClient(bob_email, bob_token, bob_meta)
    await bob.connect()

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

    senders = {item.get("sender") for item in messages.get("items", []) if isinstance(item, dict)}
    expected = {alice_email, bob_email, carol_email}
    if not expected.issubset(senders):
        print("smoke test failed: missing senders", senders, file=sys.stderr)
        return 1

    print("smoke test ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
