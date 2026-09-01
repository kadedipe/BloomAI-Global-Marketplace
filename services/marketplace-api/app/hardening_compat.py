from . import hardening, notifications


async def paystack_request_proxy(method: str, path: str, **kwargs):
    return await notifications.paystack_request(method, path, **kwargs)


hardening.paystack_request = paystack_request_proxy
