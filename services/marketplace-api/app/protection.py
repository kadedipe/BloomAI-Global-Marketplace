import hashlib
import time

from fastapi import HTTPException, Request
from redis.asyncio import Redis

from .config import get_settings


async def enforce_csrf_origin(request: Request) -> None:
    settings = get_settings()
    if request.method not in {"POST", "PATCH", "PUT", "DELETE"}:
        return
    if not request.cookies.get(settings.auth_cookie_name):
        return
    origin = request.headers.get("origin")
    if not origin or origin.rstrip("/") not in settings.cors_origins:
        raise HTTPException(403, "Untrusted request origin")


async def rate_limit(request: Request, scope: str, limit: int, window_seconds: int) -> None:
    settings = get_settings()
    if not settings.rate_limit_enabled:
        return
    forwarded = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    identity = forwarded or (request.client.host if request.client else "unknown")
    digest = hashlib.sha256(identity.encode()).hexdigest()[:24]
    bucket = int(time.time() // window_seconds)
    key = f"ratelimit:{scope}:{digest}:{bucket}"
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, window_seconds + 1)
        if count > limit:
            raise HTTPException(429, "Too many requests; please try again later")
    except HTTPException:
        raise
    except Exception:
        # Availability-safe for the MVP; production monitoring must alert on Redis failures.
        return
    finally:
        await redis.aclose()
