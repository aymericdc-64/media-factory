"""Strategist skills — read Notion DBs and write briefs into Production Pipeline."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from src.clients.notion import notion_client
from src.config import settings
from src.logging_config import get_logger
from src.schemas.strategist import (
    ConceptItem,
    PerformanceItem,
    ReadBibleCreativeRequest,
    ReadBibleCreativeResponse,
    ReadContentCatalogRequest,
    ReadContentCatalogResponse,
    ReadContentThemesRequest,
    ReadContentThemesResponse,
    ReadPerformanceTrackerRequest,
    ReadPerformanceTrackerResponse,
    ThemeItem,
    WriteBriefRequest,
    WriteBriefResponse,
)

log = get_logger(__name__)


# ===================================================================
# read_content_catalog
# ===================================================================
async def read_content_catalog(req: ReadContentCatalogRequest) -> ReadContentCatalogResponse:
    nc = notion_client()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=req.min_days_since_publish)).date().isoformat()

    filt = {
        "and": [
            {"property": "Status", "select": {"equals": req.status}},
            {
                "or": [
                    {"property": "Last Published", "date": {"before": cutoff}},
                    {"property": "Last Published", "date": {"is_empty": True}},
                ]
            },
        ]
    }

    pages = await nc.query_data_source(
        data_source_id=settings.NOTION_DS_CONTENT_CATALOG,
        filter=filt,
        page_size=req.limit,
    )

    items: list[ConceptItem] = []
    for p in pages.get("results", []):
        props = p["properties"]
        items.append(
            ConceptItem(
                page_id=p["id"],
                concept_id=nc.extract_unique_id(props.get("Concept ID")),
                concept=nc.extract_text(props.get("Concept")) or "(untitled)",
                hook=nc.extract_text(props.get("Hook")),
                logline=nc.extract_text(props.get("Logline")),
                tags=nc.extract_multi_select(props.get("Tags")),
                status=nc.extract_select(props.get("Status")),
                source=nc.extract_select(props.get("Source")),
                difficulty=nc.extract_select(props.get("Difficulty")),
                last_published=nc.extract_date_start(props.get("Last Published")),
                re_promote_score=nc.extract_number(props.get("Re-promote Score")),
                notes=nc.extract_text(props.get("Notes")),
            )
        )

    return ReadContentCatalogResponse(concepts=items, total=len(items))


# ===================================================================
# read_performance_tracker
# ===================================================================
async def read_performance_tracker(req: ReadPerformanceTrackerRequest) -> ReadPerformanceTrackerResponse:
    nc = notion_client()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=req.window_days)).date().isoformat()

    and_filters: list[dict] = [
        {"property": "Publish Date", "date": {"on_or_after": cutoff}}
    ]
    if req.snapshot:
        and_filters.append({"property": "Snapshot", "select": {"equals": req.snapshot}})

    pages = await nc.query_data_source(
        data_source_id=settings.NOTION_DS_PERFORMANCE_TRACKER,
        filter={"and": and_filters},
        sorts=[{"property": "Publish Date", "direction": "descending"}],
        page_size=req.limit,
    )

    items: list[PerformanceItem] = []
    for p in pages.get("results", []):
        pr = p["properties"]
        items.append(
            PerformanceItem(
                page_id=p["id"],
                post_id=nc.extract_unique_id(pr.get("Post ID")),
                post=nc.extract_text(pr.get("Post")),
                platform=nc.extract_select(pr.get("Platform")),
                publish_date=nc.extract_date_start(pr.get("Publish Date")),
                snapshot=nc.extract_select(pr.get("Snapshot")),
                views=nc.extract_number(pr.get("Views")),
                likes=nc.extract_number(pr.get("Likes")),
                comments=nc.extract_number(pr.get("Comments")),
                shares=nc.extract_number(pr.get("Shares")),
                saves=nc.extract_number(pr.get("Saves")),
                follows_gained=nc.extract_number(pr.get("Follows Gained")),
                engagement_rate=nc.extract_number(pr.get("Engagement Rate")),
                watch_time_sec=nc.extract_number(pr.get("Watch Time Sec")),
                verdict=nc.extract_select(pr.get("Verdict")),
                post_url=nc.extract_url(pr.get("Post URL")),
            )
        )
    return ReadPerformanceTrackerResponse(items=items, total=len(items))


# ===================================================================
# read_content_themes
# ===================================================================
async def read_content_themes(req: ReadContentThemesRequest) -> ReadContentThemesResponse:
    nc = notion_client()
    pages = await nc.query_data_source(
        data_source_id=settings.NOTION_DS_CONTENT_THEMES,
        filter={"property": "Status", "select": {"equals": req.status}},
    )
    themes: list[ThemeItem] = []
    for p in pages.get("results", []):
        pr = p["properties"]
        themes.append(
            ThemeItem(
                page_id=p["id"],
                theme=nc.extract_text(pr.get("Theme")) or "(untitled)",
                code=nc.extract_text(pr.get("Code")),
                description=nc.extract_text(pr.get("Description")),
                tone=nc.extract_text(pr.get("Tone")),
                visual_codes=nc.extract_text(pr.get("Visual Codes")),
                color=nc.extract_select(pr.get("Color")),
                status=nc.extract_select(pr.get("Status")),
            )
        )
    return ReadContentThemesResponse(themes=themes)


# ===================================================================
# read_bible_creative
# ===================================================================
async def read_bible_creative(req: ReadBibleCreativeRequest) -> ReadBibleCreativeResponse:
    nc = notion_client()
    children = await nc.get_block_children(req.page_id, page_size=100)
    chunks: list[str] = []
    for b in children.get("results", []):
        t = b.get("type")
        block = b.get(t, {})
        rich = block.get("rich_text", [])
        if rich:
            chunks.append("".join(r.get("plain_text", "") for r in rich))
    return ReadBibleCreativeResponse(page_id=req.page_id, plain_text="\n".join(chunks))


# ===================================================================
# write_brief_to_pipeline
# ===================================================================
async def write_brief_to_pipeline(req: WriteBriefRequest) -> WriteBriefResponse:
    nc = notion_client()
    properties = {
        "Title": nc.title_prop(req.title),
        "Brief": nc.text_prop(req.brief),
        "Script": nc.text_prop(req.script),
        "Status": nc.select_prop("Briefed"),
        "Linked Agent": nc.select_prop(req.linked_agent),
        "Production Date": nc.date_prop(datetime.now(timezone.utc).date().isoformat()),
    }
    page = await nc.create_page(
        parent_data_source_id=settings.NOTION_DS_PRODUCTION_PIPELINE,
        properties=properties,
    )
    return WriteBriefResponse(
        page_id=page["id"],
        prod_id=nc.extract_unique_id(page.get("properties", {}).get("Prod ID")),
        status="Briefed",
    )
