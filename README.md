# FoodVerse AI

FoodVerse AI is a React and FastAPI food intelligence workspace. It accepts food photos, kitchen video, text prompts, and voice notes, then presents food recognition, estimated nutrition, visual freshness signals, hygiene observations, recipes, and meal plans.

**Mentor links:** [GitHub source](https://github.com/bhavishyjain/food-verse) and [Streamlit demo](https://food-verse-dmym3c7mhe9igb4evk492k.streamlit.app/) deployed from [`streamlit_app.py`](streamlit_app.py). The Streamlit app reuses the same Python analysis services; the React/FastAPI interface remains in this repository.

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

## Publish a Streamlit demo

Streamlit Community Cloud runs a Streamlit Python entrypoint, so `streamlit_app.py` is a companion interface for demonstrating the existing analysis services. It does not host the React frontend or launch FastAPI. The root `requirements.txt` installs its dependencies, and `.streamlit/config.toml` supplies the theme and upload limit.

1. Push the repository to GitHub. Keep `.env` and `.streamlit/secrets.toml` uncommitted. Confirm the repository is public if you want your mentor to view its source without a GitHub invitation.
2. Sign in to [Streamlit Community Cloud](https://share.streamlit.io/) and connect your GitHub account. Create an app using repository `bhavishyjain/food-verse`, branch `main`, and entrypoint `streamlit_app.py`. Select Python 3.12 in Advanced settings.
3. In Advanced settings → Secrets, add **one** provider key, for example `OPENAI_API_KEY = "..."` or `GROQ_API_KEY = "..."`. If using Groq while an OpenAI key is also present, set `FOODVERSE_AI_PROVIDER = "groq"`. Never put real keys in GitHub or a public URL. The example format is in `.streamlit/secrets.toml.example`.
4. After deployment, open the Streamlit URL in a private browser window and try one text recipe plus one small image. Send that URL and the GitHub repository URL to your mentor. If the model key is absent, the demo opens but analysis buttons explain that setup is needed.

For local testing, install `pip install -r requirements.txt`, set a provider key in your shell, and run `streamlit run streamlit_app.py`. Large video jobs may be limited by Streamlit Community Cloud resources; use short clips for demonstration.

## Activity 1 — Project setup

1. **Requirements:** `backend/requirements.txt` pins the backend libraries; React dependencies are listed in `package.json`.
2. **Isolated environment:** install the Python dependencies in a project virtual environment to keep development and deployment reproducible.

## Activity 2 — Food recognition and nutrition

1. **Food recognition:** validate and preprocess uploaded images, combine optional text or voice context, and return structured dish and ingredient predictions.
2. **Nutrition analysis:** estimate calories, macros, fiber and a heuristic health score from portion estimates and a small nutrient reference table, labeling model estimates when no reference matches.

## Activity 3 — Freshness detection

1. **Visual features:** normalize images and report descriptive brightness, color, texture and dark-area measurements.
2. **Freshness classification:** return Fresh, Moderately Fresh, Spoiled or insufficient evidence with visible signs and cautious recommendations. A photo cannot establish food safety.

## Activity 4 — Kitchen monitoring and cooking

1. **Hygiene monitoring:** sample kitchen video frames, evaluate visible glove use, hair restraints, handling and surfaces, then generate a score and alerts from observed checks.
2. **Cooking assistant:** turn text, ingredient photos or transcribed voice requests into recipes, ordered steps, tips and safety notes.

## Activity 5 — Personalized meal planning

1. **User profiles:** validate adult health metrics, goals, preferences, allergies and avoided foods before planning; raw health measurements are not saved to report history.
2. **Daily and weekly plans:** calculate estimated calorie and macro targets, generate meals and alternatives, and reject plans that conflict with stated dietary constraints.

## Activity 6 — Integration and validation

1. **Frontend integration:** connect React pages to the FastAPI routes for all modules and support direct navigation to each workspace.
2. **Edge-case checks:** test low-resolution or corrupt images, malformed video, missing inputs, profile limits, dietary conflicts and plan totals.
3. **Demo readiness:** review the interface, API responses and navigation locally, then verify the Streamlit companion after deployment. A plan cannot report real adherence without logged meals.

## Architecture and limits

The React client calls modular FastAPI services for model invocation, image preprocessing, nutrition calculations, food analysis, sampled video review, transcription, recommendations, and SQLite report storage. Uploaded media is processed in memory or a temporary directory and is not persisted. Structured results are saved under a random browser token and can be cleared from the dashboard. The configured model provider receives submitted content for inference. There is no account authentication or cross-device profile sync yet; the browser token is suitable only for a local prototype.

Nutrition, portions, health scores, freshness, and hygiene findings are estimates. The built-in nutrient table is an illustrative subset, not a verified comprehensive food database. A photograph cannot prove food is microbiologically safe; sampled footage cannot replace a formal inspection. For production use, add account authorization, encrypted storage with retention controls, a verified nutrition database such as USDA FoodData Central, specialist validation datasets, asynchronous video jobs, rate limiting, observability, and human review for safety decisions.

Energy estimates use the [Mifflin-St Jeor resting-energy equation](https://pubmed.ncbi.nlm.nih.gov/2305711/) with simple activity assumptions. The [NIDDK Body Weight Planner](https://www.niddk.nih.gov/health-information/weight-management/body-weight-planner) also limits its automated planning to adults and excludes pregnancy and breastfeeding. Food allergies still require label and preparation checks; matching an ingredient list cannot rule out hidden ingredients or cross-contact.
