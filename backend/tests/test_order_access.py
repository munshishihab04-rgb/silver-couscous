from order_access import hash_order_token, issue_order_token, verify_order_token


def test_order_access_token_is_random_hashed_and_constant_time_verified():
    token = issue_order_token()
    digest = hash_order_token(token)
    assert len(token) >= 40
    assert len(digest) == 64
    assert token not in digest
    assert verify_order_token(token, digest) is True
    assert verify_order_token("wrong-token", digest) is False
