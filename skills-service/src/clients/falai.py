"""fal.ai async client — image (Flux Pro) and video (Kling) generation.

Doc : https://fal.ai/docs
fal.ai uses an async job pattern: submit → poll → fetch result.
"""
from __future__ import annotations

import asyncio
from typing import Any

import httpx

from src.config import settings
from src.logging_config import get_logger

log = get_logger(__name__)

FALAI_API_BASE = "https://queue.fal.run"


class FalAIError(Exception):
    pass


class FalAIClient:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            headers={"Authorization": f"Key {settings.FALAI_API_KEY}"},
            timeout=settings.HTTP_TIMEOUT_LONG,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def submit(self, model: str, payload: dict[str, Any]) -> str:
        """Submit a job and return the request_id."""
        url = f"{FALAI_API_BASE}/{model}"
        r = await self._client.post(url, json=payload)
        if r.status_code >= 400:
            raise FalAIError(f"fal.ai submit failed: {r.status_code} {r.text[:300]}")
        return r.json()["request_id"]

    async def poll(self, model: str, request_id: str, max_wait_s: int = 300) -> dict[str, Any]:
        """Poll until status==COMPLETED or timeout."""
        status_url = f"{FALAI_API_BASE}/{model}/requests/{request_id}/status"
        result_url = f"{FALAI_API_BASE}/{model}/requests/{request_id}"
        elapsed = 0
        backoff = 2
        while elapsed < max_wait_s:
            r = await self._client.get(status_url)
            status = r.json().get("status")
            if status == "COMPLETED":
                final = await self._client.get(result_url)
                return final.json()
            if status in ("FAILED", "ERROR"):
                raise FalAIError(f"fal.ai job failed: {r.json()}")
            await asyncio.sleep(backoff)
            elapsed += backoff
            backoff = min(backoff * 1.5, 10)
        raise FalAIError(f"fal.ai job timeout after {max_wait_s}s")

    async def run(self, model: str, payload: dict[str, Any], max_wait_s: int = 300) -> dict[str, Any]:
        """Submit + poll convenience wrapper."""
        rid = await self.submit(model, payload)
        log.info("falai_submitted", model=model, request_id=rid)
        return await self.poll(model, rid, max_wait_s=max_wait_s)

    # ---- high-level skills ----

    async def generate_image(self, prompt: str, aspect_ratio: str = "9:16") -> dict[str, Any]:
        result = await self.run(
            settings.FALAI_IMAGE_MODEL,
            {
                "prompt": prompt,
                "aspect_ratio": aspect_ratio,
                "num_images": 1,
                "output_format": "png",
                "safety_tolerance": "5",
            },
            max_wait_s=120,
        )
        img = (result.get("images") or [{}])[0]
        return {"url": img.get("url"), "width": img.get("width"), "height": img.get("height")}

    async def animate_image_to_video(
        self,
        image_url: str,
        prompt: str = "",
        duration_seconds: int = 5,
    ) -> dict[str, Any]:
        result = await self.run(
            settings.FALAI_VIDEO_MODEL,
            {
                "image_url": image_url,
                "prompt": prompt,
                "duration": str(duration_seconds),
                "aspect_ratio": "9:16",
            },
            max_wait_s=600,
        )
        video = result.get("video") or {}
        return {"url": video.get("url"), "duration": duration_seconds}


_falai_client: FalAIClient | None = None


def falai_client() -> FalAIClient:
    global _falai_client
    if _falai_client is None:
        _falai_client = FalAIClient()
    return _falai_client
