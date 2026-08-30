import hashlib
import hmac

import httpx
from fastapi import HTTPException

from .config import get_settings

BASE_URL = "https://api.paystack.co"


def enabled() -> None:
    if not get_settings().paystack_enabled:
        raise HTTPException(503, "Paystack payments are not configured")


async def request(method: str, path: str, **kwargs) -> dict:
    enabled()
    headers = {"Authorization": f"Bearer {get_settings().paystack_secret_key}"}
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=15) as client:
        response = await client.request(method, path, headers=headers, **kwargs)
    if response.status_code >= 400:
        raise HTTPException(502, "Payment provider request failed")
    body = response.json()
    if not body.get("status"):
        raise HTTPException(502, "Payment provider rejected the request")
    return body["data"]


def valid_webhook_signature(payload: bytes, signature: str | None) -> bool:
    if not signature or not get_settings().paystack_secret_key:
        return False
    expected = hmac.new(get_settings().paystack_secret_key.encode(), payload, hashlib.sha512).hexdigest()
    return hmac.compare_digest(expected, signature)
