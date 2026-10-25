from typing import Literal
from pydantic import BaseModel, Field, field_validator, model_validator


class Nutrition(BaseModel):
    calories: int
    protein: float
    carbs: float
    fat: float
    fiber: float


class FoodItem(BaseModel):
    name: str
    confidence: float
    portion: str
    grams: float | None = Field(default=None, ge=1, le=1500)
    category: Literal["vegetable", "fruit", "grain", "protein", "dairy", "fat", "mixed", "other"] = "other"


class FoodAnalysis(BaseModel):
    dish: str
    confidence: float
    items: list[FoodItem]
    nutrition: Nutrition | None = None
    health_score: int | None = None
    freshness: Literal["Fresh", "Moderately Fresh", "Spoiled"] | None = None
    freshness_confidence: float | None = None
    visual_signals: list[str] = []
    insights: list[str]
    limitations: list[str] = []
    nutrition_source: str = "AI estimate"
    health_score_method: str = "Macro-balance heuristic"


class FreshnessFeatures(BaseModel):
    mean_brightness: float
    color_variation: float
    texture_variation: float
    dark_pixel_ratio: float


class FreshnessAnalysis(BaseModel):
    item_name: str
    level: Literal["Fresh", "Moderately Fresh", "Spoiled"] | None = None
    confidence: float = Field(ge=0, le=1)
    visual_signals: list[str]
    features: FreshnessFeatures
    recommendation: str
    warning: str
    limitations: list[str] = Field(default_factory=list)


class UserProfile(BaseModel):
    age: int = Field(ge=18, le=100)
    height_cm: float = Field(ge=120, le=230)
    weight_kg: float = Field(ge=35, le=300)
    activity: Literal["sedentary", "light", "moderate", "active"] = "moderate"
    energy_basis: Literal["manual", "female_equation", "male_equation"] = "manual"
    goal: Literal["balanced", "weight-loss", "muscle-gain", "heart-health"] = "balanced"
    diet: Literal["everything", "vegetarian", "vegan", "pescatarian"] = "everything"
    allergies: list[str] = Field(default_factory=list, max_length=20)
    dislikes: list[str] = Field(default_factory=list, max_length=20)
    health_notes: str = Field(default="", max_length=300)
    pregnant_or_breastfeeding: bool = False

    @field_validator("allergies", "dislikes")
    @classmethod
    def clean_food_lists(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip().lower() for value in values if value.strip()]
        if any(len(value) > 50 for value in cleaned):
            raise ValueError("Each allergy or avoided food must be 50 characters or fewer.")
        return list(dict.fromkeys(cleaned))

    @model_validator(mode="after")
    def supported_profile(self):
        if self.pregnant_or_breastfeeding:
            raise ValueError("Automated energy targets are not offered during pregnancy or breastfeeding; seek individualized professional guidance.")
        if set(self.allergies) & set(self.dislikes):
            raise ValueError("List each food in either allergies or foods to avoid, not both.")
        return self


class MealPlanRequest(BaseModel):
    profile: UserProfile
    period: Literal["daily", "weekly"] = "daily"
    manual_calories: int | None = Field(default=2000, ge=1200, le=4500)

    @model_validator(mode="after")
    def manual_target_required(self):
        if self.profile.energy_basis == "manual" and self.manual_calories is None:
            raise ValueError("Enter a daily energy target when using a manual target.")
        return self


class RecipeRequest(BaseModel):
    prompt: str = Field(min_length=2, max_length=500)


class Recipe(BaseModel):
    title: str
    subtitle: str
    time: str
    difficulty: str
    ingredients: list[str]
    steps: list[str]
    tip: str
    safety_note: str = ""


class MacroTotals(BaseModel):
    calories: int = Field(ge=0)
    protein: float = Field(ge=0)
    carbs: float = Field(ge=0)
    fat: float = Field(ge=0)


class PlannedMeal(BaseModel):
    slot: Literal["Breakfast", "Lunch", "Snack", "Dinner"]
    name: str = Field(min_length=2)
    description: str
    ingredients: list[str] = Field(min_length=1)
    portion: str
    macros: MacroTotals
    reason: str


class PlannedDay(BaseModel):
    day: str
    meals: list[PlannedMeal]
    totals: MacroTotals


class MealAlternative(BaseModel):
    day: str
    replaces: Literal["Breakfast", "Lunch", "Snack", "Dinner"]
    meal: PlannedMeal


class MealPlan(BaseModel):
    period: Literal["daily", "weekly"]
    profile_summary: str
    target: MacroTotals
    target_method: str
    days: list[PlannedDay]
    alternatives: list[MealAlternative]
    coach_note: str
    cautions: list[str]


class HygieneCheck(BaseModel):
    label: str
    score: int | None = None
    status: Literal["Pass", "Review", "Not visible"]


class HygieneAlert(BaseModel):
    time: str
    message: str


class HygieneAnalysis(BaseModel):
    score: int | None = None
    status: str
    duration: str
    frames_analyzed: int
    checks: list[HygieneCheck]
    alerts: list[HygieneAlert]
    limitations: list[str] = []


class CookingGuidance(BaseModel):
    transcript: str
    guidance: str
    steps: list[str]
    safety_note: str = ""

