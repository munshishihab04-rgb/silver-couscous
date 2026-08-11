from security import SlidingWindowRateLimiter, build_security_headers


def test_security_headers_are_fail_closed_and_hsts_only_on_https():
    http = build_security_headers(is_https=False)
    https = build_security_headers(is_https=True)
    production_https = build_security_headers(is_https=True, enable_hsts=True)
    assert http["X-Content-Type-Options"] == "nosniff"
    assert http["X-Frame-Options"] == "DENY"
    assert "default-src 'self'" in http["Content-Security-Policy"]
    assert "object-src 'none'" in http["Content-Security-Policy"]
    assert "Strict-Transport-Security" not in http
    assert "Strict-Transport-Security" not in https
    assert production_https["Strict-Transport-Security"].startswith("max-age=")


def test_sliding_window_rate_limiter_blocks_and_recovers_after_window():
    now = [100.0]
    limiter = SlidingWindowRateLimiter(clock=lambda: now[0])
    assert limiter.allow("support:ip", limit=2, window_seconds=60) is True
    assert limiter.allow("support:ip", limit=2, window_seconds=60) is True
    assert limiter.allow("support:ip", limit=2, window_seconds=60) is False
    now[0] = 161.0
    assert limiter.allow("support:ip", limit=2, window_seconds=60) is True
