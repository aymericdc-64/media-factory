"""Publisher skills — query approved rows, post to each active channel, create Performance row."""
from __future__ import annotations

from datetime import datetime, timezone

from src.clients.notion import notion_client
from src.clients.social_platforms import social_client
from src.config import settings
from src.logging_config import get_logger
from src.schemas.publisher import (
    ApprovedRowItem,
    ChannelItem,
    CreatePerformanceRowRequest,
    CreatePerformanceRowResponse,
    PostRequest,
    PostResponse,
    ReadChannelsActiveRequest,
    ReadChannelsActiveResponse,
    ReadPipelineApprovedRequest,
    ReadPipelineApprovedResponse,
)

log = get_logger(__name__)


async def read_pipeline_approved(req: ReadPipelineApprovedRequest) -> ReadPipelineApprovedResponse:
    nc = notion_client()
    now_iso = datetime.now(timezone.utc).isoformat()
    pages = await nc.query_data_source(
        data_source_id=settings.NOTION_DS_PRODUCTION_PIPELINE,
        filter={
            "and": [
                {"property": "Status", "select": {"equals": "Approved"}},
                {"property": "Scheduled Publish", "date": {"on_or_before": now_iso}},
            ]
        },
        page_size=req.limit,
    )
    rows: list[ApprovedRowItem] = []
    for p in pages.get("results", []):
        pr = p["properties"]
        rows.append(
            ApprovedRowItem(
                page_id=p["id"],
                prod_id=nc.extract_unique_id(pr.get("Prod ID")),
                title=nc.extract_text(pr.get("Title")) or "(untitled)",
                final_asset_url=nc.extract_url(pr.get("Final Asset URL")),
                caption_fr=nc.extract_text(pr.get("Caption FR")),
                caption_en=nc.extract_text(pr.get("Caption EN")),
                hashtags=nc.extract_text(pr.get("Hashtags")),
                scheduled_publish=nc.extract_date_start(pr.get("Scheduled Publish")),
            )
        )
    return ReadPipelineApprovedResponse(rows=rows, total=len(rows))


async def read_channels_active(_req: ReadChannelsActiveRequest) -> ReadChannelsActiveResponse:
    nc = notion_client()
    pages = await nc.query_data_source(
        data_source_id=settings.NOTION_DS_CHANNELS,
        filter={"property": "Status", "select": {"equals": "Active"}},
    )
    channels: list[ChannelItem] = []
    for p in pages.get("results", []):
        pr = p["properties"]
        channels.append(
            ChannelItem(
                page_id=p["id"],
                channel=nc.extract_text(pr.get("Channel")) or "(untitled)",
                platform=nc.extract_select(pr.get("Platform")),
                handle=nc.extract_text(pr.get("Handle")),
                formats=nc.extract_multi_select(pr.get("Format")),
                posting_frequency=nc.extract_select(pr.get("Posting Frequency")),
                best_slot_utc=nc.extract_text(pr.get("Best Slot UTC")),
                status=nc.extract_select(pr.get("Status")),
            )
        )
    return ReadChannelsActiveResponse(channels=channels)


async def post_instagram(req: PostRequest) -> PostResponse:
    sc = social_client()
    out = await sc.post_instagram_reel(req.video_url, req.caption)
    return PostResponse(
        page_id=req.page_id, platform="Instagram", post_id=out["post_id"], post_url=out["post_url"]
    )


async def post_tiktok(req: PostRequest) -> PostResponse:
    sc = social_client()
    out = await sc.post_tiktok_video(req.video_url, req.caption)
    return PostResponse(
        page_id=req.page_id, platform="TikTok", post_id=out["post_id"], post_url=out["post_url"]
    )


async def post_youtube_shorts(req: PostRequest) -> PostResponse:
    sc = social_client()
    out = await sc.post_youtube_short(
        video_url=req.video_url,
        title=req.title or req.caption[:80],
        description=req.caption,
    )
    return PostResponse(
        page_id=req.page_id, platform="YouTube Shorts", post_id=out["post_id"], post_url=out["post_url"]
    )


async def create_performance_row(req: CreatePerformanceRowRequest) -> CreatePerformanceRowResponse:
    nc = notion_client()
    page = await nc.create_page(
        parent_data_source_id=settings.NOTION_DS_PERFORMANCE_TRACKER,
        properties={
            "Post": nc.title_prop(req.title),
            "Platform": nc.select_prop(req.platform),
            "Post URL": nc.url_prop(req.post_url),
            "Publish Date": nc.date_prop(req.publish_date),
            "Snapshot": nc.select_prop("D+1"),
            "Verdict": nc.select_prop("TBD"),
        },
    )
    return CreatePerformanceRowResponse(performance_page_id=page["id"])
