import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.freshness import extract_features
from backend.app.services.hygiene import score_observations
from backend.tests.test_food_analysis import sample_image


class NextActivitiesTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_freshness_features_are_normalized(self):
        from backend.app.services.image_processing import prepare_food_image
        original, _ = prepare_food_image(sample_image(), "image/png")
        values = extract_features(original)
        self.assertTrue(all(0 <= value <= 1 for value in values.model_dump().values()))

    def test_freshness_endpoint_maps_spoilage_to_cautious_advice(self):
        output = {"is_food": True, "item_name": "Apple", "level": "Spoiled", "confidence": .8, "visual_signals": ["Visible fuzzy patch"]}
        with patch("backend.app.services.freshness.ask_json", return_value=output):
            response = self.client.post("/api/analyze/freshness", data={"storage_time": "3 days", "storage_type": "Refrigerated"}, files={"file": ("apple.png", sample_image(), "image/png")})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["level"], "Spoiled")
        self.assertIn("Do not consume", response.json()["recommendation"])
        self.assertIn("dark_pixel_ratio", response.json()["features"])

    def test_hygiene_score_excludes_invisible_checks(self):
        result = score_observations({"checks": [
            {"label": "Glove usage", "status": "Pass"},
            {"label": "Hair restraint", "status": "Review"},
        ], "alerts": []}, 2)
        self.assertEqual(result.score, 50)
        self.assertEqual(result.checks[2].status, "Not visible")
        self.assertIsNone(result.checks[2].score)
        self.assertEqual(score_observations({"checks": [], "alerts": []}, 1).score, None)

    def test_ingredient_photo_recipe_uses_image_model(self):
        output = {"title": "Apple salad", "subtitle": "Simple", "time": "10 min", "difficulty": "Easy", "ingredients": ["Apple"], "steps": ["Wash and slice the apple."], "tip": "Serve fresh.", "safety_note": "Wash produce."}
        with patch("backend.app.services.recommendations.ask_json", return_value=output) as model:
            response = self.client.post("/api/recipe/from-image", data={"prompt": "Make a salad"}, files={"file": ("apple.png", sample_image(), "image/png")})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["title"], "Apple salad")
        self.assertTrue(model.call_args.args[1][0]["type"] == "input_image")

    def test_small_or_corrupt_image_is_rejected_before_model_call(self):
        from io import BytesIO
        from PIL import Image
        buffer = BytesIO()
        Image.new("RGB", (32, 32), "red").save(buffer, format="PNG")
        with patch("backend.app.services.freshness.ask_json") as model:
            small = self.client.post("/api/analyze/freshness", files={"file": ("small.png", buffer.getvalue(), "image/png")})
            corrupt = self.client.post("/api/analyze/freshness", files={"file": ("broken.png", b"not an image", "image/png")})
        self.assertEqual(small.status_code, 422)
        self.assertEqual(corrupt.status_code, 422)
        model.assert_not_called()

    def test_invalid_video_and_partial_food_input(self):
        with patch("backend.app.main.model_ready", return_value=True):
            response = self.client.post("/api/analyze/hygiene", files={"file": ("bad.mp4", b"invalid video", "video/mp4")})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(self.client.post("/api/analyze/food").status_code, 400)


if __name__ == "__main__":
    unittest.main()
