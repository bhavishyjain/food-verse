from pathlib import Path

from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool

from .models import CookingGuidance, FoodAnalysis, FreshnessAnalysis, HygieneAnalysis, MealPlan, MealPlanRequest, Recipe, RecipeRequest
from .services.food_analysis import analyze_food
from .services.freshness import analyze_freshness
from .services.hygiene import analyze_hygiene
from .services.model_provider import ask_json, model_ready, provider_name, transcribe_audio, validate_output
from .services.recommendations import build_meal_plan, build_recipe, build_recipe_from_image
from .services.storage import clear_reports, list_reports, save_report

app = FastAPI(title="FoodVerse AI API", description="Multimodal food intelligence services.", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


async def read_upload(file: UploadFile, prefix: str, limit_mb: int) -> bytes:
    if not file.content_type or not file.content_type.startswith(prefix):
        raise HTTPException(status_code=415, detail=f"Please upload a {prefix.rstrip('/')} file.")
    content = await file.read(limit_mb * 1024 * 1024 + 1)
    if len(content) > limit_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File must be smaller than {limit_mb} MB.")
    if not content:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    return content


@app.get("/api/health")
def health() -> dict:
    return {"status": "healthy", "ai_ready": model_ready(), "provider": provider_name() if model_ready() else None, "services": ["vision", "nutrition", "freshness", "hygiene", "audio", "cooking", "planner"]}


@app.post("/api/analyze/food", response_model=FoodAnalysis)
async def food_analysis(file: UploadFile | None = File(None), text_context: str = Form(""), audio_file: UploadFile | None = File(None), session: str | None = Header(None, alias="X-FoodVerse-Session")) -> FoodAnalysis:
    context = text_context.strip()[:500]
    if not file and not audio_file and not context:
        raise HTTPException(status_code=400, detail="Provide a food image, audio note, or text context.")
    content = await read_upload(file, "image/", 10) if file else None
    if audio_file:
        audio = await read_upload(audio_file, "audio/", 20)
        transcript = await run_in_threadpool(transcribe_audio, audio, audio_file.filename or "audio.webm", audio_file.content_type or "audio/webm")
        context = f"{context}\nSpoken context: {transcript}".strip()
    result = await run_in_threadpool(analyze_food, content, file.content_type if file else None, context)
    await run_in_threadpool(save_report, session, "food", result.dish, result.insights[0] if result.insights else result.nutrition_source, result)
    return result


@app.post("/api/analyze/freshness", response_model=FreshnessAnalysis)
async def freshness_analysis(file: UploadFile = File(...), storage_time: str = Form(""), storage_type: str = Form(""), audio_file: UploadFile | None = File(None), session: str | None = Header(None, alias="X-FoodVerse-Session")) -> FreshnessAnalysis:
    content = await read_upload(file, "image/", 10)
    context = f"Reported storage time: {storage_time[:100] or 'unknown'}; reported storage type: {storage_type[:100] or 'unknown'}."
    if audio_file:
        audio = await read_upload(audio_file, "audio/", 20)
        transcript = await run_in_threadpool(transcribe_audio, audio, audio_file.filename or "audio.webm", audio_file.content_type or "audio/webm")
        context += f" Spoken note: {transcript[:400]}"
    result = await run_in_threadpool(analyze_freshness, content, file.content_type or "", context)
    await run_in_threadpool(save_report, session, "freshness", result.item_name, result.warning, result)
    return result


@app.post("/api/analyze/hygiene", response_model=HygieneAnalysis)
async def hygiene_analysis(file: UploadFile = File(...), session: str | None = Header(None, alias="X-FoodVerse-Session")) -> HygieneAnalysis:
    content = await read_upload(file, "video/", 100)
    if not model_ready():
        raise HTTPException(status_code=503, detail="AI analysis is unavailable. Configure OPENAI_API_KEY or GROQ_API_KEY on the API server.")
    try:
        result = await run_in_threadpool(analyze_hygiene, content, Path(file.filename or "video.mp4").suffix.lower())
        await run_in_threadpool(save_report, session, "hygiene", "Kitchen hygiene review", result.alerts[0].message if result.alerts else result.status, result)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/cooking/audio", response_model=CookingGuidance)
async def cooking_audio(file: UploadFile = File(...), session: str | None = Header(None, alias="X-FoodVerse-Session")) -> CookingGuidance:
    content = await read_upload(file, "audio/", 20)
    transcript = await run_in_threadpool(transcribe_audio, content, file.filename or "audio.webm", file.content_type or "audio/webm")
    result = await run_in_threadpool(lambda: ask_json("Give concise contextual cooking guidance based on this spoken request. Return JSON only with guidance, steps (array), and safety_note. Do not invent ingredients the user did not mention.", text=transcript))
    guidance = validate_output(CookingGuidance, {"transcript": transcript, **result})
    await run_in_threadpool(save_report, session, "cooking", "Voice cooking guidance", guidance.guidance, guidance)
    return guidance


@app.post("/api/meal-plan", response_model=MealPlan)
def meal_plan(request: MealPlanRequest, session: str | None = Header(None, alias="X-FoodVerse-Session")) -> MealPlan:
    result = build_meal_plan(request)
    save_report(session, "meal-plan", "Personal meal plan", result.coach_note, result)
    return result


@app.post("/api/recipe", response_model=Recipe)
def recipe(request: RecipeRequest, session: str | None = Header(None, alias="X-FoodVerse-Session")) -> Recipe:
    result = build_recipe(request)
    save_report(session, "recipe", result.title, result.tip, result)
    return result


@app.post("/api/recipe/from-image", response_model=Recipe)
async def recipe_from_image(file: UploadFile = File(...), prompt: str = Form(""), session: str | None = Header(None, alias="X-FoodVerse-Session")) -> Recipe:
    content = await read_upload(file, "image/", 10)
    result = await run_in_threadpool(build_recipe_from_image, content, file.content_type or "", prompt[:500])
    await run_in_threadpool(save_report, session, "recipe", result.title, result.tip, result)
    return result


@app.get("/api/history")
def history(session: str | None = Header(None, alias="X-FoodVerse-Session")) -> list[dict]:
    return list_reports(session)


@app.delete("/api/history")
def delete_history(session: str | None = Header(None, alias="X-FoodVerse-Session")) -> dict:
    return {"deleted": clear_reports(session)}
