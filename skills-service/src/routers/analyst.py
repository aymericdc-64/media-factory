"""Routes for the Analyst agent."""
from __future__ import annotations

from fastapi import APIRouter

from src.schemas.analyst import (
    ComputeEngagementRequest,
    ComputeEngagementResponse,
    ComputeVerdictRequest,
    ComputeVerdictResponse,
    FetchMetricsRequest,
    FetchMetricsResponse,
    ReadAnalystSnapshotRequest,
    ReadAnalystSnapshotResponse,
    UpdatePerformanceRequest,
    UpdatePerformanceResponse,
    WriteAnalystNotesRequest,
    WriteAnalystNotesResponse,
)
from src.skills import analyst as sk

router = APIRouter()


@router.post("/fetch_metrics", response_model=FetchMetricsResponse)
async def fetch_metrics(req: FetchMetricsRequest):
    return await sk.fetch_metrics(req)


@router.post("/compute_engagement_rate", response_model=ComputeEngagementResponse)
async def compute_engagement_rate(req: ComputeEngagementRequest):
    return await sk.compute_engagement_rate(req)


@router.post("/compute_verdict", response_model=ComputeVerdictResponse)
async def compute_verdict(req: ComputeVerdictRequest):
    return await sk.compute_verdict(req)


@router.post("/write_analyst_notes", response_model=WriteAnalystNotesResponse)
async def write_analyst_notes(req: WriteAnalystNotesRequest):
    return await sk.write_analyst_notes(req)


@router.post("/update_performance", response_model=UpdatePerformanceResponse)
async def update_performance(req: UpdatePerformanceRequest):
    return await sk.update_performance(req)


@router.post("/read_snapshot", response_model=ReadAnalystSnapshotResponse)
async def read_snapshot(req: ReadAnalystSnapshotRequest):
    return await sk.read_snapshot(req)
