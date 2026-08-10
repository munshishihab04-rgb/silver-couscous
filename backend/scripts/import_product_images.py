#!/usr/bin/env python3
"""Import and locally host verified product images from a structured catalog export."""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
TARGET_CSV = ROOT / "backend" / "data" / "catalog.csv"
OVERLAY = ROOT / "backend" / "data" / "product_images.json"
PUBLIC_DIR = ROOT / "frontend" / "public" / "products"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/127.0 Safari/537.36"


def make_slug(source_url: str, gtin: str) -> str:
    base = Path(urlparse(source_url).path).name
    base = re.sub(r"\.html$", "", base, flags=re.I)
    base = re.sub(r"^\d+[-_]", "", base)
    digits = re.sub(r"\D", "", gtin or "")
    if digits:
        base = re.sub(rf"-{re.escape(digits)}$", "", base)
        trimmed = digits.lstrip("0")
        if trimmed:
            base = re.sub(rf"-0*{re.escape(trimmed)}$", "", base)
    else:
        base = re.sub(r"-\d{10,14}$", "", base)
    return re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-") or "prodotto"


def best_image(row: dict) -> str:
    try:
        offer = json.loads(row.get("offer_schema_json") or "{}")
        image = offer.get("image")
        if isinstance(image, list) and image:
            return str(image[0])
        if isinstance(image, str):
            return image
    except Exception:
        pass
    return (row.get("image") or "").split(" | ")[0].strip()


def download(item: tuple[str, str]) -> dict:
    slug, url = item
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "image/avif,image/webp,image/png,image/jpeg,*/*;q=0.8"})
    try:
        with urllib.request.urlopen(req, timeout=45) as response:
            status = response.status
            content_type = response.headers.get("Content-Type", "")
            payload = response.read()
        if status != 200 or not content_type.lower().startswith("image/"):
            raise ValueError(f"unexpected response {status} {content_type}")
        with Image.open(io.BytesIO(payload)) as image:
            image.load()
            source_format = image.format or ""
            source_size = image.size
            if image.mode not in ("RGB", "RGBA"):
                image = image.convert("RGBA" if "transparency" in image.info else "RGB")
            image.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
            out = PUBLIC_DIR / f"{slug}.webp"
            image.save(out, "WEBP", quality=88, method=6)
        with Image.open(out) as check:
            check.verify()
        return {
            "slug": slug,
            "status": "ok",
            "source_url": url,
            "source_format": source_format,
            "source_width": source_size[0],
            "source_height": source_size[1],
            "bytes": out.stat().st_size,
            "local_url": f"/products/{slug}.webp",
        }
    except Exception as exc:
        return {"slug": slug, "status": f"error: {type(exc).__name__}: {exc}", "source_url": url}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-csv", required=True, type=Path)
    args = parser.parse_args()

    with TARGET_CSV.open(encoding="utf-8-sig", newline="") as handle:
        target_slugs = {row["product_slug"].strip() for row in csv.DictReader(handle) if row.get("product_slug")}
    with args.source_csv.open(encoding="utf-8-sig", newline="") as handle:
        source_rows = list(csv.DictReader(handle))

    source_map: dict[str, str] = {}
    for row in source_rows:
        slug = make_slug(row.get("source_page_url", ""), row.get("gtin_digits", ""))
        if slug in source_map:
            slug = f"{slug}-{row.get('product_id', '').strip()}".rstrip("-")
        url = best_image(row)
        if slug and url:
            source_map[slug] = url

    missing = sorted(target_slugs - source_map.keys())
    if missing:
        raise SystemExit(f"No source image for {len(missing)} target slugs: {missing[:20]}")

    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    items = sorted((slug, source_map[slug]) for slug in target_slugs)
    results = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(download, item) for item in items]
        for index, future in enumerate(as_completed(futures), 1):
            results.append(future.result())
            if index % 25 == 0 or index == len(futures):
                print(f"images {index}/{len(futures)}", flush=True)

    results.sort(key=lambda row: row["slug"])
    failed = [row for row in results if row["status"] != "ok"]
    manifest_path = ROOT / "backend" / "data" / "product_images_verification.csv"
    fields = ["slug", "status", "source_url", "source_format", "source_width", "source_height", "bytes", "local_url"]
    with manifest_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)
    if failed:
        raise SystemExit(f"Image import failed for {len(failed)} products; see {manifest_path}")

    overlay = {row["slug"]: row["local_url"] for row in results}
    OVERLAY.write_text(json.dumps(overlay, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"target_products": len(target_slugs), "downloaded": len(results), "failed": 0, "overlay": str(OVERLAY)}, indent=2))


if __name__ == "__main__":
    main()
