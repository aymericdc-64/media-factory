"""Multi-platform publishing client : Instagram Graph, TikTok, YouTube Data API.

Each method returns {post_id, post_url} on success.
Doc :
 - Instagram Graph : https://developers.facebook.com/docs/instagram-api/guides/content-publishing
 - TikTok Content Posting : https://developers.tiktok.com/doc/content-posting-api-reference-upload-video
 - YouTube Data v3 : https://developers.google.com/youtube/v3/docs/videos/insert
"""
from __future__ import annotations

import asyncio
from typing import Any

import httpx

from src.config import settings
from src.logging_config import get_logger

log = get_logger(__name__)


class PublishError(Exception):
    pass


class SocialPlatformsClient:
    # =========================
    # Instagram Reels
    # =========================
    async def post_instagram_reel(
        self,
        video_url: str,
        caption: str,
    ) -> dict[str, str]:
        if not settings.INSTAGRAM_ACCESS_TOKEN or not settings.INSTAGRAM_BUSINESS_ACCOUNT_ID:
            raise PublishError("instagram not configured")
        token = settings.INSTAGRAM_ACCESS_TOKEN
        ig_id = settings.INSTAGRAM_BUSINESS_ACCOUNT_ID

        async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT_LONG) as c:
            # 1. Create container
            r = await c.post(
                f"https://graph.facebook.com/v21.0/{ig_id}/media",
                params={
                    "media_type": "REELS",
                    "video_url": video_url,
                    "caption": caption,
                    "access_token": token,
                },
            )
            r.raise_for_status()
            container_id = r.json()["id"]

            # 2. Wait until container is FINISHED
            for _ in range(30):
                s = await c.get(
                    f"https://graph.facebook.com/v21.0/{container_id}",
                    params={"fields": "status_code", "access_token": token},
                )
                if s.json().get("status_code") == "FINISHED":
                    break
                await asyncio.sleep(5)
            else:
                raise PublishError("instagram container never finished")

            # 3. Publish
            p = await c.post(
                f"https://graph.facebook.com/v21.0/{ig_id}/media_publish",
                params={"creation_id": container_id, "access_token": token},
            )
            p.raise_for_status()
            media_id = p.json()["id"]

            # 4. Get permalink
            link = await c.get(
                f"https://graph.facebook.com/v21.0/{media_id}",
                params={"fields": "permalink", "access_token": token},
            )
            return {
                "post_id": str(media_id),
                "post_url": link.json().get("permalink", ""),
            }

    # =========================
    # TikTok
    # =========================
    async def post_tiktok_video(
        self,
        video_url: str,
        caption: str,
    ) -> dict[str, str]:
        if not settings.TIKTOK_ACCESS_TOKEN:
            raise PublishError("tiktok not configured")
        token = settings.TIKTOK_ACCESS_TOKEN

        async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT_LONG) as c:
            r = await c.post(
                "https://open.tiktokapis.com/v2/post/publish/video/init/",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json={
                    "post_info": {
                        "title": caption[:150],
                        "privacy_level": "PUBLIC_TO_EVERYONE",
                        "disable_duet": False,
                        "disable_comment": False,
                        "disable_stitch": False,
                    },
                    "source_info": {
                        "source": "PULL_FROM_URL",
                        "video_url": video_url,
                    },
                },
            )
            r.raise_for_status()
            data = r.json()
            publish_id = data.get("data", {}).get("publish_id")
            return {
                "post_id": str(publish_id or ""),
                "post_url": f"https://www.tiktok.com/@me/video/{publish_id}",
            }

    # =========================
    # YouTube Shorts
    # =========================
    async def post_youtube_short(
        self,
        video_url: str,
        title: str,
        description: str,
    ) -> dict[str, str]:
        if not (settings.YOUTUBE_REFRESH_TOKEN and settings.YOUTUBE_CLIENT_ID):
            raise PublishError("youtube not configured")

        # 1. Exchange refresh_token for access_token
        async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT_LONG) as c:
            tok = await c.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": settings.YOUTUBE_CLIENT_ID,
                    "client_secret": settings.YOUTUBE_CLIENT_SECRET,
                    "refresh_token": settings.YOUTUBE_REFRESH_TOKEN,
                    "grant_type": "refresh_token",
                },
            )
            tok.raise_for_status()
            access_token = tok.json()["access_token"]

            # 2. Download video bytes
            v = await c.get(video_url)
            v.raise_for_status()
            video_bytes = v.content

            # 3. Resumable upload (simplified : single-shot)
            metadata = {
                "snippet": {
                    "title": title[:100],
                    "description": description[:5000],
                    "tags": ["Shorts"],
                    "categoryId": "24",  # Entertainment
                },
                "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False},
            }
            upload_url = "https://www.googleapis.com/upload/youtube/v3/videos"
            up = await c.post(
                upload_url,
                params={"uploadType": "multipart", "part": "snippet,status"},
                headers={"Authorization": f"Bearer {access_token}"},
                files={
                    "metadata": (None, str(metadata).replace("'", '"'), "application/json"),
                    "video": ("video.mp4", video_bytes, "video/mp4"),
                },
            )
            up.raise_for_status()
            video_id = up.json().get("id")
            return {
                "post_id": str(video_id),
                "post_url": f"https://www.youtube.com/shorts/{video_id}",
            }

    # =========================
    # Metrics fetching
    # =========================
    async def fetch_instagram_metrics(self, post_id: str) -> dict[str, float]:
        token = settings.INSTAGRAM_ACCESS_TOKEN
        async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT_DEFAULT) as c:
            r = await c.get(
                f"https://graph.facebook.com/v21.0/{post_id}/insights",
                params={
                    "metric": "reach,likes,comments,shares,saved,total_interactions,plays",
                    "access_token": token,
                },
            )
            r.raise_for_status()
            data = {m["name"]: m["values"][0].get("value", 0) for m in r.json().get("data", [])}
            return {
                "views": float(data.get("plays", 0)),
                "likes": float(data.get("likes", 0)),
                "comments": float(data.get("comments", 0)),
                "shares": float(data.get("shares", 0)),
                "saves": float(data.get("saved", 0)),
                "reach": float(data.get("reach", 0)),
            }

    async def fetch_tiktok_metrics(self, post_id: str) -> dict[str, float]:
        token = settings.TIKTOK_ACCESS_TOKEN
        async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT_DEFAULT) as c:
            r = await c.get(
                "https://open.tiktokapis.com/v2/research/video/query/",
                headers={"Authorization": f"Bearer {token}"},
                params={"fields": "view_count,like_count,comment_count,share_count"},
                json={"query": {"and": [{"operation": "EQ", "field_name": "video_id", "field_values": [post_id]}]}},
            )
            r.raise_for_status()
            videos = r.json().get("data", {}).get("videos", [])
            if not videos:
                return {"views": 0, "likes": 0, "comments": 0, "shares": 0}
            v = videos[0]
            return {
                "views": float(v.get("view_count", 0)),
                "likes": float(v.get("like_count", 0)),
                "comments": float(v.get("comment_count", 0)),
                "shares": float(v.get("share_count", 0)),
            }

    async def fetch_youtube_metrics(self, video_id: str) -> dict[str, float]:
        async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT_LONG) as c:
            tok = await c.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": settings.YOUTUBE_CLIENT_ID,
                    "client_secret": settings.YOUTUBE_CLIENT_SECRET,
                    "refresh_token": settings.YOUTUBE_REFRESH_TOKEN,
                    "grant_type": "refresh_token",
                },
            )
            tok.raise_for_status()
            access_token = tok.json()["access_token"]

            r = await c.get(
                "https://youtube.googleapis.com/youtube/v3/videos",
                params={"part": "statistics", "id": video_id},
                headers={"Authorization": f"Bearer {access_token}"},
            )
            r.raise_for_status()
            items = r.json().get("items", [])
            if not items:
                return {"views": 0, "likes": 0, "comments": 0}
            s = items[0]["statistics"]
            return {
                "views": float(s.get("viewCount", 0)),
                "likes": float(s.get("likeCount", 0)),
                "comments": float(s.get("commentCount", 0)),
            }


_social_client: SocialPlatformsClient | None = None


def social_client() -> SocialPlatformsClient:
    global _social_client
    if _social_client is None:
        _social_client = SocialPlatformsClient()
    return _social_client
