"""Routes for the Scorer agent."""
from __future__ import annotations

from fastapi import APIRouter

from src.schemas.scorer import (
    ReadProductionPipelineRequest,
    ReadProductionPipelineResponse,
    ScoreVideoRequest,
    ScoreVideoResponse,
    WriteCaptionScoreRequest,
    WriteCaptionScoreResponse,
)
from src.skills import scorer as sk

router = APIRouter()


@router.post("/read_production_pipeline", response_model=ReadProductionPipelineResponse)
async def read_production_pipeline(req: ReadProductionPipelineRequest):
    return await sk.read_production_pipeline(req)


@router.post("/score_video", response_model=ScoreVideoResponse)
async def score_video(req: ScoreVideoRequest):
    return await sk.score_video(req)


@router.post("/write_caption_score", response_model=WriteCaptionScoreResponse)
async def write_caption_score(req: WriteCaptionScoreRequest):
    return await sk.write_caption_score(req)
