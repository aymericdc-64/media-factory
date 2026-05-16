"""Creatomate async client — template-based video/image composition.

Doc : https://creatomate.com/docs/api/rest-api/introduction
"""
from __future__ import annotations

import asyncio
from typing import Any

import httpx

from src.config import settings
from src.logging_config import get_logger

log = get_logger(__name__)

CREATOMATE_API_BASE = "https://api.creatomate.com/v1"


class CreatomateError(Exception):
    pass


class CreatomateClient:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=CREATOMATE_API_BASE,
            headers={
                "Authorization": f"Bearer {settings.CREATOMATE_API_KEY}",
                "Content-Type": "application/json",
            },
            timeout=settings.HTTP_TIMEOUT_LONG,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def render(
        self,
        template_id: str,
        modifications: dict[str, Any],
        output_format: str = "mp4",
        max_wait_s: int = 300,
    ) -> dict[str, Any]:
        """POST /renders and poll until the render finishes."""
        payload = {
            "template_id": template_id,
            "modifications": modifications,
            "output_format": output_format,
        }
        r = await self._client.post("/renders", json=payload)
        if r.status_code >= 400:
            raise CreatomateError(f"creatomate render failed: {r.status_code} {r.text[:300]}")
        # Creatomate returns a list of renders (one per output)
        renders = r.json() if isinstance(r.json(), list) else [r.json()]
        render_id = renders[0]["id"]
        log.info("creatomate_submitted", render_id=render_id, template=template_id)
        return await self._poll(render_id, max_wait_s)

    async def _poll(self, render_id: str, max_wait_s: int) -> dict[str, Any]:
        elapsed, backoff = 0, 2
        while elapsed < max_wait_s:
            r = await self._client.get(f"/renders/{render_id}")
            data = r.json()
            status = data.get("status")
            if status == "succeeded":
                return {"url": data.get("url"), "render_id": render_id, "raw": data}
            if status in ("failed", "cancelled"):
                raise CreatomateError(f"creatomate render {render_id} status={status}")
            await asyncio.sleep(backoff)
            elapsed += backoff
            backoff = min(backoff * 1.5, 10)
        raise CreatomateError(f"creatomate render {render_id} timeout after {max_wait_s}s")


_creatomate_client: CreatomateClient | None = None


def creatomate_client() -> CreatomateClient:
    global _creatomate_client
    if _creatomate_client is None:
        _creatomate_client = CreatomateClient()
    return _creatomate_client
