from __future__ import annotations

from datetime import datetime

from config import settings


def draft_pro_handoff(appliance: dict, issue_summary: str, city: str | None = None) -> dict:
    location = city or "your area"
    message = (
        f"Need licensed appliance repair support in {location}. "
        f"Appliance: {appliance.get('brand')} {appliance.get('model_number')} "
        f"(serial: {appliance.get('serial_number') or 'n/a'}). "
        f"Issue: {issue_summary}. Please provide earliest service window and quote."
    )
    return {
        "message": message,
        "created_at": datetime.utcnow().isoformat(),
    }


def build_affiliate_links(appliance: dict, part_query: str) -> dict:
    q = f"{appliance.get('brand', '')} {appliance.get('model_number', '')} {part_query}".strip().replace(" ", "+")

    if settings.rainforest_api_key:
        return {
            "provider": "rainforest",
            "query": q,
            "note": "Attach Rainforest API lookup in production path.",
        }

    # Free fallback path for hackathon demos.
    return {
        "provider": "fallback",
        "links": [
            f"https://www.amazon.com/s?k={q}",
            f"https://www.ebay.com/sch/i.html?_nkw={q}",
        ],
    }


def whatsapp_dispatch_preview(message: str, to_number: str) -> dict:
    if not (settings.twilio_account_sid and settings.twilio_auth_token and settings.twilio_whatsapp_from):
        return {
            "provider": "twilio",
            "status": "preview_only",
            "message": message,
            "to": to_number,
        }

    return {
        "provider": "twilio",
        "status": "ready",
        "message": message,
        "to": to_number,
    }
