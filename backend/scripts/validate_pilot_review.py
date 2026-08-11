#!/usr/bin/env python3
"""Validate a completed pilot-review CSV without mutating MongoDB."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from pilot_catalog import validate_review_row  # noqa: E402

DATA = BACKEND / "data"
MANIFEST = DATA / "pilot_catalog.json"
TEMPLATE = DATA / "pilot_review_template.csv"
REPORT = DATA / "pilot_review_report.json"


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    expected = [item["slug"] for item in manifest["items"]]
    with TEMPLATE.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    by_slug = {row.get("slug"): row for row in rows if row.get("slug")}
    results = []
    for slug in expected:
        row = by_slug.get(slug)
        blockers = ["row_missing"] if row is None else validate_review_row(row)
        results.append({"slug": slug, "ready": not blockers, "blockers": blockers})
    extras = sorted(set(by_slug) - set(expected))
    payload = {
        "status": "ready_for_human_application" if all(item["ready"] for item in results) and not extras else "blocked",
        "expected_rows": len(expected),
        "ready_rows": sum(item["ready"] for item in results),
        "blocked_rows": sum(not item["ready"] for item in results),
        "unexpected_slugs": extras,
        "items": results,
        "warning": "Schema validation does not prove that referenced documents are authentic. A human reviewer must inspect every private document before applying approval.",
    }
    REPORT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: payload[key] for key in ("status", "expected_rows", "ready_rows", "blocked_rows")}))
    return 0 if payload["status"] == "ready_for_human_application" else 1


if __name__ == "__main__":
    raise SystemExit(main())
