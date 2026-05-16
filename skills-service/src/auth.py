"""Bearer-token auth used by every router. n8n must pass Authorization: Bearer <SKILLS_AUTH_SECRET>."""
from __future__ import annotations

import hmac

from fastapi import Header, HTTPException

from src.config import settings


async def verify_token(authorization: str = Header(..., alias="Authorization")) -> None:
    """Raise 401/403 if the bearer token is missing or wrong."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or malformed bearer token")

    presented = authorization.removeprefix("Bearer ").strip()
    expected = settings.SKILLS_AUTH_SECRET

    # constant-time compare to defeat timing oracles
    if not hmac.compare_digest(presented.encode(), expected.encode()):
        raise HTTPException(status_code=403, detail="Invalid bearer token")
