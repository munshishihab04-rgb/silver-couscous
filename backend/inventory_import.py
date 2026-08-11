"""Fail-closed parsing for private license inventory imports."""
from __future__ import annotations

from collections import Counter
import hashlib
from typing import Iterable


def analyse_rows(rows: Iterable[dict], known_skus: set[str]) -> tuple[list[dict], dict]:
    valid: list[dict] = []
    seen: set[str] = set()
    counts: Counter[str] = Counter()
    report = {
        "rows": 0,
        "valid": 0,
        "duplicates_in_file": 0,
        "blank_or_invalid": 0,
        "unknown_sku": 0,
        "per_sku": {},
    }
    for row in rows:
        report["rows"] += 1
        sku = str(row.get("sku") or "").strip()
        key = str(row.get("key") or "").strip()
        source = str(row.get("source") or "private-csv").strip()[:200]
        if not sku or not key:
            report["blank_or_invalid"] += 1
            continue
        if sku not in known_skus:
            report["unknown_sku"] += 1
            continue
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        if digest in seen:
            report["duplicates_in_file"] += 1
            continue
        seen.add(digest)
        valid.append({"sku": sku, "key": key, "source": source})
        counts[sku] += 1
    report["valid"] = len(valid)
    report["per_sku"] = dict(sorted(counts.items()))
    return valid, report
