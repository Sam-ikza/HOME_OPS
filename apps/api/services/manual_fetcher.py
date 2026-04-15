from __future__ import annotations

import logging
from urllib.parse import quote_plus

import httpx

logger = logging.getLogger(__name__)


async def fetch_manual_url(brand: str, model_number: str) -> str | None:
    """Best-effort manual discovery using iFixit search style endpoint.

    Returns a URL when found, otherwise None.
    """
    query = quote_plus(f"{brand} {model_number} manual")
    search_url = f"https://www.ifixit.com/Search?query={query}"

    try:
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.get(search_url)
            if response.status_code == 200:
                return str(response.url)
    except Exception as exc:  # pragma: no cover - network dependent
        logger.warning("manual discovery failed: %s", exc)

    return None
