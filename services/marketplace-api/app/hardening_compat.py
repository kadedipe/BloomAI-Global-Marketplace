from . import hardening, notifications


async def paystack_request_proxy(method: str, path: str, **kwargs):
    if method == "GET" and path.startswith("/transaction/verify/"):
        from . import main

        return await main.paystack_request(method, path, **kwargs)
    return await notifications.paystack_request(method, path, **kwargs)


hardening.paystack_request = paystack_request_proxy
