import pytest

from form_challenge import issue_form_challenge, verify_form_challenge


def test_form_challenge_is_purpose_bound_signed_and_time_bound():
    secret = "s" * 40
    token = issue_form_challenge("support", secret, now=100)
    with pytest.raises(ValueError, match="too quickly"):
        verify_form_challenge(token, "support", secret, now=100, min_age=2)
    verify_form_challenge(token, "support", secret, now=103, min_age=2)
    with pytest.raises(ValueError, match="purpose"):
        verify_form_challenge(token, "order", secret, now=103, min_age=2)
    with pytest.raises(ValueError, match="expired"):
        verify_form_challenge(token, "support", secret, now=2000, max_age=600)
    with pytest.raises(ValueError):
        verify_form_challenge(token + "tampered", "support", secret, now=103)
