import asyncio
import base64
import json
import os
import sys
import time
from urllib.request import Request, urlopen

try:
    import websockets
except Exception as exc:
    print("missing dependency:", exc, file=sys.stderr)
    print("install: pip install -r scripts/requirements.txt", file=sys.stderr)
    sys.exit(2)

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8180")
WS_URL = os.getenv("WS_URL", "ws://localhost:8180/ws")
PASSWORD = os.getenv("TEST_USER_PASSWORD", "test")
ALICE = os.getenv("ALICE_EMAIL", "alice@test.de")
BOB = os.getenv("BOB_EMAIL", "bob@test.de")
CRYPTO_PROFILE = os.getenv("CRYPTO_PROFILE", "x25519_chacha20_hkdf_dr")
CRYPTO_SUITE = os.getenv("CRYPTO_SUITE", "x25519_chacha20")
TIMEOUT = float(os.getenv("SMOKE_TIMEOUT", "10"))


def login(email: str) -> str:
    payload = json.dumps({"email": email, "password": PASSWORD}).encode("utf-8")
    req = Request(
        f"{API_BASE}/api/login_check",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(req, timeout=TIMEOUT) as response:
        body = response.read().decode("utf-8")
    data = json.loads(body)
    token = data.get("token")
    if not token:
        raise RuntimeError(f"missing token for {email}: {data}")
    return token


def unwrap(payload: str) -> dict:
    data = json.loads(payload)
    if isinstance(data, dict) and data.get("type") == "event" and isinstance(data.get("payload"), dict):
        return data["payload"]
    return data if isinstance(data, dict) else {}


async def bob_listener(token: str, ready: asyncio.Event) -> bool:
    url = f"{WS_URL}?access_token={token}"
    async with websockets.connect(url) as ws:
        await ws.send(json.dumps({"type": "ping"}))
        ready.set()
        start = time.time()
        while True:
            remaining = TIMEOUT - (time.time() - start)
            if remaining <= 0:
                return False
            msg = await asyncio.wait_for(ws.recv(), timeout=remaining)
            payload = unwrap(msg)
            if payload.get("type") != "chat":
                continue
            if payload.get("user") == f"user:{ALICE}":
                print("bob_received:", payload.get("text", "<encrypted>"))
                return True


async def alice_sender(token: str, ready: asyncio.Event) -> None:
    await ready.wait()
    url = f"{WS_URL}?access_token={token}"
    async with websockets.connect(url) as ws:
        await ws.send(json.dumps({"type": "ping"}))
        message = {"type": "chat", "to": BOB}
        if CRYPTO_PROFILE:
            plaintext = b"hello bob"
            ciphertext = base64.b64encode(plaintext).decode("ascii")
            nonce = base64.b64encode(b"").decode("ascii")
            message.update(
                {
                    "ciphertext": ciphertext,
                    "nonce": nonce,
                    "suite": CRYPTO_SUITE,
                    "crypto_profile": CRYPTO_PROFILE,
                }
            )
        else:
            message["text"] = "hello bob"
        await ws.send(json.dumps(message))


async def main() -> int:
    alice_token = login(ALICE)
    bob_token = login(BOB)
    ready = asyncio.Event()
    bob_task = asyncio.create_task(bob_listener(bob_token, ready))
    alice_task = asyncio.create_task(alice_sender(alice_token, ready))
    done, _ = await asyncio.wait(
        {bob_task, alice_task}, timeout=TIMEOUT + 2, return_when=asyncio.ALL_COMPLETED
    )
    if bob_task not in done or not bob_task.result():
        print("smoke test failed: bob did not receive message", file=sys.stderr)
        return 1
    print("smoke test ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
