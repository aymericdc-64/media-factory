"""Centralized settings via pydantic-settings. Loaded once at startup."""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # --- Internal auth ---
    SKILLS_AUTH_SECRET: str

    # --- Anthropic ---
    ANTHROPIC_API_KEY: str
    ANTHROPIC_MODEL_STRATEGIST: str = "claude-opus-4-6"
    ANTHROPIC_MODEL_SCORER: str = "claude-haiku-4-5-20251001"
    ANTHROPIC_MODEL_ANALYST: str = "claude-haiku-4-5-20251001"
    ANTHROPIC_MODEL_VISION: str = "claude-sonnet-4-6"

    # --- Notion ---
    NOTION_API_KEY: str
    NOTION_DS_CONTENT_CATALOG: str
    NOTION_DS_PRODUCTION_PIPELINE: str
    NOTION_DS_PERFORMANCE_TRACKER: str
    NOTION_DS_CHANNELS: str
    NOTION_DS_CONTENT_THEMES: str
    NOTION_DS_ASSET_TEMPLATES: str
    NOTION_DS_PROMPTS_LIBRARY: str
    NOTION_DS_ARCHETYPES: str = ""

    # --- fal.ai ---
    FALAI_API_KEY: str = ""
    FALAI_IMAGE_MODEL: str = "fal-ai/flux-pro/v1.1"
    FALAI_VIDEO_MODEL: str = "fal-ai/kling-video/v2.5-turbo/image-to-video"

    # --- Creatomate ---
    CREATOMATE_API_KEY: str = ""
    CREATOMATE_TEMPLATE_CARD: str = ""
    CREATOMATE_TEMPLATE_VIDEO_FINAL: str = ""

    # --- Epidemic ---
    EPIDEMIC_API_KEY: str = ""

    # --- Cloudflare R2 ---
    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET: str = "factory-assets"
    R2_PUBLIC_URL_BASE: str = ""

    # --- Publishing ---
    INSTAGRAM_ACCESS_TOKEN: str = ""
    INSTAGRAM_BUSINESS_ACCOUNT_ID: str = ""
    TIKTOK_ACCESS_TOKEN: str = ""
    YOUTUBE_CLIENT_ID: str = ""
    YOUTUBE_CLIENT_SECRET: str = ""
    YOUTUBE_REFRESH_TOKEN: str = ""
    BUFFER_ACCESS_TOKEN: str = ""

    # --- Telegram ---
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""

    # --- Service ---
    LOG_LEVEL: str = "INFO"
    HTTP_TIMEOUT_DEFAULT: int = 30
    HTTP_TIMEOUT_LONG: int = 300


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


# Convenience module-level singleton
settings = get_settings()
