from io import BytesIO

from fastapi import HTTPException
from PIL import Image, ImageFilter, ImageStat

from ..models import FreshnessAnalysis, FreshnessFeatures
from .image_processing import prepare_food_image
from .model_provider import ask_json, image_part, validate_output


PROMPT = """Assess visible food freshness from the supplied original normalized photo. Return JSON only with is_food (boolean), item_name, level (Fresh, Moderately Fresh, Spoiled, or null when evidence is insufficient), confidence (0-1), and visual_signals (array of specific visible color, texture, discoloration, or surface-pattern observations). Use storage details only as user-reported context. A photo cannot establish microbial safety. Do not assert that food is safe to eat, and do not infer mold unless a suspicious pattern is visibly present. Low image quality or ambiguous food should lower confidence. Do not include recommendations; these are determined by the application."""


def extract_features(image_bytes: bytes) -> FreshnessFeatures:
    """Record descriptive image metrics, not food-specific spoilage diagnoses."""
    with Image.open(BytesIO(image_bytes)) as source:
        image = source.convert("RGB")
        image.thumbnail((256, 256), Image.Resampling.LANCZOS)
    image = image.filter(ImageFilter.MedianFilter(3))
    gray = image.convert("L")
    luminance = ImageStat.Stat(gray)
    color = ImageStat.Stat(image)
    edges = gray.filter(ImageFilter.FIND_EDGES)
    dark = sum(1 for pixel in gray.getdata() if pixel < 45)
    total = max(1, image.width * image.height)
    return FreshnessFeatures(
        mean_brightness=round(luminance.mean[0] / 255, 3),
        color_variation=round(sum(color.stddev) / (3 * 127.5), 3),
        texture_variation=round(ImageStat.Stat(edges).mean[0] / 255, 3),
        dark_pixel_ratio=round(dark / total, 3),
    )


def analyze_freshness(content: bytes, content_type: str, context: str = "") -> FreshnessAnalysis:
    original, _ = prepare_food_image(content, content_type)
    features = extract_features(original)
    data = ask_json(PROMPT, [image_part(original, "image/jpeg")], context[:700])
    if data.get("is_food") is False:
        raise HTTPException(status_code=422, detail="No food was identified in the supplied image.")
    data["features"] = features.model_dump()
    level = data.get("level")
    if level == "Spoiled":
        recommendation = "Do not consume food showing visible spoilage. Discard it and clean any contacted surfaces."
        warning = "Visible spoilage was flagged; this visual assessment is not a laboratory test."
    elif level == "Moderately Fresh":
        recommendation = "Check storage time and temperature, date labels, odor and texture. When in doubt, discard it."
        warning = "Visible changes need closer review before use."
    elif level == "Fresh":
        recommendation = "No obvious spoilage was identified. Verify storage conditions and food-specific use guidance before eating."
        warning = "Food can carry harmful microbes even when it looks fresh."
    else:
        recommendation = "Retake a well-lit close-up photo and check storage conditions; discard if safety is uncertain."
        warning = "The image does not support a reliable freshness classification."
        data["confidence"] = 0
    data["recommendation"] = recommendation
    data["warning"] = warning
    data["limitations"] = ["Image metrics describe pixels, not spoilage. Appearance cannot confirm microbial safety."]
    return validate_output(FreshnessAnalysis, data)
