# BloomAI Support Assistant

BloomAI Support provides signed-in customers and vendors with contextual help for orders, payments, refunds, fulfillment, account access and vendor listings.

## Safety model

- The assistant reads only the signed-in user's accessible marketplace context.
- It never changes payment, refund, fulfillment, account or inventory state.
- It never asks for passwords, OTPs, full card numbers, API keys or other secrets.
- Critical issues can be explicitly escalated by the user to BloomAI administrators.
- Escalations use the existing BloomAI notification pipeline. `system.critical.support` alerts are mandatory for administrators and use Resend email when transactional email is configured.
- If the external AI provider is unavailable or unconfigured, the assistant falls back to deterministic support guidance and current order-state summaries.

## Marketplace API endpoints

- `POST /api/v1/support/assistant`
- `POST /api/v1/support/escalate`

Both endpoints require an authenticated customer or vendor session.

## Production environment variables

The feature works without an external LLM, but AI-generated responses require:

```text
SUPPORT_AI_API_KEY=<provider key>
SUPPORT_AI_BASE_URL=https://openrouter.ai/api/v1
SUPPORT_AI_MODEL=google/gemini-2.0-flash-001
```

Existing notification/email variables remain in use:

```text
RESEND_API_KEY=<existing Resend key>
RESEND_FROM_EMAIL=<verified sender>
WEB_BASE_URL=https://bloomai-web-production.up.railway.app
```

Do not expose provider keys through Vite variables or browser JavaScript. `SUPPORT_AI_API_KEY` belongs only on the Marketplace API service.

## Production smoke test

After Railway deploys the API and web services:

1. Sign in as a customer or vendor.
2. Open the floating **Support** button.
3. Ask a normal order/refund question and confirm a context-aware response is returned.
4. Ask a critical test question such as `I think this payment is unauthorized` using a test account.
5. Click **Escalate to administrator**.
6. Confirm the participant receives `Support request escalated` and the administrator receives a `system.critical.support` notification. If administrator email delivery is configured, confirm the corresponding Resend message is delivered.

Do not use real card data, passwords, OTPs, API keys or other secrets in support tests.
