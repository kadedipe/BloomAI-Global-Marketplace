# Production commerce validation runbook

This runbook validates the complete BloomAI commerce lifecycle without exposing provider secrets or fabricating production state.

## 1. Railway configuration

Configure the Marketplace API service with the following values. Secrets must be entered directly in Railway, never committed to Git or pasted into tickets/chat.

Required core values:

- `ENVIRONMENT=production`
- `DATABASE_URL=${{ Postgres.DATABASE_PRIVATE_URL }}` (or the existing private Postgres reference)
- `REDIS_URL=${{ Redis.REDIS_PRIVATE_URL }}` (or the existing private Redis reference)
- `PUBLIC_API_BASE_URL=https://<marketplace-api-public-domain>`
- `WEB_BASE_URL=https://<bloomai-web-public-domain>`
- `CORS_ORIGINS=https://<bloomai-web-public-domain>`
- `PAYSTACK_SECRET_KEY=<Paystack secret key>`
- `PAYSTACK_CALLBACK_URL=https://<bloomai-web-public-domain>/<payment-callback-route>`
- `PAYSTACK_CURRENCIES=NGN`
- `ORDER_RESERVATION_MINUTES=30`
- `SHIPPING_FLAT_AMOUNT=<approved server-side shipping amount>`
- `SHIPPING_FREE_THRESHOLD=<approved threshold or 0>`
- `SALES_TAX_PERCENT=<approved tax rate or 0>`

Tracking integration:

- `AFTERSHIP_API_KEY=<AfterShip Tracking API key>`
- `AFTERSHIP_WEBHOOK_SECRET=<AfterShip Tracking webhook secret>`
- `AFTERSHIP_API_VERSION=2026-07`

The Event Worker must have both the production `DATABASE_URL` and `REDIS_URL`; reservation expiry now uses PostgreSQL as well as the existing event queue.

Do not invent shipping or tax values. Keep them at zero until the marketplace has an approved policy for the active jurisdiction.

## 2. Provider webhook destinations

After deployment, sign in as an administrator and call:

`GET /api/v1/admin/commerce/readiness`

The response returns the exact public webhook URLs without returning any secret value. Configure the providers with those URLs:

- Paystack: `https://<api-domain>/api/v1/payments/webhook`
- AfterShip Tracking: `https://<api-domain>/api/v1/shipping/aftership/webhook`

Paystack events are validated with the `x-paystack-signature` HMAC before they are processed. The commerce handler accepts `charge.success` plus refund lifecycle events (`refund.pending`, `refund.processing`, `refund.needs-attention`, `refund.failed`, and `refund.processed`).

AfterShip Tracking webhooks are validated using `aftership-hmac-sha256`. Enable shipment-status tracking updates and use the provider's test-webhook facility to confirm a 2xx response before a real shipment is used.

## 3. Readiness check

Run locally with production credentials supplied only through environment variables:

```bash
cd services/marketplace-api
export BLOOMAI_API_URL="https://<marketplace-api-public-domain>"
export BLOOMAI_WEB_ORIGIN="https://<bloomai-web-public-domain>"
export BLOOMAI_ADMIN_EMAIL="<admin-email>"
export BLOOMAI_ADMIN_PASSWORD="<admin-password>"
python scripts/validate_production_commerce.py
```

The command checks live/ready health, authenticates the administrator, and evaluates production database, HTTPS, Paystack, AfterShip, reservation, shipping, and tax configuration. It never prints the admin password, Paystack key, AfterShip key, webhook secret, or database URL.

If Paystack reports `mode: test`, complete the first lifecycle with Paystack test credentials. If it reports `mode: live`, use a deliberately controlled low-value product and account. Do not use an arbitrary customer's real order as a validation transaction.

## 4. Controlled lifecycle

Use dedicated customer and vendor validation accounts whose email inboxes you control. Use a dedicated low-value tracked product with a known starting inventory (for example, quantity 2). Record the product ID, starting inventory, order ID, and payment reference.

1. Customer opens the product and requests the server quote. Confirm subtotal, shipping, tax, total, and currency.
2. Customer submits structured checkout. Confirm inventory decreases by the reserved quantity and `reservation_expires_at` is populated.
3. Complete payment through Paystack. Confirm `/payments/{reference}/verify` and/or the signed Paystack `charge.success` webhook changes the order to paid, stores the provider transaction ID, clears the reservation flag, and leaves inventory consumed exactly once.
4. Confirm customer/vendor/admin in-app notifications and any enabled transactional email notifications.
5. Confirm the receipt endpoint becomes available and shows the same order total/currency.
6. Confirm executive analytics include the paid order and its revenue exactly once.
7. Vendor marks the order shipped with a controlled carrier and tracking number. When AfterShip is configured, confirm a provider tracking ID/status is stored.
8. Use AfterShip's test webhook or the controlled shipment to produce a tracking update. Confirm the buyer notification and tracking status update. A delivered event should move fulfillment to delivered and set `delivered_at`.
9. Customer requests a refund. Vendor/admin approves it. Administrator executes the Paystack refund.
10. Confirm Paystack refund webhook transitions eventually reconcile to `refund.processed`, `refund_status=refunded`, and `refund_processed_at` is present. Failed or needs-attention events must not be reported as a completed refund.

## 5. Automated evidence audit

After the lifecycle, run:

```bash
python scripts/validate_production_commerce.py --order-id <ORDER_ID> --output commerce-validation.json
```

The admin audit validates pricing arithmetic, reservation consumption, provider transaction presence, tracking requirements, delivery timestamps, refund timestamps, receipt availability, related notification evidence, and the current paid-order/revenue analytics totals. The command is read-only: it does not create, pay, ship, deliver, or refund an order.

A successful run exits `0`. Readiness or consistency failures exit `2` so the command can be used as a deployment gate.

## 6. Acceptance criteria

Production commerce validation is complete only when all of the following are true:

- Marketplace API and Event Worker deploy successfully and both can reach production Postgres.
- Commerce readiness has no blockers.
- Paystack and AfterShip test webhooks receive HTTP 2xx and invalid signatures receive HTTP 401.
- A controlled checkout reserves stock once; payment consumes the reservation once; no oversell or duplicate decrement occurs.
- Stored subtotal + shipping + tax equals total and matches the amount verified by Paystack.
- Receipt and executive analytics agree with the paid order.
- Shipment/tracking state and buyer notifications agree.
- Refund state is provider-reconciled and only `refund.processed` is treated as a completed webhook refund.
- The final admin commerce audit reports `consistent: true`.

Keep the generated validation JSON as release evidence, but inspect it before sharing outside the operations team because it contains order metadata even though it deliberately excludes secrets.
