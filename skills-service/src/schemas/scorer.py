"""Pydantic models for the Scorer agent."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ReadProductionPipelineRequest(BaseModel):
    status: Literal["Briefed", "Produced", "Scored", "Approved", "Rejected", "Published", "Re-promote"] = "Produced"
    limit: int = 10


class PipelineRowItem(BaseModel):
    page_id: str
    prod_id: int | None
    title: str
    brief: str | None
    script: str | None
    final_asset_url: str | None
    status: str | None


class ReadProductionPipelineResponse(BaseModel):
    rows: list[PipelineRowItem]
    total: int


class ScoreVideoRequest(BaseModel):
    page_id: str
    final_asset_url: str
    brief: str
    bible_context: str = Field(default="", description="Excerpt from the Bible créative for coherence check")


class ScoreVideoResponse(BaseModel):
    page_id: str
    score: float = Field(ge=0, le=10)
    rationale: str
    caption_fr: str
    caption_en: str
    hashtags: str


class WriteCaptionScoreRequest(BaseModel):
    page_id: str
    score: float
    caption_fr: str
    caption_en: str
    hashtags: str


class WriteCaptionScoreResponse(BaseModel):
    page_id: str
    status: str
