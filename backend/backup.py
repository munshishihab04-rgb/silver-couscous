"""Encrypted backup helpers for MongoDB exports containing customer data."""
from __future__ import annotations

from cryptography.fernet import Fernet


def _fernet(key: str) -> Fernet:
    if not key:
        raise RuntimeError("BACKUP_ENCRYPTION_KEY is required")
    try:
        return Fernet(key.encode("ascii"))
    except (TypeError, ValueError) as exc:
        raise RuntimeError("BACKUP_ENCRYPTION_KEY must be a valid Fernet key") from exc


def encrypt_backup(payload: bytes, key: str) -> bytes:
    return _fernet(key).encrypt(payload)


def decrypt_backup(payload: bytes, key: str) -> bytes:
    return _fernet(key).decrypt(payload)
