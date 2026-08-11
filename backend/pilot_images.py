"""Deterministic, source-free product-card artwork for the pilot catalog."""
from __future__ import annotations

import hashlib
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

WIDTH = 1200
HEIGHT = 1200

PALETTES = {
    "Microsoft": (18, 60, 110),
    "Bitdefender": (112, 22, 42),
    "Adobe": (103, 24, 84),
    "Corel": (20, 91, 76),
}


def _font(size: int, bold: bool = False):
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{name}", size)


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textbbox((0, 0), candidate, font=font)[2] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def render_product_image(name: str, brand: str, output: Path) -> dict:
    base = PALETTES.get(brand, (36, 48, 67))
    image = Image.new("RGB", (WIDTH, HEIGHT), base)
    draw = ImageDraw.Draw(image)
    # Original geometric background; no vendor logos or imported package artwork.
    for index in range(12):
        inset = 44 + index * 46
        color = tuple(min(255, channel + index * 4) for channel in base)
        draw.rounded_rectangle((inset, inset, WIDTH - inset, HEIGHT - inset), radius=48, outline=color, width=3)
    draw.ellipse((820, -160, 1300, 320), fill=tuple(min(255, c + 30) for c in base))
    draw.rectangle((0, 1010, WIDTH, HEIGHT), fill=(8, 12, 20))

    draw.text((88, 82), "LICENZPOL", font=_font(35, True), fill=(255, 255, 255))
    draw.text((88, 132), "DIGITAL SOFTWARE", font=_font(20), fill=(195, 210, 225))
    draw.text((88, 310), brand.upper(), font=_font(27, True), fill=(180, 205, 225))

    title_font = _font(72, True)
    lines = _wrap(draw, name, title_font, 980)
    y = 380
    for line in lines[:5]:
        draw.text((88, y), line, font=title_font, fill=(255, 255, 255))
        y += 88

    draw.text((88, 1065), "SCHEDA DIGITALE • LICENZPOL.IT", font=_font(25, True), fill=(220, 230, 240))
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, "WEBP", quality=92, method=6)
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    return {"width": WIDTH, "height": HEIGHT, "sha256": digest, "source_assets": []}
