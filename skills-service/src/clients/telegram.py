"""Telegram bot client — sends notifications + receives approvals via inline keyboard."""
from __future__ import annotations

import httpx

from src.config import settings
from src.logging_config import get_logger

log = get_logger(__name__)


class TelegramClient:
    def __init__(self) -> None:
        self._base = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"

    async def send_message(
        self,
        text: str,
        chat_id: str | None = None,
        reply_markup: dict | None = None,
        parse_mode: str = "Markdown",
    ) -> dict:
        if not settings.TELEGRAM_BOT_TOKEN:
            raise RuntimeError("telegram not configured")

        payload = {
            "chat_id": chat_id or settings.TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": parse_mode,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup

        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.post(f"{self._base}/sendMessage", json=payload)
            r.raise_for_status()
            return r.json()

    async def send_video_with_buttons(
        self,
        video_url: str,
        caption: str,
        prod_id: str,
        chat_id: str | None = None,
    ) -> dict:
        if not settings.TELEGRAM_BOT_TOKEN:
            raise RuntimeError("telegram not configured")

        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "Approve", "callback_data": f"approve_PROD-{prod_id}"},
                    {"text": "Reject", "callback_data": f"reject_PROD-{prod_id}"},
                ]
            ]
        }
        payload = {
            "chat_id": chat_id or settings.TELEGRAM_CHAT_ID,
            "video": video_url,
            "caption": caption[:1024],
            "parse_mode": "Markdown",
            "reply_markup": keyboard,
        }
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.post(f"{self._base}/sendVideo", json=payload)
            r.raise_for_status()
            return r.json()


_telegram_client: TelegramClient | None = None


def telegram_client() -> TelegramClient:
    global _telegram_client
    if _telegram_client is None:
        _telegram_client = TelegramClient()
    return _telegram_client
