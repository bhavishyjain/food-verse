# FoodVerse AI

FoodVerse AI is a React and FastAPI food intelligence workspace. It accepts food photos, kitchen video, text prompts, and voice notes, then presents food recognition, estimated nutrition, visual freshness signals, hygiene observations, recipes, and meal plans.

## Current capabilities

| Workflow | Input | Output |
| --- | --- | --- |
| Food recognition | Food image with optional text or voice context; text or voice alone also supported | Dish and food items with model stated confidence, categories and portion estimates |
| Nutrition | Recognized food and portion weights | Estimated calories, protein, carbohydrates, fats, fiber and a labeled heuristic health score |
| Freshness | Dedicated photo upload with optional storage time, storage type, and voice note | Fresh / Moderately Fresh / Spoiled visual assessment, descriptive image features, cautious safety guidance |
| Kitchen hygiene | Video upload | Up to eight frames sampled about 30 seconds apart, observable checks for gloves, hair restraints, handling and surfaces, rule-based compliance score and alerts |
| Cooking assistant | Text, ingredient image, or audio file | Recipe, steps, contextual guidance, and safety notes; audio is transcribed first |
| Meal planner | Adult profile, activity, energy target basis, goal, diet, allergies and dislikes | Daily or seven-day plan, estimated macro totals, ingredient lists, meal swaps and cautions |
| Reports | Browser-scoped history | Recent structured results and a clear-history action; uploaded media is not retained |

Images are EXIF oriented, resized, converted to RGB, and conditionally enhanced for low light recognition. Freshness judgments use the normalized original view. When every item matches the small built-in per-100g ingredient table and has an estimated weight, the backend calculates macros from that table. Otherwise it uses the model's labeled estimate. All model output is screened through Pydantic response schemas. The app does **not** show fabricated fallback results if the API or model provider is unavailable.

## Run locally

1. Install frontend dependencies: `npm install`
2. Create a Python environment and install backend dependencies: `pip install -r backend/requirements.txt`
3. Set `OPENAI_API_KEY` or `GROQ_API_KEY` on the API server. The app uses OpenAI when both are present; set `FOODVERSE_AI_PROVIDER=groq` to select Groq. Optional model overrides are `OPENAI_VISION_MODEL` (default `gpt-4.1-mini`) and `GROQ_VISION_MODEL` (default `qwen/qwen3.8-27b`).
4. Start the API: `uvicorn backend.app.main:app --reload --port 8000`
5. Start React: `npm run dev`

Open <http://localhost:5173>. Vite proxies `/api` to FastAPI. API docs are at <http://localhost:8000/docs>; `/api/health` reports whether an AI key is configured. Docker Compose can also start both services; pass your selected provider key to the API container. Structured report history is stored in `backend/data/foodverse.sqlite3` by default; set `FOODVERSE_DB_PATH` to change that path.

Run the focused backend checks with `python -m unittest discover -s backend/tests -v`, and verify the frontend with `npm run build`.

## Activity 1.1–1.4 implementation

1. **Requirements:** `backend/requirements.txt` pins only imported backend libraries. React dependencies are separately recorded in `package.json`; unused packages from the reference screenshot are intentionally absent.
2. **Isolated environment:** create and activate a Python virtual environment before installing the backend requirements. The same command is used in local and container setup.
3. **Food recognition:** the upload route validates file type and size, preprocesses images, combines optional spoken or typed context, calls a vision model, rejects non-food input, and returns structured dish and ingredient classifications.
4. **Nutrition:** recognized items and estimated weights are matched to built-in approximate nutrient profiles when possible. A deterministic macro/fiber/calorie heuristic produces the health score. The response states whether nutrition came from the reference table or model estimate.

## Activity 1.5–1.8 implementation

5. **Freshness features:** the dedicated route validates and normalizes the image, then applies median filtering for descriptive brightness, color variation, texture variation, and dark-area metrics. These pixel statistics are not spoilage diagnoses.
6. **Freshness classification:** the vision model reports visible signals and one of three freshness states or insufficient evidence. The application maps the state to conservative guidance and never claims that an apparently fresh item is safe to eat.
7. **Kitchen hygiene:** FFmpeg samples representative frames. The model records visible status for four defined checks and approximate alert times; deterministic weighted aggregation computes a score only from visible checks. Missing evidence is marked “Not visible.”
8. **Smart cooking:** text and ingredient-photo routes return structured ingredients, ordered steps, tips and safety notes. Voice notes produce a transcript and contextual guidance.

## Activity 1.9–1.13 implementation and checks

9. **User profiles:** the planner accepts a structured Pydantic profile with adult age, height, weight, activity, goal, eating style, allergies, avoided foods and optional health context. Invalid ranges, overlapping restrictions and pregnancy/breastfeeding are rejected. Raw health measurements are not saved to report history.
10. **Personalized planning:** users choose a one-day or seven-day plan. A user-selected energy target or a labeled Mifflin-St Jeor estimate informs goal-based macro targets. The model supplies meals, ingredient lists and swaps; the server calculates daily totals and rejects outputs that exceed calorie tolerance, have inconsistent macros, omit meal slots, or explicitly conflict with dietary restrictions. This is a rough adult planning aid, not a clinical prescription.
11. **Frontend integration:** React uses REST endpoints for all modules and direct workspace paths: `/food-recognition`, `/freshness-detector`, `/hygiene-monitor`, `/kitchen-assistant`, and `/meal-planner`. Browser Back restores the selected module.
12. **Edge-case checks:** backend tests cover low-resolution and corrupt photos, malformed video, text-only and missing inputs, nutrition references, profile bounds, dietary conflicts, daily and weekly plan structure, and calculated totals. Build and test commands are listed above.
13. **Demo readiness:** the UI, API contracts, error states and navigation were reviewed locally. The model-backed workflows still require a valid `OPENAI_API_KEY` or `GROQ_API_KEY` and have not been verified against live provider output in this environment. A plan cannot report real adherence without logged meals.

## Architecture and limits

The React client calls modular FastAPI services for model invocation, image preprocessing, nutrition calculations, food analysis, sampled video review, transcription, recommendations, and SQLite report storage. Uploaded media is processed in memory or a temporary directory and is not persisted. Structured results are saved under a random browser token and can be cleared from the dashboard. The configured model provider receives submitted content for inference. There is no account authentication or cross-device profile sync yet; the browser token is suitable only for a local prototype.

Nutrition, portions, health scores, freshness, and hygiene findings are estimates. The built-in nutrient table is an illustrative subset, not a verified comprehensive food database. A photograph cannot prove food is microbiologically safe; sampled footage cannot replace a formal inspection. For production use, add account authorization, encrypted storage with retention controls, a verified nutrition database such as USDA FoodData Central, specialist validation datasets, asynchronous video jobs, rate limiting, observability, and human review for safety decisions.

Energy estimates use the [Mifflin-St Jeor resting-energy equation](https://pubmed.ncbi.nlm.nih.gov/2305711/) with simple activity assumptions. The [NIDDK Body Weight Planner](https://www.niddk.nih.gov/health-information/weight-management/body-weight-planner) also limits its automated planning to adults and excludes pregnancy and breastfeeding. Food allergies still require label and preparation checks; matching an ingredient list cannot rule out hidden ingredients or cross-contact.
