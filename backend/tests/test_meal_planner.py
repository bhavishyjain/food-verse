import copy
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models import MealPlanRequest, UserProfile
from backend.app.services.recommendations import build_meal_plan, target_for


def profile(**changes):
    base = {"age": 30, "height_cm": 170, "weight_kg": 70, "activity": "moderate", "energy_basis": "manual", "goal": "balanced", "diet": "everything", "allergies": [], "dislikes": [], "health_notes": "", "pregnant_or_breastfeeding": False}
    base.update(changes)
    return base


def meal(slot, name="Bean bowl"):
    return {"slot": slot, "name": name, "description": "Simple meal", "ingredients": ["beans", "rice", "tomato"], "portion": "one bowl", "macros": {"calories": 500, "protein": 25, "carbs": 63, "fat": 17}, "reason": "Fits the plan"}


def generated(days=1):
    names = ["Today"] if days == 1 else ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    return {"days": [{"day": day, "meals": [meal(slot) for slot in ("Breakfast", "Lunch", "Snack", "Dinner")]} for day in names],
            "alternatives": [{"day": day, "replaces": "Lunch", "meal": meal("Lunch", "Lentil salad")} for day in names], "coach_note": "Vary vegetables through the week."}


class MealPlannerTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_profile_validation_rejects_minor_and_pregnancy(self):
        self.assertEqual(self.client.post("/api/meal-plan", json={"profile": profile(age=16), "period": "daily", "manual_calories": 2000}).status_code, 422)
        self.assertEqual(self.client.post("/api/meal-plan", json={"profile": profile(pregnant_or_breastfeeding=True), "period": "daily", "manual_calories": 2000}).status_code, 422)
        self.assertEqual(self.client.post("/api/meal-plan", json={"profile": profile(allergies=["Peanuts"], dislikes=["peanuts"]), "period": "daily", "manual_calories": 2000}).status_code, 422)

    def test_energy_and_macros_derived_from_profile(self):
        request = MealPlanRequest(profile=UserProfile(**profile(energy_basis="female_equation", goal="muscle-gain")), period="daily", manual_calories=None)
        target, method = target_for(request)
        self.assertGreater(target.calories, 1500)
        self.assertIn("Mifflin-St Jeor", method)
        self.assertAlmostEqual(target.protein * 4 / target.calories, .30, delta=.01)

    def test_daily_plan_has_calculated_totals_and_alternative(self):
        with patch("backend.app.services.recommendations.ask_json", return_value=generated()):
            response = self.client.post("/api/meal-plan", json={"profile": profile(), "period": "daily", "manual_calories": 2000})
        self.assertEqual(response.status_code, 200, response.text)
        result = response.json()
        self.assertEqual(result["days"][0]["totals"]["calories"], 2000)
        self.assertEqual(len(result["alternatives"]), 1)
        self.assertEqual(result["target"]["calories"], 2000)

    def test_weekly_plan_has_seven_days(self):
        with patch("backend.app.services.recommendations.ask_json", return_value=generated(7)):
            response = self.client.post("/api/meal-plan", json={"profile": profile(), "period": "weekly", "manual_calories": 2000})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(len(response.json()["days"]), 7)

    def test_allergen_and_vegan_conflicts_fail_closed(self):
        data = generated()
        data["days"][0]["meals"][0]["ingredients"] = ["peanuts", "rice"]
        request = MealPlanRequest(profile=UserProfile(**profile(allergies=["Peanuts"])), period="daily", manual_calories=2000)
        with patch("backend.app.services.recommendations.ask_json", side_effect=lambda *args, **kwargs: copy.deepcopy(data)) as model:
            with self.assertRaises(Exception) as caught:
                build_meal_plan(request)
        self.assertEqual(caught.exception.status_code, 502)
        self.assertEqual(model.call_count, 2)
        vegan = MealPlanRequest(profile=UserProfile(**profile(diet="vegan")), period="daily", manual_calories=2000)
        data["days"][0]["meals"][0]["ingredients"] = ["milk", "rice"]
        with patch("backend.app.services.recommendations.ask_json", side_effect=lambda *args, **kwargs: copy.deepcopy(data)):
            with self.assertRaises(Exception) as caught:
                build_meal_plan(vegan)
        self.assertEqual(caught.exception.status_code, 502)

    def test_plant_milk_is_not_rejected_as_animal_product(self):
        data = generated()
        data["days"][0]["meals"][0]["ingredients"] = ["oat milk", "rice"]
        request = MealPlanRequest(profile=UserProfile(**profile(diet="vegan")), period="daily", manual_calories=2000)
        with patch("backend.app.services.recommendations.ask_json", return_value=data):
            plan = build_meal_plan(request)
        self.assertEqual(plan.days[0].meals[0].ingredients[0], "oat milk")


if __name__ == "__main__":
    unittest.main()
