"""Routes for the Publisher agent."""
from __future__ import annotations

from fastapi import APIRouter

from src.schemas.publisher import (
    CreatePerformanceRowRequest,
    CreatePerformanceRowResponse,
    PostRequest,
    PostResponse,
    ReadChannelsActiveRequest,
    ReadChannelsActiveResponse,
    ReadPipelineApprovedRequest,
    ReadPipelineApprovedResponse,
)
from src.skills import publisher as sk

router = APIRouter()


@router.post("/read_pipeline_approved", response_model=ReadPipelineApprovedResponse)
async def read_pipeline_approved(req: ReadPipelineApprovedRequest):
    return await sk.read_pipeline_approved(req)


@router.post("/read_channels_active", response_model=ReadChannelsActiveResponse)
async def read_channels_active(req: ReadChannelsActiveRequest):
    return await sk.read_channels_active(req)


@router.post("/post_instagram", response_model=PostResponse)
async def post_instagram(req: PostRequest):
    return await sk.post_instagram(req)


@router.post("/post_tiktok", response_model=PostResponse)
async def post_tiktok(req: PostRequest):
    return await sk.post_tiktok(req)


@router.post("/post_youtube_shorts", response_model=PostResponse)
async def post_youtube_shorts(req: PostRequest):
    return await sk.post_youtube_shorts(req)


@router.post("/create_performance_row", response_model=CreatePerformanceRowResponse)
async def create_performance_row(req: CreatePerformanceRowRequest):
    return await sk.create_performance_row(req)
