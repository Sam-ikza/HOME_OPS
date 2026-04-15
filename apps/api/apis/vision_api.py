"""Vision/OCR extraction for appliance onboarding."""

from __future__ import annotations

from datetime import date, datetime
from functools import lru_cache
import os
import json
from pathlib import Path
import re

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

_GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if _GOOGLE_API_KEY:
    genai.configure(api_key=_GOOGLE_API_KEY)
    _model = genai.GenerativeModel("gemini-1.5-flash")
else:
    _model = None

_PROMPT = (
    "You are an appliance recognition assistant. "
    "Look at this image and extract appliance purchase/sticker details. "
    'Return ONLY valid JSON with keys: "brand", "model_number", "serial_number", "purchase_date", "confidence". '
    'Example: {"brand":"Samsung","model_number":"WF45R6100AW","serial_number":"SN12345","purchase_date":"2025-02-11","confidence":0.92}'
)

_SCENE_PROMPT_TEMPLATE = """
You are an appliance visual diagnosis assistant.
Analyze the raw image and infer what is visibly wrong, including power/connectivity issues and display error codes.

User context (optional): {issue_text}

Return ONLY valid JSON with these keys:
- appliance_type: string|null
- brand: string
- model_number: string
- error_code: string|null
- display_text: string|null
- likely_issue: string
- visible_signals: string[]
- risk_flags: string[]
- summary: string
- confidence: number between 0 and 1

Rules:
- If something is not clearly visible, set it to null or "Unknown" and lower confidence.
- Include practical visual findings in visible_signals (e.g., plug_unplugged, switch_off, breaker_tripped, leak_visible, burn_mark_visible, loose_cable, frost_buildup).
- risk_flags should include only serious safety risks if clearly visible (e.g., sparks_visible, burn_damage, exposed_wire, leak_near_electrical, smoke_mark).
- For error_code, prefer compact formats like E03, F21, LE when visible.
""".strip()

_DEMO_MANIFEST_PATH = Path(__file__).resolve().parents[1] / "data" / "demo_scan" / "demo_manifest.json"


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    value = value.strip()
    for pattern in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
        try:
            if pattern == "%Y-%m-%d":
                return date.fromisoformat(value)
            return datetime.strptime(value, pattern).date()
        except Exception:
            continue
    return None


def _safe_parse_json(text: str) -> dict:
    raw = (text or "").strip()
    raw = raw.strip("`")
    raw = raw.replace("json", "", 1).strip() if raw.lower().startswith("json") else raw
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text or "", re.DOTALL)
        if not match:
            return {}
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return {}


def _normalize_payload(payload: dict, raw_response: str | None = None) -> dict:
    confidence = payload.get("confidence", 0.0)
    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        confidence = 0.0
    confidence = max(0.0, min(1.0, confidence))

    brand = str(payload.get("brand") or "Unknown").strip()
    model_number = str(payload.get("model_number") or payload.get("model") or "Unknown").strip()
    serial_number = payload.get("serial_number")
    purchase = _parse_date(str(payload.get("purchase_date") or ""))

    needs_confirmation = confidence < 0.7 or brand == "Unknown" or model_number == "Unknown"

    return {
        "brand": brand,
        "model_number": model_number,
        "serial_number": serial_number,
        "purchase_date": purchase,
        "confidence": confidence,
        "needs_confirmation": needs_confirmation,
        "raw_response": raw_response,
    }


def _normalize_error_code(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = re.sub(r"[^A-Za-z0-9-]", "", str(value).upper())
    if not cleaned:
        return None
    # Reject unrealistic long codes to reduce hallucinated OCR output.
    if len(cleaned) > 12:
        return None
    return cleaned


def _normalize_scene_payload(payload: dict, raw_response: str | None = None) -> dict:
    confidence = payload.get("confidence", 0.0)
    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        confidence = 0.0
    confidence = max(0.0, min(1.0, confidence))

    brand = str(payload.get("brand") or "Unknown").strip()
    model_number = str(payload.get("model_number") or payload.get("model") or "Unknown").strip()
    appliance_type = payload.get("appliance_type")
    display_text = payload.get("display_text")
    likely_issue = str(payload.get("likely_issue") or "Unable to determine from image.").strip()
    summary = payload.get("summary")

    visible_signals = payload.get("visible_signals") or []
    if not isinstance(visible_signals, list):
        visible_signals = [str(visible_signals)]
    visible_signals = [str(item).strip() for item in visible_signals if str(item).strip()][:12]

    risk_flags = payload.get("risk_flags") or []
    if not isinstance(risk_flags, list):
        risk_flags = [str(risk_flags)]
    risk_flags = [str(item).strip() for item in risk_flags if str(item).strip()][:8]

    error_code = _normalize_error_code(payload.get("error_code"))
    needs_confirmation = confidence < 0.7 or (brand == "Unknown" and model_number == "Unknown" and not error_code)
    source = str(payload.get("source") or "gemini").strip() or "gemini"

    return {
        "appliance_type": str(appliance_type).strip() if appliance_type else None,
        "brand": brand,
        "model_number": model_number,
        "error_code": error_code,
        "display_text": str(display_text).strip() if display_text else None,
        "likely_issue": likely_issue,
        "visible_signals": visible_signals,
        "risk_flags": risk_flags,
        "summary": str(summary).strip() if summary else None,
        "confidence": confidence,
        "needs_confirmation": needs_confirmation,
        "source": source,
        "raw_response": raw_response,
    }


def _normalize_demo_filename(filename: str | None) -> str:
    if not filename:
        return ""
    stem = Path(filename).stem.lower()
    return re.sub(r"[^a-z0-9]+", "-", stem).strip("-")


@lru_cache(maxsize=1)
def _load_demo_scene_manifest() -> dict[str, dict]:
    if not _DEMO_MANIFEST_PATH.exists():
        return {}

    try:
        payload = json.loads(_DEMO_MANIFEST_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}

    entries = payload.get("scenarios") if isinstance(payload, dict) else None
    if not isinstance(entries, list):
        return {}

    manifest: dict[str, dict] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        filename = entry.get("filename")
        normalized_name = _normalize_demo_filename(str(filename) if filename else None)
        if not normalized_name:
            continue
        manifest[normalized_name] = entry
    return manifest


def match_demo_appliance_scene(filename: str | None) -> dict | None:
    normalized_name = _normalize_demo_filename(filename)
    if not normalized_name:
        return None

    entry = _load_demo_scene_manifest().get(normalized_name)
    if not entry:
        return None

    payload = dict(entry)
    payload["source"] = "demo_manifest"
    return _normalize_scene_payload(payload, raw_response=f"demo_manifest:{entry.get('filename', filename or '')}")


def extract_appliance_details(image_bytes: bytes, mime_type: str = "image/jpeg") -> dict:
    """
    Send an appliance image to Gemini and extract brand/model information.

    Args:
        image_bytes: Raw image bytes (JPEG, PNG, etc.)
        mime_type:   MIME type of the image, e.g. "image/jpeg".

    Returns:
        dict with at least "brand" and "model" keys.
    """
    if not mime_type.startswith("image/"):
        return _normalize_payload(
            {
                "brand": "Unknown",
                "model_number": "Unknown",
                "serial_number": None,
                "purchase_date": None,
                "confidence": 0.0,
            },
            raw_response=f"Unsupported MIME type: {mime_type}",
        )

    if not _model:
        return _normalize_payload(
            {
                "brand": "Unknown",
                "model_number": "Unknown",
                "serial_number": None,
                "purchase_date": None,
                "confidence": 0.0,
            },
            raw_response="Google API key not configured",
        )

    try:
        image_part = {"mime_type": mime_type, "data": image_bytes}
        response = _model.generate_content([_PROMPT, image_part])
        raw_response = getattr(response, "text", "")
        parsed = _safe_parse_json(raw_response)
        return _normalize_payload(parsed, raw_response=raw_response)
    except Exception as exc:
        return _normalize_payload(
            {
                "brand": "Unknown",
                "model_number": "Unknown",
                "serial_number": None,
                "purchase_date": None,
                "confidence": 0.0,
            },
            raw_response=f"Vision provider error: {exc}",
        )


def analyze_appliance_scene(
    image_bytes: bytes,
    mime_type: str = "image/jpeg",
    issue_text: str | None = None,
) -> dict:
    """
    Analyze a raw image for visible appliance faults, error codes, and scene clues.

    Returns a normalized dict safe for API responses and downstream LLM handoff.
    """
    if not mime_type.startswith("image/"):
        return _normalize_scene_payload(
            {
                "brand": "Unknown",
                "model_number": "Unknown",
                "likely_issue": "Unsupported image type.",
                "visible_signals": [],
                "risk_flags": [],
                "confidence": 0.0,
            },
            raw_response=f"Unsupported MIME type: {mime_type}",
        )

    if not _model:
        return _normalize_scene_payload(
            {
                "brand": "Unknown",
                "model_number": "Unknown",
                "likely_issue": "Vision model unavailable.",
                "visible_signals": [],
                "risk_flags": [],
                "confidence": 0.0,
            },
            raw_response="Google API key not configured",
        )

    prompt = _SCENE_PROMPT_TEMPLATE.format(issue_text=(issue_text or "none provided"))

    try:
        image_part = {"mime_type": mime_type, "data": image_bytes}
        response = _model.generate_content([prompt, image_part])
        raw_response = getattr(response, "text", "")
        parsed = _safe_parse_json(raw_response)
        return _normalize_scene_payload(parsed, raw_response=raw_response)
    except Exception as exc:
        return _normalize_scene_payload(
            {
                "brand": "Unknown",
                "model_number": "Unknown",
                "likely_issue": "Could not analyze image.",
                "visible_signals": [],
                "risk_flags": [],
                "confidence": 0.0,
            },
            raw_response=f"Vision provider error: {exc}",
        )


def scan_appliance(image_bytes: bytes, mime_type: str = "image/jpeg") -> dict:
    """Backward-compatible alias for older endpoints."""
    data = extract_appliance_details(image_bytes=image_bytes, mime_type=mime_type)
    return {
        "brand": data["brand"],
        "model": data["model_number"],
        "confidence": data["confidence"],
        "source": "gemini",
    }
