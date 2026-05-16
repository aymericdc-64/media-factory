"""Pydantic models for the Publisher agent."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class ReadPipelineApprovedRequest(BaseModel):
    limit: int = 20


class ApprovedRowItem(BaseModel):
    page_id: str
    prod_id: int | None
    title: str
    final_asset_url: str | None
    caption_fr: str | None
    caption_en: str | None
    hashtags: str | None
    scheduled_publish: str | None


class ReadPipelineApprovedResponse(BaseModel):
    rows: list[ApprovedRowItem]
    total: int


class ReadChannelsActiveRequest(BaseModel):
    pass


class ChannelItem(BaseModel):
    page_id: str
    channel: str
    platform: str | None
    handle: str | None
    formats: list[str]
    posting_frequency: str | None
    best_slot_utc: str | None
    status: str | None


class ReadChannelsActiveResponse(BaseModel):
    channels: list[ChannelItem]


class PostRequest(BaseModel):
    page_id: str
    video_url: str
    caption: str
    title: str | None = None


class PostResponse(BaseModel):
    page_id: str
    platform: str
    post_id: str
    post_url: str


class CreatePerformanceRowRequest(BaseModel):
    pipeline_page_id: str
    title: str
    platform: Literal["Instagram", "TikTok", "YouTube Shorts", "Threads", "X", "Pinterest", "LinkedIn"]
    post_id: str
    post_url: str
    publish_date: str  # ISO 8601


class CreatePerformanceRowResponse(BaseModel):
    performance_page_id: str
