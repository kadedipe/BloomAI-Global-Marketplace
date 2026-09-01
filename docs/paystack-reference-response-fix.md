# Paystack checkout response reference fix

Production Sentry reported `CheckoutResponse() got multiple values for keyword argument 'reference'` on `POST /api/v1/orders/{order_id}/pay`.

Paystack transaction initialization returns its own `reference` field in the provider payload. BloomAI was also passing the canonical order `reference` explicitly while expanding the entire provider payload with `**data`, causing Python to receive the same keyword twice.

The fix now extracts only `authorization_url` and `access_code` from Paystack initialization data and keeps BloomAI's order reference authoritative. Both new checkout and existing-order `Pay now` use the same safe response construction. Provider responses missing an authorization URL or access code fail before the authoritative database commit.

Regression coverage includes provider data containing `reference` for both `POST /api/v1/orders/checkout` and `POST /api/v1/orders/{order_id}/pay`.
