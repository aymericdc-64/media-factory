"""Routes for the Strategist agent."""
from __future__ import annotations

from fastapi import APIRouter

from src.schemas.strategist import (
    ReadBibleCreativeRequest,
    ReadBibleCreativeResponse,
    ReadContentCatalogRequest,
    ReadContentCatalogResponse,
    ReadContentThemesRequest,
    ReadContentThemesResponse,
    ReadPerformanceTrackerRequest,
    ReadPerformanceTrackerResponse,
    WriteBriefRequest,
    WriteBriefResponse,
)
from src.skills import strategist as sk

router = APIRouter()


@router.post("/read_content_catalog", response_model=ReadContentCatalogResponse)
async def read_content_catalog(req: ReadContentCatalogRequest) -> ReadContentCatalogResponse:
    return await sk.read_content_catalog(req)


@router.post("/read_performance_tracker", response_model=ReadPerformanceTrackerResponse)
async def read_performance_tracker(req: ReadPerformanceTrackerRequest) -> ReadPerformanceTrackerResponse:
    return await sk.read_performance_tracker(req)


@router.post("/read_content_themes", response_model=ReadContentThemesResponse)
async def read_content_themes(req: ReadContentThemesRequest) -> ReadContentThemesResponse:
    return await sk.read_content_themes(req)


@router.post("/read_bible_creative", response_model=ReadBibleCreativeResponse)
async def read_bible_creative(req: ReadBibleCreativeRequest) -> ReadBibleCreativeResponse:
    return await sk.read_bible_creative(req)


@router.post("/write_brief_to_pipeline", response_model=WriteBriefResponse)
async def write_brief_to_pipeline(req: WriteBriefRequest) -> WriteBriefResponse:
    return await sk.write_brief_to_pipeline(req)
