"""Epidemic Sound async client — fetch a track URL by tags / mood.

Note : Epidemic's public API is limited; this client is a thin wrapper that
falls back to a curated catalog if the API key is empty. In dev, override the
audio URL manually.
"""
from __future__ import annotations

import httpx

from src.config import settings
from src.logging_config import get_logger

log = get_logger(__name__)

EPIDEMIC_API_BASE = "https://api.epidemicsound.com/v1"


class EpidemicError(Exception):
    pass


class EpidemicClient:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=EPIDEMIC_API_BASE,
            headers={"Authorization": f"Bearer {settings.EPIDEMIC_API_KEY}"} if settings.EPIDEMIC_API_KEY else {},
            timeout=settings.HTTP_TIMEOUT_DEFAULT,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def search_track(self, mood: str, max_duration_s: int = 30) -> dict[str, str]:
        """Return {url, title, license_id} for one track matching mood."""
        if not settings.EPIDEMIC_API_KEY:
            log.warning("epidemic_no_key", mood=mood)
            return {
                "url": f"https://placeholder.audio/{mood.lower()}.mp3",
                "title": f"placeholder-{mood}",
                "license_id": "dev-placeholder",
            }

        r = await self._client.get(
            "/tracks/search",
            params={"mood": mood, "max_duration": max_duration_s, "limit": 1},
        )
        if r.status_code >= 400:
            raise EpidemicError(f"epidemic search failed: {r.status_code} {r.text[:200]}")
        results = r.json().get("results") or []
        if not results:
            raise EpidemicError(f"no track for mood={mood}")
        t = results[0]
        return {
            "url": t.get("download_url") or t.get("preview_url"),
            "title": t.get("title", ""),
            "license_id": t.get("id", ""),
        }


_epidemic_client: EpidemicClient | None = None


def epidemic_client() -> EpidemicClient:
    global _epidemic_client
    if _epidemic_client is None:
        _epidemic_client = EpidemicClient()
    return _epidemic_client
