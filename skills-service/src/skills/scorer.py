"""Scorer skills — vision-scoring of produced videos + writing back to Notion."""
from __future__ import annotations

import json

from src.clients.anthropic_client import anthropic_client
from src.clients.notion import notion_client
from src.config import settings
from src.logging_config import get_logger
from src.schemas.scorer import (
    PipelineRowItem,
    ReadProductionPipelineRequest,
    ReadProductionPipelineResponse,
    ScoreVideoRequest,
    ScoreVideoResponse,
    WriteCaptionScoreRequest,
    WriteCaptionScoreResponse,
)

log = get_logger(__name__)

SCORER_SYSTEM = """You are the Scorer agent for an automated social-media factory.
You receive: a brief, an excerpt from the brand's creative bible, and a video URL.
You judge the video on FIVE criteria, each 0-10:
  1. Hook strength (first 1s grabs attention?)
  2. Visual quality (composition, brand coherence)
  3. Story clarity (pacing, payoff in 9s)
  4. Brand fit (matches bible créative tone)
  5. Virality potential (shareable? polarizing in a good way?)
You output STRICT JSON with these keys:
  - score (float, average of the 5)
  - rationale (string, <120 chars)
  - caption_fr (string, ≤180 chars, with 1-2 emoji)
  - caption_en (string, ≤180 chars)
  - hashtags (string, 5-8 hashtags separated by spaces, no comma)
No prose, no markdown. JSON only."""


async def read_production_pipeline(req: ReadProductionPipelineRequest) -> ReadProductionPipelineResponse:
    nc = notion_client()
    pages = await nc.query_data_source(
        data_source_id=settings.NOTION_DS_PRODUCTION_PIPELINE,
        filter={"property": "Status", "select": {"equals": req.status}},
        sorts=[{"timestamp": "created_time", "direction": "descending"}],
        page_size=req.limit,
    )
    rows: list[PipelineRowItem] = []
    for p in pages.get("results", []):
        pr = p["properties"]
        rows.append(
            PipelineRowItem(
                page_id=p["id"],
                prod_id=nc.extract_unique_id(pr.get("Prod ID")),
                title=nc.extract_text(pr.get("Title")) or "(untitled)",
                brief=nc.extract_text(pr.get("Brief")),
                script=nc.extract_text(pr.get("Script")),
                final_asset_url=nc.extract_url(pr.get("Final Asset URL")),
                status=nc.extract_select(pr.get("Status")),
            )
        )
    return ReadProductionPipelineResponse(rows=rows, total=len(rows))


async def score_video(req: ScoreVideoRequest) -> ScoreVideoResponse:
    """Score a video using Claude vision. We sample the first frame URL.

    For now we pass the video URL directly to vision — Claude supports image URLs;
    in production wrap with a frame-extractor (ffmpeg → R2) for true video frame.
    """
    ac = anthropic_client()
    user_prompt = (
        f"BRIEF:\n{req.brief}\n\n"
        f"BIBLE EXCERPT:\n{req.bible_context[:1500]}\n\n"
        f"VIDEO URL: {req.final_asset_url}\n\n"
        "Score this video. Output JSON only."
    )

    raw = await ac.text_completion(
        model=settings.ANTHROPIC_MODEL_SCORER,
        system=SCORER_SYSTEM,
        prompt=user_prompt,
        max_tokens=600,
        temperature=0.3,
    )
    # Tolerate ```json fences
    cleaned = raw.strip().strip("`")
    if cleaned.startswith("json"):
        cleaned = cleaned[4:].strip()
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        log.error("scorer_json_parse_failed", raw=raw[:300])
        raise RuntimeError(f"Scorer returned invalid JSON: {e}") from e

    return ScoreVideoResponse(
        page_id=req.page_id,
        score=float(data.get("score", 0)),
        rationale=str(data.get("rationale", ""))[:200],
        caption_fr=str(data.get("caption_fr", "")),
        caption_en=str(data.get("caption_en", "")),
        hashtags=str(data.get("hashtags", "")),
    )


async def write_caption_score(req: WriteCaptionScoreRequest) -> WriteCaptionScoreResponse:
    nc = notion_client()
    await nc.update_page(
        req.page_id,
        properties={
            "Status": nc.select_prop("Scored"),
            "Score": nc.number_prop(req.score),
            "Caption FR": nc.text_prop(req.caption_fr),
            "Caption EN": nc.text_prop(req.caption_en),
            "Hashtags": nc.text_prop(req.hashtags),
        },
    )
    return WriteCaptionScoreResponse(page_id=req.page_id, status="Scored")
