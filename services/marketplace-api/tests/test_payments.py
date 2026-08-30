import hashlib
import hmac

from app.config import get_settings
from app.payments import valid_webhook_signature


def test_paystack_webhook_signature_is_verified(monkeypatch):
    monkeypatch.setenv("PAYSTACK_SECRET_KEY", "test_secret")
    get_settings.cache_clear()
    payload = b'{"event":"charge.success"}'
    signature = hmac.new(b"test_secret", payload, hashlib.sha512).hexdigest()
    assert valid_webhook_signature(payload, signature)
    assert not valid_webhook_signature(payload + b"x", signature)
    get_settings.cache_clear()
