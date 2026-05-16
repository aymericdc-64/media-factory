"""Thin async wrapper around the Notion data-source API.

The Notion `notion-client` SDK is sync; we use raw httpx for predictable async I/O.
Doc : https://developers.notion.com/reference
"""
from __future__ import annotations

from typing import Any

import httpx

from src.config import settings
from src.logging_config import get_logger

log = get_logger(__name__)

NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2025-09-03"  # Pin a known version


class NotionError(Exception):
    pass


class NotionClient:
    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or settings.NOTION_API_KEY
        self._client = httpx.AsyncClient(
            base_url=NOTION_API_BASE,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Notion-Version": NOTION_VERSION,
                "Content-Type": "application/json",
            },
            timeout=settings.HTTP_TIMEOUT_DEFAULT,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    # ---- low-level ----

    async def _request(self, method: str, path: str, **kw) -> dict[str, Any]:
        r = await self._client.request(method, path, **kw)
        if r.status_code >= 400:
            log.error("notion_error", method=method, path=path, status=r.status_code, body=r.text[:500])
            raise NotionError(f"Notion {method} {path} → {r.status_code}: {r.text[:300]}")
        return r.json()

    # ---- data sources ----

    async def query_data_source(
        self,
        data_source_id: str,
        filter: dict[str, Any] | None = None,
        sorts: list[dict[str, Any]] | None = None,
        page_size: int = 100,
        start_cursor: str | None = None,
    ) -> dict[str, Any]:
        """POST /data_sources/{id}/query — Notion API 2025-09 syntax."""
        payload: dict[str, Any] = {"page_size": page_size}
        if filter:
            payload["filter"] = filter
        if sorts:
            payload["sorts"] = sorts
        if start_cursor:
            payload["start_cursor"] = start_cursor
        return await self._request("POST", f"/data_sources/{data_source_id}/query", json=payload)

    async def query_all(
        self,
        data_source_id: str,
        filter: dict[str, Any] | None = None,
        sorts: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        """Loop through pagination and return every page."""
        results: list[dict[str, Any]] = []
        cursor: str | None = None
        while True:
            res = await self.query_data_source(
                data_source_id, filter=filter, sorts=sorts, start_cursor=cursor
            )
            results.extend(res.get("results", []))
            if not res.get("has_more"):
                break
            cursor = res.get("next_cursor")
        return results

    # ---- pages ----

    async def create_page(
        self,
        parent_data_source_id: str,
        properties: dict[str, Any],
    ) -> dict[str, Any]:
        payload = {
            "parent": {"type": "data_source_id", "data_source_id": parent_data_source_id},
            "properties": properties,
        }
        return await self._request("POST", "/pages", json=payload)

    async def update_page(
        self,
        page_id: str,
        properties: dict[str, Any] | None = None,
        archived: bool | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if properties is not None:
            payload["properties"] = properties
        if archived is not None:
            payload["archived"] = archived
        return await self._request("PATCH", f"/pages/{page_id}", json=payload)

    async def get_page(self, page_id: str) -> dict[str, Any]:
        return await self._request("GET", f"/pages/{page_id}")

    async def get_block_children(self, block_id: str, page_size: int = 100) -> dict[str, Any]:
        return await self._request(
            "GET", f"/blocks/{block_id}/children", params={"page_size": page_size}
        )

    # ---- helpers for property serialization ----

    @staticmethod
    def title_prop(text: str) -> dict[str, Any]:
        return {"title": [{"type": "text", "text": {"content": text}}]}

    @staticmethod
    def text_prop(text: str) -> dict[str, Any]:
        return {"rich_text": [{"type": "text", "text": {"content": text}}]}

    @staticmethod
    def select_prop(name: str) -> dict[str, Any]:
        return {"select": {"name": name}}

    @staticmethod
    def multi_select_prop(names: list[str]) -> dict[str, Any]:
        return {"multi_select": [{"name": n} for n in names]}

    @staticmethod
    def number_prop(value: float | int) -> dict[str, Any]:
        return {"number": value}

    @staticmethod
    def url_prop(url: str) -> dict[str, Any]:
        return {"url": url}

    @staticmethod
    def date_prop(start: str, end: str | None = None) -> dict[str, Any]:
        d: dict[str, Any] = {"start": start}
        if end:
            d["end"] = end
        return {"date": d}

    @staticmethod
    def extract_text(prop: dict[str, Any] | None) -> str | None:
        """Extract plain text from a title or rich_text property."""
        if not prop:
            return None
        if "title" in prop and prop["title"]:
            return "".join(t.get("plain_text", "") for t in prop["title"]) or None
        if "rich_text" in prop and prop["rich_text"]:
            return "".join(t.get("plain_text", "") for t in prop["rich_text"]) or None
        return None

    @staticmethod
    def extract_select(prop: dict[str, Any] | None) -> str | None:
        if not prop or not prop.get("select"):
            return None
        return prop["select"].get("name")

    @staticmethod
    def extract_multi_select(prop: dict[str, Any] | None) -> list[str]:
        if not prop:
            return []
        return [t["name"] for t in prop.get("multi_select", [])]

    @staticmethod
    def extract_number(prop: dict[str, Any] | None) -> float | None:
        return prop.get("number") if prop else None

    @staticmethod
    def extract_url(prop: dict[str, Any] | None) -> str | None:
        return prop.get("url") if prop else None

    @staticmethod
    def extract_date_start(prop: dict[str, Any] | None) -> str | None:
        if not prop or not prop.get("date"):
            return None
        return prop["date"].get("start")

    @staticmethod
    def extract_unique_id(prop: dict[str, Any] | None) -> int | None:
        if not prop or not prop.get("unique_id"):
            return None
        return prop["unique_id"].get("number")


# Module-level singleton — instantiated lazily
_notion_client: NotionClient | None = None


def notion_client() -> NotionClient:
    global _notion_client
    if _notion_client is None:
        _notion_client = NotionClient()
    return _notion_client
