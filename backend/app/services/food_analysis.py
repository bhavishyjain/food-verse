from fastapi import HTTPException

from .image_processing import prepare_food_image
from .model_provider import ask_json, image_part, validate_output
from .nutrition import heuristic_health_score, reference_nutrition
from ..models import FoodAnalysis


FOOD_PROMPT = """Analyze the food or drink provided by image and/or user context. Return JSON only with is_food (boolean), dish, confidence (0-1), items (array of name, confidence 0-1, portion, estimated grams or null, category chosen from vegetable/fruit/grain/protein/dairy/fat/mixed/other), nutrition (calories, protein, carbs, fat, fiber or null), freshness (Fresh, Moderately Fresh, Spoiled or null), freshness_confidence (0-1 or null), visual_signals (array), insights (array of useful actions), and limitations (array). When a photo is present, classify only visible food. Use the user's context to refine portions or ingredients but do not treat it as visual evidence. The first photo is color-normalized and should be the ONLY basis for freshness/color judgments; a second image, if present, is lighting-enhanced for recognition only. If no image is present, set visual confidence to 0, freshness to null, freshness_confidence to null, and visual_signals to []. If this is not food or drink, set is_food false. Nutrition and portion grams are rough estimates; use null where insufficient. Appearance cannot establish microbial safety. Never claim certainty about invisible ingredients."""


def analyze_food(content: bytes | None, content_type: str | None, context: str = "") -> FoodAnalysis:
    parts = []
    if content is not None and content_type is not None:
        normalized, enhanced = prepare_food_image(content, content_type)
        parts.extend([{"type": "input_text", "text": "Original normalized image for all visual judgments"}, image_part(normalized, "image/jpeg")])
        if enhanced is not None:
            parts.extend([{"type": "input_text", "text": "Lighting-enhanced view for recognition only"}, image_part(enhanced, "image/jpeg")])
    result = ask_json(FOOD_PROMPT, parts, context or "Identify and analyze this food")
    if result.get("is_food") is False:
        raise HTTPException(status_code=422, detail="No food or drink was identified in the supplied input.")
    analysis = validate_output(FoodAnalysis, result)
    matched = reference_nutrition(analysis.items)
    if matched is not None:
        analysis.nutrition = matched
        analysis.nutrition_source = "Approximate per-100g ingredient reference + estimated portion weight"
    else:
        analysis.nutrition_source = "AI estimate from available context"
    analysis.health_score = heuristic_health_score(analysis.nutrition)
    analysis.health_score_method = "Heuristic based on estimated macros, fiber and meal calories"
    if content is None:
        analysis.freshness = None
        analysis.freshness_confidence = None
        analysis.visual_signals = []
        analysis.confidence = 0
        analysis.limitations.append("No image was supplied; food identity and nutrition come from text or audio context.")
    return analysis
