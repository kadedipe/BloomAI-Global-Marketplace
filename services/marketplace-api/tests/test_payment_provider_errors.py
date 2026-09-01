import httpx
import pytest
from fastapi import HTTPException

from app import payments


@pytest.mark.asyncio
async def test_paystack_transport_failure_becomes_http_502(monkeypatch):
    monkeypatch.setenv("PAYSTACK_SECRET_KEY", "sk_test_example")
    monkeypatch.setenv("PAYSTACK_CALLBACK_URL", "https://example.com/payment/callback")
    payments.get_settings.cache_clear()

    async def fail_request(self, method, path, **kwargs):
        request = httpx.Request(method, f"https://api.paystack.co{path}")
        raise httpx.ConnectError("provider unavailable", request=request)

    monkeypatch.setattr(httpx.AsyncClient, "request", fail_request)

    with pytest.raises(HTTPException) as exc_info:
        await payments.request("POST", "/transaction/initialize", json={"amount": 100})

    assert exc_info.value.status_code == 502
    assert exc_info.value.detail == "Payment provider is temporarily unreachable"

    payments.get_settings.cache_clear()
