"""Streamlit Community Cloud companion for the React/FastAPI FoodVerse project.

This imports the same analysis services as the API; it does not start a second API server.
"""

import os
from pathlib import Path

import streamlit as st
from fastapi import HTTPException
from pydantic import ValidationError


st.set_page_config(page_title="FoodVerse AI · Demo", page_icon="🥗", layout="wide", initial_sidebar_state="expanded")
st.markdown(f"<style>{(Path(__file__).parent / '.streamlit' / 'style.css').read_text()}</style>", unsafe_allow_html=True)

# Streamlit Cloud secrets are available only at runtime. Map them before the
# model provider module is imported so the existing provider selection works.
try:
    cloud_secrets = dict(st.secrets)
except FileNotFoundError:
    cloud_secrets = {}
for setting in ("OPENAI_API_KEY", "GROQ_API_KEY", "FOODVERSE_AI_PROVIDER", "OPENAI_VISION_MODEL", "GROQ_VISION_MODEL"):
    if setting in cloud_secrets and not os.getenv(setting):
        os.environ[setting] = str(cloud_secrets[setting])

from backend.app.models import MealPlanRequest, RecipeRequest, UserProfile  # noqa: E402
from backend.app.services.food_analysis import analyze_food  # noqa: E402
from backend.app.services.freshness import analyze_freshness  # noqa: E402
from backend.app.services.hygiene import analyze_hygiene  # noqa: E402
from backend.app.services.model_provider import model_ready, provider_name, transcribe_audio  # noqa: E402
from backend.app.services.recommendations import build_meal_plan, build_recipe, build_recipe_from_image  # noqa: E402


GITHUB_URL = "https://github.com/bhavishyjain/food-verse"
MAX_IMAGE = 10 * 1024 * 1024
MAX_AUDIO = 20 * 1024 * 1024
MAX_VIDEO = 100 * 1024 * 1024
PAGES = ["Overview", "Food recognition", "Freshness", "Kitchen hygiene", "Cooking assistant", "Meal planner"]


def go_to(page: str) -> None:
    st.session_state["workspace_page"] = page


def page_header(kicker: str, title: str, description: str) -> None:
    st.markdown(
        f'<div class="fv-page-head"><span class="fv-kicker">{kicker}</span>'
        f'<h1>{title}</h1><p>{description}</p></div>',
        unsafe_allow_html=True,
    )


def capability_card(number: int, icon: str, title: str, description: str, tags: tuple[str, ...], page: str) -> None:
    with st.container(key=f"fv_cap_{number}"):
        tag_html = "".join(f"<span>{tag}</span>" for tag in tags)
        st.markdown(
            f'<div class="fv-card"><div class="fv-card-head"><span class="fv-card-icon">{icon}</span>'
            f'<span class="fv-card-number">{number:02d} / 05</span></div><h3>{title}</h3>'
            f'<p>{description}</p><div class="fv-tags">{tag_html}</div></div>',
            unsafe_allow_html=True,
        )
        st.button("Open workspace →", key=f"open_{number}", on_click=go_to, args=(page,))


def uploaded_bytes(upload, limit: int) -> bytes:
    content = upload.getvalue()
    if not content or len(content) > limit:
        raise ValueError(f"Upload a nonempty file smaller than {limit // (1024 * 1024)} MB.")
    return content


def show_error(error: Exception) -> None:
    if isinstance(error, HTTPException):
        st.error(str(error.detail))
    elif isinstance(error, (ValueError, ValidationError)):
        st.error(str(error))
    else:
        st.error("Analysis failed. Check the app setup and try again.")


def run_action(action, key: str) -> None:
    if not model_ready():
        st.error("AI analysis is unavailable until the app owner configures OPENAI_API_KEY or GROQ_API_KEY in Streamlit Cloud secrets.")
        return
    try:
        with st.spinner("Analyzing…"):
            st.session_state[key] = action()
    except Exception as error:
        st.session_state.pop(key, None)
        show_error(error)


with st.sidebar:
    st.markdown('<div class="fv-brand"><span class="fv-brand-mark">✳</span><div><div class="fv-brand-name">foodverse<i>.</i></div><div class="fv-brand-sub">FOOD INTELLIGENCE WORKSPACE</div></div></div>', unsafe_allow_html=True)
    page = st.radio("WORKSPACE", PAGES, key="workspace_page")
    st.divider()
    if model_ready():
        st.markdown(f'<div class="fv-status"><span class="fv-status-dot"></span><div><strong>{provider_name().title()} model connected</strong><small>Ready for food insights and guidance</small></div></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="fv-status off"><span class="fv-status-dot"></span><div><strong>AI setup needed</strong><small>Add OPENAI_API_KEY or GROQ_API_KEY in Streamlit Cloud secrets.</small></div></div>', unsafe_allow_html=True)
    st.link_button("View React + FastAPI source", GITHUB_URL)
    st.markdown('<div class="fv-side-note">Streamlit demo · UI v2.0<br>Built from the shared FoodVerse services.</div>', unsafe_allow_html=True)


if page == "Overview":
    hero_status = "Model connected · Ready for input" if model_ready() else "Connect an AI model to start analysis"
    st.markdown('<div class="fv-overline">FOODVERSE AI / CONTROL CENTER &nbsp;&nbsp;·&nbsp;&nbsp; IMAGE — VIDEO — AUDIO — TEXT</div>', unsafe_allow_html=True)
    st.markdown(
        '<section class="fv-hero"><div class="fv-hero-copy"><span class="fv-hero-tag"><span></span>MULTIMODAL FOOD INTELLIGENCE</span>'
        '<h1>Every food decision,<br><em>more informed.</em></h1>'
        '<p>Understand what you eat, how fresh it looks, how safely it is prepared, and what to cook next — all in one workspace.</p>'
        f'<div class="fv-hero-status">{hero_status}</div></div>'
        '<div class="fv-hero-art" aria-hidden="true"><div class="fv-orbit"></div><div class="fv-orbit two"></div>'
        '<div class="fv-core"><span>✳</span><strong>FoodVerse</strong><small>AI ENGINE</small></div>'
        '<span class="fv-node image">▧ &nbsp;Image</span><span class="fv-node audio">◉ &nbsp;Audio</span><span class="fv-node text">☷ &nbsp;Text</span>'
        '<span class="fv-node nutrition">Nutrition &nbsp;↗</span><span class="fv-node freshness">Freshness &nbsp;↗</span>'
        '<span class="fv-node guidance">Guidance &nbsp;↗</span></div></section>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="fv-section-head"><div><span class="fv-kicker">THE PLATFORM</span><h2>One workspace. Five ways to see more.</h2></div><p>Choose an input. FoodVerse turns model output into useful estimates, visual observations, alerts and next steps.</p></div>', unsafe_allow_html=True)
    first_row = st.columns(3, gap="medium")
    cards = [
        (1, "▧", "Food recognition", "Identify dishes and estimate portions, macros, calories and a health score.", ("IMAGE", "NUTRITION"), "Food recognition"),
        (2, "❋", "Freshness signals", "Review visible quality cues with storage context and careful safety advice.", ("IMAGE", "SAFETY"), "Freshness"),
        (3, "◇", "Kitchen hygiene", "Sample footage for gloves, hair restraints, handling and surfaces.", ("VIDEO", "ALERTS"), "Kitchen hygiene"),
        (4, "♨", "Cooking assistant", "Turn ingredient photos, text or voice into practical recipes.", ("IMAGE", "TEXT", "AUDIO"), "Cooking assistant"),
        (5, "◈", "Personal meal plans", "Build a day or week around your profile and nutrition goals.", ("PROFILE", "PLANNING"), "Meal planner"),
    ]
    for column, card in zip(first_row, cards[:3]):
        with column:
            capability_card(*card)
    second_row = st.columns(3, gap="medium")
    for column, card in zip(second_row, cards[3:]):
        with column:
            capability_card(*card)
    st.markdown('<div class="fv-trust"><span class="fv-trust-mark">♧</span><div><strong>Evidence first, estimates clearly labeled.</strong><p>Visual freshness is a screening signal, not a microbiological test. Nutrition depends on visible portions and ingredients; hygiene checks use sampled frames.</p></div></div>', unsafe_allow_html=True)

elif page == "Food recognition":
    page_header("01 / FOOD ANALYZER", "Food recognition & nutrition", "Upload a food photo, describe the portion, or add a voice note to receive a structured nutrition estimate.")
    with st.form("food_form"):
        photo = st.file_uploader("Food photo", type=["jpg", "jpeg", "png", "webp"])
        context = st.text_area("Food or portion context (optional)", max_chars=500)
        voice = st.file_uploader("Voice note (optional)", type=["mp3", "wav", "m4a", "webm", "ogg"], key="food_voice")
        submitted = st.form_submit_button("Analyze food", type="primary")
    if submitted:
        if not (photo or voice or context.strip()):
            st.warning("Add a photo, voice note or text context.")
        else:
            def action():
                full_context = context.strip()
                if voice:
                    transcript = transcribe_audio(uploaded_bytes(voice, MAX_AUDIO), voice.name, voice.type or "audio/webm")
                    full_context = f"{full_context}\nSpoken context: {transcript}".strip()
                return analyze_food(uploaded_bytes(photo, MAX_IMAGE) if photo else None, photo.type if photo else None, full_context)
            run_action(action, "food_result")
    if result := st.session_state.get("food_result"):
        st.subheader(result.dish)
        st.caption(f"Model-stated recognition confidence: {result.confidence:.0%}")
        if result.nutrition:
            cols = st.columns(4)
            for col, label, value in zip(cols, ("Calories", "Protein", "Carbs", "Fat"), (result.nutrition.calories, result.nutrition.protein, result.nutrition.carbs, result.nutrition.fat)):
                col.metric(label, f"{value}{' g' if label != 'Calories' else ' kcal'}")
            st.caption(result.nutrition_source)
        st.write(f"**Heuristic health score:** {result.health_score if result.health_score is not None else 'Unavailable'}/100")
        st.write("**Recognized items:** " + ", ".join(item.name for item in result.items))
        for insight in result.insights:
            st.write(f"• {insight}")
        st.caption(" ".join(result.limitations))

elif page == "Freshness":
    page_header("02 / FOOD SAFETY", "Visual freshness review", "Compare visible food quality cues with your storage context and receive cautious recommendations.")
    with st.form("freshness_form"):
        photo = st.file_uploader("Food photo", type=["jpg", "jpeg", "png", "webp"], key="fresh_photo")
        storage_time = st.text_input("How long has it been stored?", max_chars=100)
        storage_type = st.selectbox("Where was it stored?", ["Unknown", "Refrigerated", "Frozen", "Room temperature"])
        voice = st.file_uploader("Voice note (optional)", type=["mp3", "wav", "m4a", "webm", "ogg"], key="fresh_voice")
        submitted = st.form_submit_button("Check visible freshness", type="primary")
    if submitted:
        if not photo:
            st.warning("Add a food photo.")
        else:
            def action():
                context = f"Reported storage time: {storage_time or 'unknown'}; reported storage type: {storage_type}."
                if voice:
                    context += " Spoken note: " + transcribe_audio(uploaded_bytes(voice, MAX_AUDIO), voice.name, voice.type or "audio/webm")[:400]
                return analyze_freshness(uploaded_bytes(photo, MAX_IMAGE), photo.type, context)
            run_action(action, "fresh_result")
    if result := st.session_state.get("fresh_result"):
        st.subheader(f"{result.item_name}: {result.level or 'Insufficient evidence'}")
        st.caption(f"Model-stated confidence: {result.confidence:.0%}")
        for signal in result.visual_signals:
            st.write(f"• {signal}")
        st.info(result.recommendation)
        st.warning(result.warning)
        with st.expander("Image feature measurements"):
            st.json(result.features.model_dump())
        st.caption(" ".join(result.limitations))

elif page == "Kitchen hygiene":
    page_header("03 / KITCHEN SAFETY", "Kitchen video hygiene review", "Sample footage for visible hygiene indicators, alerts and an evidence-based compliance score.")
    st.caption("The system samples video frames roughly every 30 seconds and assesses only visible evidence.")
    with st.form("hygiene_form"):
        video = st.file_uploader("Kitchen footage", type=["mp4", "mov", "webm"])
        submitted = st.form_submit_button("Review hygiene", type="primary")
    if submitted:
        if not video:
            st.warning("Add a kitchen video.")
        else:
            run_action(lambda: analyze_hygiene(uploaded_bytes(video, MAX_VIDEO), Path(video.name).suffix.lower()), "hygiene_result")
    if result := st.session_state.get("hygiene_result"):
        st.metric("Visible-check compliance", f"{result.score}%" if result.score is not None else "Insufficient evidence")
        st.write(f"**Status:** {result.status} · **Frames reviewed:** {result.frames_analyzed}")
        for check in result.checks:
            st.write(f"**{check.label}:** {check.status}")
        for alert in result.alerts:
            st.warning(f"{alert.time}: {alert.message}")
        st.caption(" ".join(result.limitations))

elif page == "Cooking assistant":
    page_header("04 / SMART KITCHEN", "Smart cooking assistant", "Describe what you have or upload ingredients to get a practical recipe and ordered cooking steps.")
    with st.form("recipe_form"):
        prompt = st.text_area("Ingredients or cooking goal", placeholder="I have chickpeas, tomatoes and spinach…", max_chars=500)
        photo = st.file_uploader("Ingredient photo (optional)", type=["jpg", "jpeg", "png", "webp"], key="recipe_photo")
        voice = st.file_uploader("Voice request (optional)", type=["mp3", "wav", "m4a", "webm", "ogg"], key="recipe_voice")
        submitted = st.form_submit_button("Create recipe", type="primary")
    if submitted:
        if not (prompt.strip() or photo or voice):
            st.warning("Describe a dish, add an ingredient photo, or add a voice request.")
        else:
            def action():
                full_prompt = prompt.strip()
                if voice:
                    transcript = transcribe_audio(uploaded_bytes(voice, MAX_AUDIO), voice.name, voice.type or "audio/webm")
                    full_prompt = f"{full_prompt}\nSpoken request: {transcript}".strip()
                if photo:
                    return build_recipe_from_image(uploaded_bytes(photo, MAX_IMAGE), photo.type, full_prompt)
                return build_recipe(RecipeRequest(prompt=full_prompt))
            run_action(action, "recipe_result")
    if result := st.session_state.get("recipe_result"):
        st.subheader(result.title)
        st.write(result.subtitle)
        st.caption(f"{result.time} · {result.difficulty}")
        st.write("**Ingredients**")
        for ingredient in result.ingredients:
            st.write(f"• {ingredient}")
        st.write("**Steps**")
        for index, step in enumerate(result.steps, 1):
            st.write(f"{index}. {step}")
        st.info(result.tip)
        if result.safety_note:
            st.warning(result.safety_note)

elif page == "Meal planner":
    page_header("05 / PERSONALIZED NUTRITION", "Daily & weekly meal plans", "Build a plan around your profile, goals, eating style and foods to avoid.")
    st.caption("Adult planning aid with estimated targets. It does not replace individualized advice for medical conditions.")
    with st.form("plan_form"):
        a, b, c = st.columns(3)
        age = a.number_input("Age", min_value=18, max_value=100, value=30)
        height = b.number_input("Height (cm)", min_value=120.0, max_value=230.0, value=170.0)
        weight = c.number_input("Weight (kg)", min_value=35.0, max_value=300.0, value=70.0)
        a, b, c = st.columns(3)
        activity = a.selectbox("Activity", ["sedentary", "light", "moderate", "active"], index=2)
        goal = b.selectbox("Goal", ["balanced", "weight-loss", "muscle-gain", "heart-health"])
        diet = c.selectbox("Eating style", ["everything", "vegetarian", "vegan", "pescatarian"])
        a, b = st.columns(2)
        period = a.selectbox("Plan length", ["daily", "weekly"])
        energy_basis = b.selectbox("Energy target basis", ["manual", "female_equation", "male_equation"], format_func=lambda item: {"manual": "My target", "female_equation": "Female equation estimate", "male_equation": "Male equation estimate"}[item])
        calories = st.slider("Daily calorie target", 1400, 3200, 2000, 50, disabled=energy_basis != "manual")
        allergies = st.text_input("Allergies (comma-separated)")
        dislikes = st.text_input("Foods to avoid (comma-separated)")
        health_notes = st.text_area("Health considerations (optional, general context only)", max_chars=300)
        pregnant_or_breastfeeding = st.checkbox("Pregnant or breastfeeding")
        submitted = st.form_submit_button("Build plan", type="primary")
    if submitted:
        def action():
            profile = UserProfile(age=age, height_cm=height, weight_kg=weight, activity=activity, energy_basis=energy_basis, goal=goal, diet=diet,
                                  allergies=[item.strip() for item in allergies.split(",") if item.strip()], dislikes=[item.strip() for item in dislikes.split(",") if item.strip()],
                                  health_notes=health_notes, pregnant_or_breastfeeding=pregnant_or_breastfeeding)
            return build_meal_plan(MealPlanRequest(profile=profile, period=period, manual_calories=calories if energy_basis == "manual" else None))
        run_action(action, "plan_result")
    if result := st.session_state.get("plan_result"):
        st.subheader(result.profile_summary)
        st.caption(f"Target: {result.target.calories} kcal · Protein {result.target.protein} g · Carbs {result.target.carbs} g · Fat {result.target.fat} g")
        for day in result.days:
            with st.expander(f"{day.day} · {day.totals.calories} estimated kcal", expanded=result.period == "daily"):
                st.caption(f"Protein {day.totals.protein} g · Carbs {day.totals.carbs} g · Fat {day.totals.fat} g")
                for meal in day.meals:
                    st.write(f"**{meal.slot}: {meal.name}** · {meal.macros.calories} kcal · {meal.portion}")
                    st.caption(f"{meal.description} Ingredients: {', '.join(meal.ingredients)}")
                for option in result.alternatives:
                    if option.day == day.day:
                        st.info(f"Swap for {option.replaces}: {option.meal.name} ({option.meal.macros.calories} kcal)")
        st.write(result.coach_note)
        st.caption(result.target_method + ". " + " ".join(result.cautions))
