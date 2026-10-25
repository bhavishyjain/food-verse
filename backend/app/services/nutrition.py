from ..models import FoodItem, Nutrition


# Approximate per-100g reference values for common unbranded ingredients.
# These examples are not a substitute for a verified nutrient database.
PROFILES = {
    "apple": (52, 0.3, 13.8, 0.2, 2.4),
    "banana": (89, 1.1, 22.8, 0.3, 2.6),
    "avocado": (160, 2.0, 8.5, 14.7, 6.7),
    "tomato": (18, 0.9, 3.9, 0.2, 1.2),
    "spinach": (23, 2.9, 3.6, 0.4, 2.2),
    "chickpea": (164, 8.9, 27.4, 2.6, 7.6),
    "rice": (130, 2.7, 28.2, 0.3, 0.4),
    "egg": (143, 12.6, 0.7, 9.5, 0.0),
    "salmon": (208, 20.4, 0.0, 13.4, 0.0),
    "chicken breast": (165, 31.0, 0.0, 3.6, 0.0),
    "broccoli": (34, 2.8, 6.6, 0.4, 2.6),
    "potato": (87, 1.9, 20.1, 0.1, 1.8),
    "carrot": (41, 0.9, 9.6, 0.2, 2.8),
}


def reference_nutrition(items: list[FoodItem]) -> Nutrition | None:
    if not items:
        return None
    totals = [0.0] * 5
    for item in items:
        name = item.name.casefold()
        match = next((profile for key, profile in PROFILES.items() if key in name), None)
        if match is None or item.grams is None or not 1 <= item.grams <= 1500:
            return None
        for index, value in enumerate(match):
            totals[index] += value * item.grams / 100
    return Nutrition(calories=round(totals[0]), protein=round(totals[1], 1), carbs=round(totals[2], 1), fat=round(totals[3], 1), fiber=round(totals[4], 1))


def heuristic_health_score(nutrition: Nutrition | None) -> int | None:
    if nutrition is None:
        return None
    energy = max(1, nutrition.protein * 4 + nutrition.carbs * 4 + nutrition.fat * 9)
    protein_pct = nutrition.protein * 4 / energy
    carb_pct = nutrition.carbs * 4 / energy
    fat_pct = nutrition.fat * 9 / energy
    score = 60
    score += 8 if 0.10 <= protein_pct <= 0.35 else 0
    score += 8 if 0.20 <= fat_pct <= 0.40 else 0
    score += 8 if 0.35 <= carb_pct <= 0.65 else 0
    score += min(10, round(nutrition.fiber * 1.5))
    score += 6 if 250 <= nutrition.calories <= 800 else 0
    return min(100, max(0, score))
