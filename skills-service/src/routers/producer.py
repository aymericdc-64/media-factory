"""Routes for the Producer agent."""
from __future__ import annotations

from fastapi import APIRouter

from src.schemas.producer import (
    AnimateVideoRequest,
    AnimateVideoResponse,
    ComposeCardRequest,
    ComposeCardResponse,
    ComposeFinalVideoRequest,
    ComposeFinalVideoResponse,
    GenerateImageRequest,
    GenerateImageResponse,
    GetAudioRequest,
    GetAudioResponse,
    UpdatePipelineStatusRequest,
    UpdatePipelineStatusResponse,
    UploadAssetRequest,
    UploadAssetResponse,
)
from src.skills import producer as sk

router = APIRouter()


@router.post("/generate_image", response_model=GenerateImageResponse)
async def generate_image(req: GenerateImageRequest):
    return await sk.generate_image(req)


@router.post("/compose_card", response_model=ComposeCardResponse)
async def compose_card(req: ComposeCardRequest):
    return await sk.compose_card(req)


@router.post("/animate_video", response_model=AnimateVideoResponse)
async def animate_video(req: AnimateVideoRequest):
    return await sk.animate_video(req)


@router.post("/get_audio", response_model=GetAudioResponse)
async def get_audio(req: GetAudioRequest):
    return await sk.get_audio(req)


@router.post("/compose_final_video", response_model=ComposeFinalVideoResponse)
async def compose_final_video(req: ComposeFinalVideoRequest):
    return await sk.compose_final_video(req)


@router.post("/upload_asset", response_model=UploadAssetResponse)
async def upload_asset(req: UploadAssetRequest):
    return await sk.upload_asset(req)


@router.post("/update_pipeline_status", response_model=UpdatePipelineStatusResponse)
async def update_pipeline_status(req: UpdatePipelineStatusRequest):
    return await sk.update_pipeline_status(req)
