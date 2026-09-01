from fastapi import APIRouter

from . import checkout_safe, hardening, manual_fulfillment

router = APIRouter(tags=["commerce-hardening"])
router.add_api_route("/orders/quote", hardening.order_quote, methods=["POST"], response_model=hardening.QuoteResponse)
router.add_api_route("/orders/checkout", checkout_safe.hardened_checkout, methods=["POST"], response_model=hardening.CheckoutResponse, status_code=201)
router.add_api_route("/orders/{order_id}/cancel", hardening.hardened_cancel, methods=["PATCH"])
router.add_api_route("/orders/{order_id}/pay", checkout_safe.hardened_retry_payment, methods=["POST"], response_model=hardening.CheckoutResponse)
router.add_api_route("/payments/initialize", hardening.deprecated_payment_initialize, methods=["POST"], status_code=410, deprecated=True)
router.add_api_route("/payments/{reference}/verify", hardening.hardened_verify_payment, methods=["GET"])
router.add_api_route("/orders/{order_id}/fulfillment", manual_fulfillment.hardened_fulfillment, methods=["PATCH"])
router.add_api_route("/payments/webhook", hardening.hardened_paystack_webhook, methods=["POST"], include_in_schema=False)
router.add_api_route("/shipping/aftership/webhook", hardening.aftership_webhook, methods=["POST"], include_in_schema=False)
