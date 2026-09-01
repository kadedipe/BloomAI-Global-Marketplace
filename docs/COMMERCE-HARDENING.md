# BloomAI commerce hardening

This stage hardens the customer/vendor order lifecycle beyond the initial checkout and fulfillment implementation.

## Reservation lifecycle

Tracked inventory is reserved when `POST /api/v1/orders/checkout` succeeds. Reservations receive `reservation_expires_at` using `ORDER_RESERVATION_MINUTES` (default 30). The event worker releases expired inventory and cancels unpaid abandoned orders. API checkout/quote operations also perform idempotent expiry cleanup so stale reservations do not block active buyers.

The checkout, retry and cancellation paths acquire database row locks for tracked products/orders. On PostgreSQL this serializes competing stock mutations and prevents two simultaneous buyers from both consuming the same final unit.

## Checkout pricing

`POST /api/v1/orders/quote` is the server-side pricing authority. The checkout stores subtotal, shipping, tax and total and sends only that server-computed total to Paystack.

Configuration:

- `SHIPPING_FLAT_AMOUNT` — flat shipping amount in the listing currency; default `0`.
- `SHIPPING_FREE_THRESHOLD` — subtotal at or above which shipping is free; `0` disables the threshold.
- `SALES_TAX_PERCENT` — percentage applied to merchandise subtotal; default `0`.

These are deliberately configuration-driven baseline rules. They do not claim jurisdiction-specific tax compliance; production operators must configure appropriate rates or replace the pricing policy with a tax/rating provider before entering jurisdictions that require it.

## Payment entry point

`POST /api/v1/payments/initialize` is retired and returns HTTP 410. All new purchases must use the structured `/api/v1/orders/checkout` endpoint so delivery details, pricing, reservation and inventory controls cannot be bypassed.

## Shipment tracking

When a paid order is marked shipped, BloomAI stores carrier and tracking number and, when `AFTERSHIP_API_KEY` is configured, registers the shipment with AfterShip Tracking API. `POST /api/v1/shipping/aftership/webhook` accepts signed tracking updates and updates the stored tracking state. A delivered tracking event advances a paid shipment to delivered.

Required production settings for automatic tracking:

- `AFTERSHIP_API_KEY`
- `AFTERSHIP_WEBHOOK_SECRET`
- optional `AFTERSHIP_API_VERSION` (default `2026-07`)

Configure AfterShip to send tracking webhooks to `/api/v1/shipping/aftership/webhook` on the Marketplace API public origin.

## Refund reconciliation

The hardened Paystack webhook processes both successful charges and Paystack refund lifecycle events. Supported refund events are `refund.pending`, `refund.processing`, `refund.needs-attention`, `refund.failed` and `refund.processed`. The order keeps both BloomAI's refund workflow status and the latest provider event/reference. `refund.processed` is the only webhook event that automatically records the refund as completed.

Paystack webhook signatures remain mandatory. Vendor approval still does not directly mark money as returned; provider reconciliation remains authoritative.

## Event worker production requirement

The event worker now requires `DATABASE_URL` in addition to `REDIS_URL` for reservation expiry. `RESERVATION_CLEANUP_INTERVAL_SECONDS` defaults to 60 seconds. The cleanup uses PostgreSQL `FOR UPDATE SKIP LOCKED` and is idempotent, so overlapping worker/API cleanup cannot restore the same reservation twice.
