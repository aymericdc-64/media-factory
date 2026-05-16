"""Analyst skills — fetch metrics, compute engagement & verdict, write notes & back to Notion."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from src.clients.anthropic_client import anthropic_client
from src.clients.notion import notion_client
from src.clients.social_platforms import social_client
from src.config import settings
from src.logging_config import get_logger
from src.schemas.analyst import (
    ComputeEngagementRequest,
    ComputeEngagementResponse,
    ComputeVerdictRequest,
    ComputeVerdictResponse,
    FetchMetricsRequest,
    FetchMetricsResponse,
    ReadAnalystSnapshotRequest,
    ReadAnalystSnapshotResponse,
    SnapshotRowItem,
    UpdatePerformanceRequest,
    UpdatePerformanceResponse,
    WriteAnalystNotesRequest,
    WriteAnalystNotesResponse,
)

log = get_logger(__name__)

ANALYST_SYSTEM = """You are the Analyst writing a one-paragraph natural-language note
about a social post's performance.
Constraints :
  - 2-3 sentences max, 200 chars
  - mention the verdict explicitly
  - cite ONE notable metric (best or worst)
  - end with a forward-looking signal (re-promote, kill, watch)
Output the note as plain text — no JSON, no markdown."""


async def fetch_metrics(req: FetchMetricsRequest) -> FetchMetricsResponse:
    sc = social_client()
    if req.platform == "Instagram":
        m = await sc.fetch_instagram_metrics(req.post_id)
    elif req.platform == "TikTok":
        m = await sc.fetch_tiktok_metrics(req.post_id)
    elif req.platform == "YouTube Shorts":
        m = await sc.fetch_youtube_metrics(req.post_id)
    else:
        # Stub for Threads / X / Pinterest / LinkedIn — TODO when keys available
        log.warning("fetch_metrics_not_implemented", platform=req.platform)
        m = {"views": 0, "likes": 0, "comments": 0, "shares": 0}

    return FetchMetricsResponse(
        views=m.get("views", 0),
        likes=m.get("likes", 0),
        comments=m.get("comments", 0),
        shares=m.get("shares", 0),
        saves=m.get("saves", 0),
        follows_gained=m.get("follows_gained", 0),
        watch_time_sec=m.get("watch_time_sec", 0),
    )


async def compute_engagement_rate(req: ComputeEngagementRequest) -> ComputeEngagementResponse:
    if req.views <= 0:
        return ComputeEngagementResponse(engagement_rate=0.0)
    interactions = req.likes + req.comments + req.shares + req.saves
    rate = interactions / req.views
    return ComputeEngagementResponse(engagement_rate=round(rate, 4))


async def compute_verdict(req: ComputeVerdictRequest) -> ComputeVerdictResponse:
    views_b = req.benchmarks.get("views", {})
    er_b = req.benchmarks.get("er", {})

    if req.views >= views_b.get("p90", 1e9) and req.engagement_rate >= 0.08:
        return ComputeVerdictResponse(
            verdict="Banger",
            rationale=f"Views ≥ p90 ({views_b.get('p90')}) and ER ≥ 8% ({req.engagement_rate:.1%}).",
        )
    if views_b.get("p50", 0) <= req.views < views_b.get("p90", 1e9) and req.engagement_rate >= 0.05:
        return ComputeVerdictResponse(
            verdict="Solid",
            rationale=f"Views in [p50, p90[ and ER ≥ 5% ({req.engagement_rate:.1%}).",
        )
    if views_b.get("p25", 0) <= req.views < views_b.get("p50", 1e9):
        return ComputeVerdictResponse(
            verdict="Mid",
            rationale=f"Views in [p25, p50[ ({req.views:.0f}).",
        )
    if req.views < views_b.get("p25", 0):
        return ComputeVerdictResponse(
            verdict="Flop",
            rationale=f"Views below p25 ({views_b.get('p25')}).",
        )
    return ComputeVerdictResponse(verdict="TBD", rationale="Not enough data yet.")


async def write_analyst_notes(req: WriteAnalystNotesRequest) -> WriteAnalystNotesResponse:
    ac = anthropic_client()
    prompt = (
        f"METRICS: {req.metrics}\n"
        f"VERDICT: {req.verdict}\n"
        f"CONTEXT: {req.context}\n\n"
        "Write the natural-language note now."
    )
    text = await ac.text_completion(
        model=settings.ANTHROPIC_MODEL_ANALYST,
        system=ANALYST_SYSTEM,
        prompt=prompt,
        max_tokens=200,
        temperature=0.5,
    )
    return WriteAnalystNotesResponse(notes=text[:400])


async def update_performance(req: UpdatePerformanceRequest) -> UpdatePerformanceResponse:
    nc = notion_client()
    await nc.update_page(
        req.performance_page_id,
        properties={
            "Views": nc.number_prop(req.views),
            "Likes": nc.number_prop(req.likes),
            "Comments": nc.number_prop(req.comments),
            "Shares": nc.number_prop(req.shares),
            "Saves": nc.number_prop(req.saves),
            "Follows Gained": nc.number_prop(req.follows_gained),
            "Watch Time Sec": nc.number_prop(req.watch_time_sec),
            "Engagement Rate": nc.number_prop(req.engagement_rate),
            "Verdict": nc.select_prop(req.verdict),
            "Notes": nc.text_prop(req.notes),
        },
    )
    return UpdatePerformanceResponse(page_id=req.performance_page_id)


async def read_snapshot(req: ReadAnalystSnapshotRequest) -> ReadAnalystSnapshotResponse:
    nc = notion_client()
    today = datetime.now(timezone.utc).date()
    offset_days = {"D+1": 1, "D+7": 7, "D+30": 30}[req.snapshot]
    target_date = (today - timedelta(days=offset_days)).isoformat()

    pages = await nc.query_data_source(
        data_source_id=settings.NOTION_DS_PERFORMANCE_TRACKER,
        filter={
            "and": [
                {"property": "Snapshot", "select": {"equals": req.snapshot}},
                {"property": "Publish Date", "date": {"equals": target_date}},
            ]
        },
    )
    rows: list[SnapshotRowItem] = []
    for p in pages.get("results", []):
        pr = p["properties"]
        rows.append(
            SnapshotRowItem(
                performance_page_id=p["id"],
                post_id=nc.extract_unique_id(pr.get("Post ID")),
                post=nc.extract_text(pr.get("Post")) or "(untitled)",
                platform=nc.extract_select(pr.get("Platform")),
                publish_date=nc.extract_date_start(pr.get("Publish Date")),
                post_url=nc.extract_url(pr.get("Post URL")),
            )
        )
    return ReadAnalystSnapshotResponse(rows=rows)
