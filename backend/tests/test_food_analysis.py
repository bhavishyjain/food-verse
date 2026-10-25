import unittest
from io import BytesIO
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from PIL import Image

from backend.app.main import app
from backend.app.models import FoodItem
from backend.app.services.image_processing import prepare_food_image
from backend.app.services.nutrition import reference_nutrition


def sample_image() -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (120, 80), (120, 40, 30)).save(buffer, format="PNG")
    return buffer.getvalue()


class FoodAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_image_preprocessing_resizes_and_orients(self):
        original, _ = prepare_food_image(sample_image(), "image/png")
        with Image.open(BytesIO(original)) as image:
            self.assertEqual(image.size, (120, 80))
            self.assertEqual(image.mode, "RGB")

    def test_reference_values_scale_with_portion(self):
        nutrition = reference_nutrition([FoodItem(name="Apple", confidence=.8, portion="200 g", grams=200)])
        self.assertEqual(nutrition.calories, 104)
        self.assertEqual(nutrition.carbs, 27.6)

    def test_food_endpoint_uses_image_and_reference_nutrition(self):
        model_output = {
            "is_food": True, "dish": "Apple", "confidence": .8,
            "items": [{"name": "Apple", "confidence": .8, "portion": "100 g", "grams": 100, "category": "fruit"}],
            "nutrition": {"calories": 999, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0},
            "freshness": "Fresh", "freshness_confidence": .6,
            "visual_signals": ["No visible bruising"], "insights": ["Wash before eating"], "limitations": [],
        }
        with patch("backend.app.services.food_analysis.ask_json", return_value=model_output):
            response = self.client.post("/api/analyze/food", files={"file": ("apple.png", sample_image(), "image/png")})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["nutrition"]["calories"], 52)
        self.assertIn("reference", response.json()["nutrition_source"])

    def test_text_only_cannot_report_visual_freshness(self):
        model_output = {
            "is_food": True, "dish": "Apple", "confidence": .8,
            "items": [{"name": "Apple", "confidence": .8, "portion": "100 g", "grams": 100}],
            "nutrition": None, "freshness": "Fresh", "freshness_confidence": .9,
            "visual_signals": ["red"], "insights": [], "limitations": [],
        }
        with patch("backend.app.services.food_analysis.ask_json", return_value=model_output):
            response = self.client.post("/api/analyze/food", data={"text_context": "I ate an apple"})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIsNone(response.json()["freshness"])
        self.assertEqual(response.json()["confidence"], 0)

    def test_non_food_rejected(self):
        with patch("backend.app.services.food_analysis.ask_json", return_value={"is_food": False}):
            response = self.client.post("/api/analyze/food", files={"file": ("desk.png", sample_image(), "image/png")})
        self.assertEqual(response.status_code, 422)

    def test_report_history_is_scoped_and_can_be_cleared(self):
        output = {
            "is_food": True, "dish": "Apple", "confidence": .8,
            "items": [{"name": "Apple", "confidence": .8, "portion": "100 g", "grams": 100}],
            "nutrition": None, "freshness": None, "freshness_confidence": None,
            "visual_signals": [], "insights": ["Wash before eating"], "limitations": [],
        }
        session = "a" * 32
        with TemporaryDirectory() as folder, patch.dict("os.environ", {"FOODVERSE_DB_PATH": str(Path(folder) / "reports.sqlite3")}), patch("backend.app.services.food_analysis.ask_json", return_value=output):
            headers = {"X-FoodVerse-Session": session}
            self.assertEqual(self.client.post("/api/analyze/food", data={"text_context": "I ate an apple"}, headers=headers).status_code, 200)
            self.assertEqual(len(self.client.get("/api/history", headers=headers).json()), 1)
            self.assertEqual(self.client.get("/api/history", headers={"X-FoodVerse-Session": "b" * 32}).json(), [])
            self.assertEqual(self.client.delete("/api/history", headers=headers).json()["deleted"], 1)
            self.assertEqual(self.client.get("/api/history", headers=headers).json(), [])


if __name__ == "__main__":
    unittest.main()
