import base64
import json
import os

from fastapi import HTTPException
from openai import OpenAI, OpenAIError
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError

load_dotenv()


def provider_name() -> str:
    selected = os.getenv("FOODVERSE_AI_PROVIDER", "").lower()
    if selected in {"openai", "groq"}:
        return selected
    return "openai" if os.getenv("OPENAI_API_KEY") else "groq"


def model_ready() -> bool:
    return bool(os.getenv("GROQ_API_KEY" if provider_name() == "groq" else "OPENAI_API_KEY"))


def model_client() -> OpenAI:
    if provider_name() == "groq":
        return OpenAI(api_key=os.getenv("GROQ_API_KEY"), base_url="https://api.groq.com/openai/v1", timeout=90)
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"), timeout=90)


def vision_model() -> str:
    if provider_name() == "groq":
        return os.getenv("GROQ_VISION_MODEL", "qwen/qwen3.8-27b")
    return os.getenv("OPENAI_VISION_MODEL", "gpt-4.1-mini")


def transcribe_audio(content: bytes, filename: str, content_type: str) -> str:
    if not model_ready():
        raise HTTPException(status_code=503, detail="AI analysis is unavailable. Configure OPENAI_API_KEY or GROQ_API_KEY on the API server.")
    model = "whisper-large-v3-turbo" if provider_name() == "groq" else "gpt-4o-mini-transcribe"
    try:
        return model_client().audio.transcriptions.create(model=model, file=(filename, content, content_type)).text
    except OpenAIError as exc:
        raise HTTPException(status_code=502, detail=f"Audio transcription failed: {str(exc)[:180]}") from exc


def validate_output(schema: type[BaseModel], value: dict):
    try:
        return schema.model_validate(value)
    except ValidationError as exc:
        raise HTTPException(status_code=502, detail="AI response did not match the expected analysis format.") from exc


def image_part(content: bytes, content_type: str) -> dict:
    encoded = base64.b64encode(content).decode("ascii")
    return {"type": "input_image", "image_url": f"data:{content_type};base64,{encoded}", "detail": "high"}


def ask_json(instructions: str, parts: list[dict] | None = None, text: str = "") -> dict:
    if not model_ready():
        raise HTTPException(status_code=503, detail="AI analysis is unavailable. Configure OPENAI_API_KEY or GROQ_API_KEY on the API server.")
    try:
        response = model_client().responses.create(
            model=vision_model(),
            instructions=instructions,
            input=[{"role": "user", "content": [{"type": "input_text", "text": f"Respond with a JSON object. {text}".strip()}] + (parts or [])}],
            text={"format": {"type": "json_object"}},
        )
        return json.loads(response.output_text)
    except (OpenAIError, ValueError, KeyError) as exc:
        raise HTTPException(status_code=502, detail=f"AI analysis failed: {str(exc)[:180]}") from exc
