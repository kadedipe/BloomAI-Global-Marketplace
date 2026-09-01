from __future__ import annotations

import base64
import hashlib
import hmac
import logging

import httpx

from .config import get_settings

logger = logging.getLogger("bloomai.shipping")


def valid_aftership_signature(payload: bytes, signature: str | None) -> bool:
    secret = get_settings().aftership_webhook_secret
    if not secret or not signature:
        return False
    digest = hmac.new(secret.encode(), payload, hashlib.sha256).digest()
    expected = base64.b64encode(digest).decode()
    return hmac.compare_digest(expected, signature)


async def register_tracking(*, tracking_number: str, order_id: int, carrier: str | None = None) -> dict | None:
    settings = get_settings()
    if not settings.aftership_enabled:
        return None
    url = f"https://api.aftership.com/tracking/{settings.aftership_api_version}/trackings"
    tracking: dict = {
        "tracking_number": tracking_number,
        "custom_fields": {"bloomai_order_id": str(order_id)},
    }
    if carrier:
        tracking["title"] = f"BloomAI order #{order_id} · {carrier}"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                url,
                headers={
                    "as-api-key": settings.aftership_api_key,
                    "Content-Type": "application/json",
                },
                json={"tracking": tracking},
            )
            response.raise_for_status()
            body = response.json()
    except (httpx.HTTPError, ValueError):
        logger.exception("aftership_tracking_registration_failed order_id=%s", order_id)
        return None
    data = body.get("data", body)
    if isinstance(data, dict) and isinstance(data.get("tracking"), dict):
        data = data["tracking"]
    return data if isinstance(data, dict) else None
