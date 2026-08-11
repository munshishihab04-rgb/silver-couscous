"""Privacy-preserving helpers for optional analytics."""
from __future__ import annotations

from copy import deepcopy
from typing import Optional


def prepare_analytics_event(payload: dict) -> Optional[dict]:
    """Return a storage-safe event only after explicit analytics consent."""
    if payload.get("analytics_consent") is not True:
        return None
    event = deepcopy(payload)
    event.pop("ip", None)
    event.pop("user_agent", None)
    return event
