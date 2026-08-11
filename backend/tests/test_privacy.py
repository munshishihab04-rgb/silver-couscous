from privacy import prepare_analytics_event


def test_analytics_without_explicit_consent_is_not_stored():
    assert prepare_analytics_event({"event_type": "page_view", "analytics_consent": False}) is None


def test_analytics_payload_drops_network_identifiers():
    event = prepare_analytics_event({
        "event_type": "page_view",
        "analytics_consent": True,
        "ip": "203.0.113.42",
        "user_agent": "Browser fingerprint",
        "path": "/catalog",
    })
    assert event["path"] == "/catalog"
    assert event["analytics_consent"] is True
    assert "ip" not in event
    assert "user_agent" not in event
