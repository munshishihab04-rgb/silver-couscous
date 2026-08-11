"""Signed, time-bound anti-automation challenge for public forms."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _key(secret: str) -> bytes:
    if len(secret) < 32:
        raise RuntimeError("JWT_SECRET must be at least 32 characters for form challenges")
    return hmac.new(secret.encode(), b"licenzpol-form-challenge-v1", hashlib.sha256).digest()


def issue_form_challenge(purpose: str, secret: str, *, now: int | None = None) -> str:
    payload = json.dumps(
        {"p": purpose, "iat": int(time.time() if now is None else now), "n": secrets.token_urlsafe(16)},
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    encoded = _b64(payload)
    signature = _b64(hmac.new(_key(secret), encoded.encode(), hashlib.sha256).digest())
    return f"{encoded}.{signature}"


def verify_form_challenge(
    token: str,
    purpose: str,
    secret: str,
    *,
    now: int | None = None,
    min_age: int = 2,
    max_age: int = 1800,
) -> str:
    try:
        encoded, supplied = token.split(".", 1)
        expected = _b64(hmac.new(_key(secret), encoded.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(supplied, expected):
            raise ValueError("invalid signature")
        payload = json.loads(_unb64(encoded))
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError("invalid form challenge") from exc
    if payload.get("p") != purpose:
        raise ValueError("invalid form challenge purpose")
    age = int(time.time() if now is None else now) - int(payload.get("iat", 0))
    if age < min_age:
        raise ValueError("form submitted too quickly")
    if age > max_age:
        raise ValueError("form challenge expired")
    nonce = payload.get("n")
    if not isinstance(nonce, str) or not nonce:
        raise ValueError("invalid form challenge nonce")
    return nonce
