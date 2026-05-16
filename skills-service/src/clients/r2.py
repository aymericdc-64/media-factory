"""Cloudflare R2 storage client (S3-compatible) using boto3 in async-friendly way.

Doc : https://developers.cloudflare.com/r2/api/s3/api/
"""
from __future__ import annotations

import asyncio
from typing import BinaryIO

import boto3
import httpx

from src.config import settings
from src.logging_config import get_logger

log = get_logger(__name__)


class R2Client:
    def __init__(self) -> None:
        if not settings.R2_ACCOUNT_ID:
            log.warning("r2_not_configured")
            self._s3 = None
            return
        endpoint = f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
        self._s3 = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            region_name="auto",
        )

    async def upload_url(self, source_url: str, key: str, content_type: str = "video/mp4") -> str:
        """Download from source_url and upload to R2 under key. Returns the public URL."""
        if not self._s3:
            raise RuntimeError("R2 not configured")

        async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT_LONG) as c:
            r = await c.get(source_url)
            r.raise_for_status()
            data = r.content

        await asyncio.to_thread(
            self._s3.put_object,
            Bucket=settings.R2_BUCKET,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
        log.info("r2_uploaded", key=key, bytes=len(data))
        return f"{settings.R2_PUBLIC_URL_BASE.rstrip('/')}/{key}"

    async def upload_bytes(self, data: bytes | BinaryIO, key: str, content_type: str) -> str:
        if not self._s3:
            raise RuntimeError("R2 not configured")
        await asyncio.to_thread(
            self._s3.put_object,
            Bucket=settings.R2_BUCKET,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
        return f"{settings.R2_PUBLIC_URL_BASE.rstrip('/')}/{key}"


_r2_client: R2Client | None = None


def r2_client() -> R2Client:
    global _r2_client
    if _r2_client is None:
        _r2_client = R2Client()
    return _r2_client
