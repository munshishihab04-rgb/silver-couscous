from PIL import Image

from pilot_images import render_product_image


def test_generated_pilot_artwork_is_original_source_free_and_large_enough(tmp_path):
    output = tmp_path / "product.webp"
    receipt = render_product_image("Example Product 2026", "Example", output)
    assert output.exists()
    assert receipt["source_assets"] == []
    assert len(receipt["sha256"]) == 64
    with Image.open(output) as image:
        assert image.size == (1200, 1200)
        assert image.format == "WEBP"
