"""Pydantic models for the Analyst agent."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class FetchMetricsRequest(BaseModel):
    platform: Literal["Instagram", "TikTok", "YouTube Shorts", "Threads", "X", "Pinterest", "LinkedIn"]
    post_id: str


class FetchMetricsResponse(BaseModel):
    views: float
    likes: float
    comments: float
    shares: float
    saves: float = 0
    follows_gained: float = 0
    watch_time_sec: float = 0


class ComputeEngagementRequest(BaseModel):
    views: float
    likes: float
    comments: float
    shares: float
    saves: float = 0


class ComputeEngagementResponse(BaseModel):
    engagement_rate: float


class ComputeVerdictRequest(BaseModel):
    views: float
    engagement_rate: float
    benchmarks: dict  # {"views": {"p25":..., "p50":..., "p75":..., "p90":...}, "er": {...}}


class ComputeVerdictResponse(BaseModel):
    verdict: Literal["Banger", "Solid", "Mid", "Flop", "TBD"]
    rationale: str


class WriteAnalystNotesRequest(BaseModel):
    metrics: dict
    verdict: str
    context: str = ""


class WriteAnalystNotesResponse(BaseModel):
    notes: str


class UpdatePerformanceRequest(BaseModel):
    performance_page_id: str
    views: float
    likes: float
    comments: float
    shares: float
    saves: float = 0
    follows_gained: float = 0
    watch_time_sec: float = 0
    engagement_rate: float
    verdict: str
    notes: str


class UpdatePerformanceResponse(BaseModel):
    page_id: str


class ReadAnalystSnapshotRequest(BaseModel):
    snapshot: Literal["D+1", "D+7", "D+30"]


class SnapshotRowItem(BaseModel):
    performance_page_id: str
    post_id: int | None
    post: str
    platform: str | None
    publish_date: str | None
    post_url: str | None


class ReadAnalystSnapshotResponse(BaseModel):
    rows: list[SnapshotRowItem]
