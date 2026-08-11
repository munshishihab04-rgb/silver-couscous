"""Unpredictable bearer tokens for customer access to individual orders."""
from __future__ import annotations

import hashlib
import hmac
import secrets


def issue_order_token() -> str:
    return secrets.token_urlsafe(32)


def hash_order_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def verify_order_token(token: str | None, expected_hash: str | None) -> bool:
    if not token or not expected_hash:
        return False
    return hmac.compare_digest(hash_order_token(token), expected_hash)
