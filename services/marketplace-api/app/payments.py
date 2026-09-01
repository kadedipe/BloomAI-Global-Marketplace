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
    try:
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=15) as client:
            response = await client.request(method, path, headers=headers, **kwargs)
    except httpx.RequestError as exc:
        raise HTTPException(502, "Payment provider is temporarily unreachable") from exc

    if response.status_code >= 400:
        raise HTTPException(502, "Payment provider request failed")

    try:
        body = response.json()
    except ValueError as exc:
        raise HTTPException(502, "Payment provider returned an invalid response") from exc

    if not body.get("status"):
        raise HTTPException(502, "Payment provider rejected the request")
    if not isinstance(body.get("data"), dict):
        raise HTTPException(502, "Payment provider returned incomplete checkout data")
    return body["data"]


def valid_webhook_signature(payload: bytes, signature: str | None) -> bool:
    if not signature or not get_settings().paystack_secret_key:
        return False
    expected = hmac.new(get_settings().paystack_secret_key.encode(), payload, hashlib.sha512).hexdigest()
    return hmac.compare_digest(expected, signature)
