import json

import pytest
from cryptography.fernet import Fernet

from backup import decrypt_backup, encrypt_backup


def test_backup_encryption_roundtrip_and_fail_closed_without_key():
    payload = json.dumps({"collection": [{"email": "customer@example.com"}]}).encode()
    key = Fernet.generate_key().decode()
    encrypted = encrypt_backup(payload, key)
    assert payload not in encrypted
    assert decrypt_backup(encrypted, key) == payload
    with pytest.raises(RuntimeError, match="BACKUP_ENCRYPTION_KEY"):
        encrypt_backup(payload, "")
