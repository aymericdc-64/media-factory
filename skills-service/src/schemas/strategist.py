"""Pydantic models for the Strategist agent."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


# === read_content_catalog ===

class ReadContentCatalogRequest(BaseModel):
    status: Literal["Idea", "Validated", "À produire", "In Production", "Published", "Archived"] = "À produire"
    min_days_since_publish: int = Field(default=30, ge=0)
    limit: int = Field(default=20, ge=1, le=100)


class ConceptItem(BaseModel):
    page_id: str
    concept_id: int | None = None
    concept: str
    hook: str | None = None
    logline: str | None = None
    tags: list[str] = []
    status: str | None = None
    source: str | None = None
    difficulty: str | None = None
    last_published: str | None = None
    re_promote_score: float | None = None
    notes: str | None = None


class ReadContentCatalogResponse(BaseModel):
    concepts: list[ConceptItem]
    total: int


# === read_performance_tracker ===

class ReadPerformanceTrackerRequest(BaseModel):
    window_days: int = Field(default=90, ge=1, le=365)
    snapshot: Literal["D+1", "D+7", "D+30", "Final"] | None = None
    limit: int = 50


class PerformanceItem(BaseModel):
    page_id: str
    post_id: int | None
    post: str | None
    platform: str | None
    publish_date: str | None
    snapshot: str | None
    views: float | None
    likes: float | None
    comments: float | None
    shares: float | None
    saves: float | None
    follows_gained: float | None
    engagement_rate: float | None
    watch_time_sec: float | None
    verdict: str | None
    post_url: str | None


class ReadPerformanceTrackerResponse(BaseModel):
    items: list[PerformanceItem]
    total: int


# === read_content_themes ===

class ReadContentThemesRequest(BaseModel):
    status: Literal["Active", "Experimental", "Retired"] = "Active"


class ThemeItem(BaseModel):
    page_id: str
    theme: str
    code: str | None
    description: str | None
    tone: str | None
    visual_codes: str | None
    color: str | None
    status: str | None


class ReadContentThemesResponse(BaseModel):
    themes: list[ThemeItem]


# === read_bible_creative (rich text from page) ===

class ReadBibleCreativeRequest(BaseModel):
    page_id: str = Field(description="Notion page ID for the Bible créative page")


class ReadBibleCreativeResponse(BaseModel):
    page_id: str
    plain_text: str


# === write_brief_to_pipeline ===

class WriteBriefRequest(BaseModel):
    title: str
    brief: str
    script: str
    linked_agent: Literal["Agent Strategist", "Agent Producer", "Agent Scorer", "Agent Publisher"] = "Agent Strategist"


class WriteBriefResponse(BaseModel):
    page_id: str
    prod_id: int | None
    status: str
