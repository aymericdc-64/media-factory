"""Factory Skills Service entrypoint.

This service exposes 27 atomic skills (Tool Use endpoints) consumed by Claude
agents inside n8n. Every /strategist, /producer, /scorer, /publisher, /analyst
route is protected by a bearer token. /health and /tools are public.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse

from src.auth import verify_token
from src.logging_config import configure_logging, get_logger
from src.routers import analyst, producer, publisher, scorer, strategist
from src.tool_definitions import load_all_tool_definitions

configure_logging()
log = get_logger("factory-skills-service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("startup", version="0.1.0")
    yield
    log.info("shutdown")


app = FastAPI(
    title="Factory Skills Service",
    description="Atomic skills exposed to Claude agents (Anthropic Tool Use).",
    version="0.1.0",
    lifespan=lifespan,
)


# --- Public endpoints ---

@app.get("/health", tags=["meta"])
async def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}


@app.get("/tools", tags=["meta"])
async def tools() -> JSONResponse:
    """Return the full Anthropic Tool Use schema for every skill.

    Used by n8n at workflow build-time, or by MCP clients.
    """
    return JSONResponse(content=load_all_tool_definitions())


# --- Skill routers (all gated by bearer auth) ---

app.include_router(
    strategist.router,
    prefix="/strategist",
    tags=["strategist"],
    dependencies=[Depends(verify_token)],
)
app.include_router(
    producer.router,
    prefix="/producer",
    tags=["producer"],
    dependencies=[Depends(verify_token)],
)
app.include_router(
    scorer.router,
    prefix="/scorer",
    tags=["scorer"],
    dependencies=[Depends(verify_token)],
)
app.include_router(
    publisher.router,
    prefix="/publisher",
    tags=["publisher"],
    dependencies=[Depends(verify_token)],
)
app.include_router(
    analyst.router,
    prefix="/analyst",
    tags=["analyst"],
    dependencies=[Depends(verify_token)],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Any, exc: Exception) -> JSONResponse:
    log.error("unhandled_exception", error=str(exc), exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error_class": exc.__class__.__name__},
    )
