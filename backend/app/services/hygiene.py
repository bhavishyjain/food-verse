import subprocess
import tempfile
from pathlib import Path

import imageio_ffmpeg

from ..models import HygieneAnalysis
from .model_provider import ask_json, image_part, provider_name, validate_output


PROMPT = """Review these chronological kitchen video frames for visible hygiene indicators. Return JSON only with duration, checks (array of exactly four objects with label, status Pass/Review/Not visible, and score null), alerts (array with approximate frame time and specific message), and limitations (array). Use these exact check labels: Glove usage, Hair restraint, Safe food handling, Surface cleanliness. Pass requires clear visible evidence of compliance; if a person, action, or surface is obscured choose Not visible. Flag only observed concerns, not hypothetical violations. Do not estimate a score; the application calculates it. This is a screening aid, not a formal inspection."""


WEIGHTS = {"Glove usage": 25, "Hair restraint": 25, "Safe food handling": 30, "Surface cleanliness": 20}


def score_observations(data: dict, frames_analyzed: int) -> HygieneAnalysis:
    checks_by_label = {check.get("label"): check for check in data.get("checks", []) if isinstance(check, dict)}
    checks = []
    visible_weight = 0
    passed_weight = 0
    for label, weight in WEIGHTS.items():
        raw = checks_by_label.get(label, {})
        status = raw.get("status") if raw.get("status") in {"Pass", "Review"} else "Not visible"
        if status != "Not visible":
            visible_weight += weight
            if status == "Pass":
                passed_weight += weight
        checks.append({"label": label, "status": status, "score": 100 if status == "Pass" else 0 if status == "Review" else None})
    score = round(100 * passed_weight / visible_weight) if visible_weight else None
    status = "Insufficient visible evidence" if score is None else "Needs review" if score < 80 else "Visible checks passed"
    return validate_output(HygieneAnalysis, {
        "score": score, "status": status, "duration": data.get("duration", "Unknown"),
        "frames_analyzed": frames_analyzed, "checks": checks,
        "alerts": data.get("alerts", []),
        "limitations": list(data.get("limitations", [])) + ["Score excludes checks that were not visible. Sampled frames cannot verify continuous compliance."],
    })


def analyze_hygiene(content: bytes, suffix: str) -> HygieneAnalysis:
    with tempfile.TemporaryDirectory() as folder:
        video = Path(folder) / f"input{suffix}"
        video.write_bytes(content)
        output = Path(folder) / "frame-%02d.jpg"
        frame_limit = 5 if provider_name() == "groq" else 8
        command = [imageio_ffmpeg.get_ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-i", str(video), "-vf", r"select=isnan(prev_selected_t)+gte(t-prev_selected_t\,30),scale=768:-2", "-fps_mode", "vfr", "-frames:v", str(frame_limit), "-pix_fmt", "yuvj420p", str(output)]
        try:
            subprocess.run(command, check=True, capture_output=True, timeout=45)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            raise ValueError("Could not decode the video. Upload a supported MP4, MOV, or WebM file.") from exc
        frames = sorted(Path(folder).glob("frame-*.jpg"))
        if not frames:
            raise ValueError("No readable video frames were found.")
        parts = []
        for index, frame in enumerate(frames):
            parts.append({"type": "input_text", "text": f"Approximate timestamp {index * 30} seconds"})
            parts.append(image_part(frame.read_bytes(), "image/jpeg"))
        result = ask_json(PROMPT, parts)
        return score_observations(result, len(frames))
