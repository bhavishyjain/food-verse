from io import BytesIO

from fastapi import HTTPException
from PIL import Image, ImageEnhance, ImageOps, ImageStat, UnidentifiedImageError


ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}


def prepare_food_image(content: bytes, content_type: str) -> tuple[bytes, bytes | None]:
    """Orient, resize and normalize a food photo; add a lighting view if useful."""
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=415, detail="Upload a JPG, PNG, or WebP image.")
    try:
        with Image.open(BytesIO(content)) as source:
            source.verify()
        with Image.open(BytesIO(content)) as source:
            if source.width * source.height > 24_000_000:
                raise HTTPException(status_code=413, detail="Image resolution must be below 24 megapixels.")
            if min(source.width, source.height) < 64:
                raise HTTPException(status_code=422, detail="Image is too small for useful visual analysis; use at least 64 pixels on each side.")
            image = ImageOps.exif_transpose(source).convert("RGB")
            image.thumbnail((1536, 1536), Image.Resampling.LANCZOS)
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise HTTPException(status_code=422, detail="The image could not be decoded.") from exc

    original = BytesIO()
    image.save(original, format="JPEG", quality=88, optimize=True)
    luminance = ImageStat.Stat(image.convert("L"))
    mean = luminance.mean[0]
    if 65 <= mean <= 190 and luminance.stddev[0] >= 27:
        return original.getvalue(), None

    # This second view helps recognition under difficult lighting. The unaltered
    # normalized image remains the only basis for freshness/color judgments.
    improved = ImageOps.autocontrast(image, cutoff=1, preserve_tone=True)
    if mean < 65:
        improved = ImageEnhance.Brightness(improved).enhance(1.35)
    enhanced = BytesIO()
    improved.save(enhanced, format="JPEG", quality=88, optimize=True)
    return original.getvalue(), enhanced.getvalue()
