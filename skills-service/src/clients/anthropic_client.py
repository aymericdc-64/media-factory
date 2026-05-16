"""Thin wrapper around the Anthropic SDK — async messages with optional vision input."""
from __future__ import annotations

from typing import Any

from anthropic import AsyncAnthropic

from src.config import settings
from src.logging_config import get_logger

log = get_logger(__name__)


class AnthropicClient:
    def __init__(self) -> None:
        self._client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def message(
        self,
        *,
        model: str,
        system: str,
        messages: list[dict[str, Any]],
        max_tokens: int = 2048,
        temperature: float = 0.7,
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Run a single non-streaming completion. Returns the parsed Message object as dict."""
        kwargs: dict[str, Any] = {
            "model": model,
            "system": system,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if tools:
            kwargs["tools"] = tools

        log.info("anthropic_request", model=model, msgs=len(messages))
        resp = await self._client.messages.create(**kwargs)
        return resp.model_dump()

    async def text_completion(
        self,
        *,
        model: str,
        system: str,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> str:
        """Convenience: send a single user message, return the concatenated text."""
        resp = await self.message(
            model=model,
            system=system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        chunks = [c["text"] for c in resp.get("content", []) if c.get("type") == "text"]
        return "".join(chunks).strip()

    async def vision_score(
        self,
        *,
        system: str,
        prompt: str,
        image_url: str,
        max_tokens: int = 512,
    ) -> str:
        """Send an image URL + prompt to Claude vision model, return the text answer."""
        resp = await self.message(
            model=settings.ANTHROPIC_MODEL_VISION,
            system=system,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "source": {"type": "url", "url": image_url}},
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
            max_tokens=max_tokens,
            temperature=0.3,
        )
        chunks = [c["text"] for c in resp.get("content", []) if c.get("type") == "text"]
        return "".join(chunks).strip()


_anthropic_client: AnthropicClient | None = None


def anthropic_client() -> AnthropicClient:
    global _anthropic_client
    if _anthropic_client is None:
        _anthropic_client = AnthropicClient()
    return _anthropic_client
