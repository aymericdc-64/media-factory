"""Pydantic models for the Producer agent."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class GenerateImageRequest(BaseModel):
    prompt: str
    aspect_ratio: Literal["9:16", "1:1", "16:9", "4:5"] = "9:16"
    prod_id: str | None = None


class GenerateImageResponse(BaseModel):
    url: str
    width: int | None = None
    height: int | None = None


class ComposeCardRequest(BaseModel):
    image_url: str
    title: str
    subtitle: str | None = None
    hp: str | None = None
    energy_type: str | None = None
    template_id: str | None = None  # falls back to env default
    extras: dict = Field(default_factory=dict, description="Free-form modifications to inject")


class ComposeCardResponse(BaseModel):
    url: str
    render_id: str


class AnimateVideoRequest(BaseModel):
    image_url: str
    prompt: str = ""
    duration_seconds: int = Field(default=5, ge=2, le=10)


class AnimateVideoResponse(BaseModel):
    url: str
    duration: int


class GetAudioRequest(BaseModel):
    mood: str
    max_duration_s: int = 30


class GetAudioResponse(BaseModel):
    url: str
    title: str
    license_id: str


class ComposeFinalVideoRequest(BaseModel):
    card_image_url: str
    animation_url: str
    audio_url: str
    caption: str | None = None
    watermark_text: str | None = None
    template_id: str | None = None
    extras: dict = Field(default_factory=dict)


class ComposeFinalVideoResponse(BaseModel):
    url: str
    render_id: str


class UploadAssetRequest(BaseModel):
    source_url: str
    key: str = Field(description="Destination object key, ex: 'videos/PROD-123.mp4'")
    content_type: str = "video/mp4"


class UploadAssetResponse(BaseModel):
    url: str


class UpdatePipelineStatusRequest(BaseModel):
    page_id: str
    status: Literal["Briefed", "Produced", "Scored", "Approved", "Rejected", "Published", "Re-promote"]
    final_asset_url: str | None = None
    error: str | None = None
    score: float | None = None
    caption_fr: str | None = None
    caption_en: str | None = None
    hashtags: str | None = None
    scheduled_publish: str | None = None  # ISO 8601


class UpdatePipelineStatusResponse(BaseModel):
    page_id: str
    status: str
