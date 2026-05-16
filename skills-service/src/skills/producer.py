"""Producer skills — generate image, animate, compose, upload, update Notion."""
from __future__ import annotations

from src.clients.creatomate import creatomate_client
from src.clients.epidemic import epidemic_client
from src.clients.falai import falai_client
from src.clients.notion import notion_client
from src.clients.r2 import r2_client
from src.config import settings
from src.logging_config import get_logger
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

log = get_logger(__name__)


async def generate_image(req: GenerateImageRequest) -> GenerateImageResponse:
    fc = falai_client()
    out = await fc.generate_image(req.prompt, aspect_ratio=req.aspect_ratio)
    if not out.get("url"):
        raise RuntimeError("fal.ai returned no image URL")
    return GenerateImageResponse(**out)


async def compose_card(req: ComposeCardRequest) -> ComposeCardResponse:
    cc = creatomate_client()
    tpl = req.template_id or settings.CREATOMATE_TEMPLATE_CARD
    if not tpl:
        raise RuntimeError("CREATOMATE_TEMPLATE_CARD not configured")

    modifications = {
        "image-1.source": req.image_url,
        "title-1.text": req.title,
        **({"subtitle-1.text": req.subtitle} if req.subtitle else {}),
        **({"hp-1.text": req.hp} if req.hp else {}),
        **({"energy-1.text": req.energy_type} if req.energy_type else {}),
        **req.extras,
    }
    res = await cc.render(tpl, modifications, output_format="png")
    return ComposeCardResponse(url=res["url"], render_id=res["render_id"])


async def animate_video(req: AnimateVideoRequest) -> AnimateVideoResponse:
    fc = falai_client()
    out = await fc.animate_image_to_video(req.image_url, req.prompt, req.duration_seconds)
    if not out.get("url"):
        raise RuntimeError("fal.ai returned no video URL")
    return AnimateVideoResponse(url=out["url"], duration=out["duration"])


async def get_audio(req: GetAudioRequest) -> GetAudioResponse:
    ec = epidemic_client()
    out = await ec.search_track(req.mood, max_duration_s=req.max_duration_s)
    return GetAudioResponse(**out)


async def compose_final_video(req: ComposeFinalVideoRequest) -> ComposeFinalVideoResponse:
    cc = creatomate_client()
    tpl = req.template_id or settings.CREATOMATE_TEMPLATE_VIDEO_FINAL
    if not tpl:
        raise RuntimeError("CREATOMATE_TEMPLATE_VIDEO_FINAL not configured")

    modifications = {
        "card-image.source": req.card_image_url,
        "animation.source": req.animation_url,
        "audio.source": req.audio_url,
        **({"caption.text": req.caption} if req.caption else {}),
        **({"watermark.text": req.watermark_text} if req.watermark_text else {}),
        **req.extras,
    }
    res = await cc.render(tpl, modifications, output_format="mp4")
    return ComposeFinalVideoResponse(url=res["url"], render_id=res["render_id"])


async def upload_asset(req: UploadAssetRequest) -> UploadAssetResponse:
    r = r2_client()
    url = await r.upload_url(req.source_url, req.key, req.content_type)
    return UploadAssetResponse(url=url)


async def update_pipeline_status(req: UpdatePipelineStatusRequest) -> UpdatePipelineStatusResponse:
    nc = notion_client()
    properties: dict = {"Status": nc.select_prop(req.status)}
    if req.final_asset_url is not None:
        properties["Final Asset URL"] = nc.url_prop(req.final_asset_url)
    if req.error is not None:
        properties["Error"] = nc.text_prop(req.error)
    if req.score is not None:
        properties["Score"] = nc.number_prop(req.score)
    if req.caption_fr is not None:
        properties["Caption FR"] = nc.text_prop(req.caption_fr)
    if req.caption_en is not None:
        properties["Caption EN"] = nc.text_prop(req.caption_en)
    if req.hashtags is not None:
        properties["Hashtags"] = nc.text_prop(req.hashtags)
    if req.scheduled_publish is not None:
        properties["Scheduled Publish"] = nc.date_prop(req.scheduled_publish)

    await nc.update_page(req.page_id, properties=properties)
    return UpdatePipelineStatusResponse(page_id=req.page_id, status=req.status)
