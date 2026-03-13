#!/usr/bin/env python3
import argparse
import re
import sys
from pathlib import Path


GATEWAY_RE = re.compile(r"msg_type=mls_welcome_request.*conversation_id=(\d+)")
COMMIT_SENT_RE = re.compile(r"conversationId:\s*(\d+)")
WELCOME_APPLIED_RE = re.compile(r"conversationId:\s*(\d+)")
MEDIA_KEY_SIGNAL_RE = re.compile(r"call\\.media_key\\.signal\\.received.*conversationId:\\s*([-\\d]+).*hasNonce:\\s*(true|false)")

MISSING_KEY_RE = re.compile(r"MissingKey: missing key", re.IGNORECASE)
MEDIA_KEY_DECRYPT_FAILED_RE = re.compile(r"call\\.media_key\\.decrypt_failed")
MEDIA_KEY_DEFER_TIMEOUT_RE = re.compile(r"call\\.media_key\\.defer_timeout_no_fallback")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return ""


def extract_ids(pattern: re.Pattern, text: str) -> set[int]:
    ids: set[int] = set()
    for match in pattern.finditer(text):
        try:
            ids.add(int(match.group(1)))
        except Exception:
            continue
    return ids


def extract_multiline_ids(marker: str, pattern: re.Pattern, text: str) -> set[int]:
    ids: set[int] = set()
    waiting = False
    for line in text.splitlines():
        if marker in line:
            waiting = True
            continue
        if waiting:
            match = pattern.search(line)
            if match:
                try:
                    ids.add(int(match.group(1)))
                except Exception:
                    pass
            waiting = False
    return ids


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Smoke test for call invite + MLS welcome reissue chain."
    )
    parser.add_argument(
        "--gateway-log",
        default="gateway.log",
        help="Path to gateway.log",
    )
    parser.add_argument(
        "--logs-a",
        default="logsA.txt",
        help="Path to logsA.txt",
    )
    parser.add_argument(
        "--logs-b",
        default="logsB.txt",
        help="Path to logsB.txt",
    )
    parser.add_argument(
        "--allow-missing-key",
        action="store_true",
        help="Do not fail on MissingKey/media_key decrypt failures.",
    )
    args = parser.parse_args()

    gateway_text = read_text(Path(args.gateway_log))
    logs_a_text = read_text(Path(args.logs_a))
    logs_b_text = read_text(Path(args.logs_b))

    if not gateway_text or not logs_a_text or not logs_b_text:
        print("smoke test failed: missing log file(s)", file=sys.stderr)
        if not gateway_text:
            print(f"- gateway log not found: {args.gateway_log}", file=sys.stderr)
        if not logs_a_text:
            print(f"- logsA not found: {args.logs_a}", file=sys.stderr)
        if not logs_b_text:
            print(f"- logsB not found: {args.logs_b}", file=sys.stderr)
        return 2

    welcome_req_ids = extract_ids(GATEWAY_RE, gateway_text)
    commit_sent_ids = extract_multiline_ids("mls.commit.sent", COMMIT_SENT_RE, logs_a_text)
    welcome_applied_ids = extract_multiline_ids("group.welcome.applied", WELCOME_APPLIED_RE, logs_b_text)

    chain_ids = welcome_req_ids & commit_sent_ids & welcome_applied_ids

    if not chain_ids:
        print("smoke test failed: no matching conversation id across chain", file=sys.stderr)
        print(f"- gateway mls_welcome_request ids: {sorted(welcome_req_ids)}", file=sys.stderr)
        print(f"- logsA mls.commit.sent ids: {sorted(commit_sent_ids)}", file=sys.stderr)
        print(f"- logsB group.welcome.applied ids: {sorted(welcome_applied_ids)}", file=sys.stderr)
        return 1

    # Optional stricter checks for media-key decrypt health
    if not args.allow_missing_key:
        missing_key = MISSING_KEY_RE.search(logs_b_text) is not None
        decrypt_failed = MEDIA_KEY_DECRYPT_FAILED_RE.search(logs_b_text) is not None
        defer_timeout = MEDIA_KEY_DEFER_TIMEOUT_RE.search(logs_b_text) is not None
        if missing_key or decrypt_failed or defer_timeout:
            print("smoke test failed: media-key decrypt issues found", file=sys.stderr)
            if missing_key:
                print("- MissingKey present in logsB", file=sys.stderr)
            if decrypt_failed:
                print("- call.media_key.decrypt_failed present in logsB", file=sys.stderr)
            if defer_timeout:
                print("- call.media_key.defer_timeout_no_fallback present in logsB", file=sys.stderr)
            return 1

        # Ensure at least one media key signal has nonce
        has_nonce = False
        for match in MEDIA_KEY_SIGNAL_RE.finditer(logs_b_text):
            if match.group(2) == "true":
                has_nonce = True
                break
        if not has_nonce:
            print("smoke test failed: no media_key.signal with hasNonce=true in logsB", file=sys.stderr)
            return 1

    print("smoke test ok")
    print(f"chain conversation ids: {sorted(chain_ids)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
