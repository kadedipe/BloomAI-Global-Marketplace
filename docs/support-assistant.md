# BloomAI Support Assistant and Support Cases

BloomAI Support provides signed-in customers and vendors with contextual help for orders, payments, refunds, fulfillment, account access and vendor listings. Critical issues use deterministic safety guidance and can be explicitly escalated into persistent administrator-managed support cases.

## Production links

- Web: https://bloomai-web-production.up.railway.app/
- Admin sign-in: https://bloomai-web-production.up.railway.app/admin-login.html
- Admin dashboard / Support Inbox: https://bloomai-web-production.up.railway.app/admin.html
- Marketplace API docs: https://marketplace-api-production-c7cd.up.railway.app/docs
- Marketplace readiness: https://marketplace-api-production-c7cd.up.railway.app/health/ready

## Safety model

- The assistant reads only marketplace context accessible to the signed-in participant.
- It never changes payment, refund, fulfillment, account or inventory state.
- It never asks for passwords, OTPs, full card numbers, API keys or other secrets.
- Critical payment/refund/account issues use deterministic responses and bypass external-model speculation.
- Critical responses default to the latest relevant accessible order rather than dumping unrelated order history.
- Full order history is used only when the participant explicitly requests it.
- Human escalation is explicit; the assistant does not silently create cases.
- External AI-provider failure falls back to deterministic support guidance.
- Reasoning-like/internal-analysis output is rejected rather than exposed to the participant.

## Persistent support cases

Explicit escalation creates a persistent case with:

- case ID;
- participant and role;
- category and priority;
- status;
- optional linked order;
- assignment;
- creation/update timestamps;
- threaded participant/admin messages.

Statuses: `open`, `in_progress`, `waiting_on_user`, `resolved`, `closed`.

Priorities: `normal`, `high`, `critical`.

Administrators manage cases from the **Support Inbox** in `/admin.html`. Admin replies notify the participant. Participant replies notify administrators. Status changes notify the participant. Critical cases use the mandatory critical-notification path.

Resolved and closed cases are participant read-only until an administrator explicitly reopens them. The backend enforces this rule and the participant UI suppresses reply actions for resolved/closed cases.

## Order association

When a critical request does not explicitly identify an order, BloomAI selects the latest relevant order accessible to the signed-in participant and returns that `order_id` with the assistant response. If the participant escalates, the support case persists the same order association. This keeps the case focused while preserving the ability to request broader history explicitly.

## API surface

The production API documentation is available at:

https://marketplace-api-production-c7cd.up.railway.app/docs

Support routes include the assistant/escalation flow plus participant/admin case operations for listing cases, replying, assignment and status updates. All routes are protected by authenticated role checks appropriate to participant or administrator access.

## Optional external AI configuration

The feature works without an external LLM. Non-critical AI-generated responses use OpenAI-compatible configuration when enabled:

```text
SUPPORT_AI_API_KEY=<provider key>
SUPPORT_AI_BASE_URL=https://openrouter.ai/api/v1
SUPPORT_AI_MODEL=google/gemini-2.0-flash-001
```

Existing notification/email configuration remains available:

```text
RESEND_API_KEY=<existing Resend key>
RESEND_FROM_EMAIL=<verified sender>
WEB_BASE_URL=https://bloomai-web-production.up.railway.app
```

Never expose provider keys through Vite variables or browser JavaScript. `SUPPORT_AI_API_KEY` belongs only on the Marketplace API service.

## Validated production lifecycle

The production workflow has been exercised end to end:

1. Sign in as a customer or vendor.
2. Open **Support**.
3. Submit a critical test concern such as `I think a payment on my account may be unauthorized.`
4. Confirm the deterministic response shows only the latest relevant order context.
5. Click **Escalate to administrator**.
6. Confirm a persistent `Support case #...` is created and the linked order is retained.
7. Open **My support cases** and verify the case/status.
8. Sign in as administrator and open **Support Inbox**.
9. Assign the case, reply and move it through the required state.
10. Confirm the participant receives the reply/status notification.
11. Have the participant reply while the case is active and confirm the administrator receives the update.
12. Resolve the case and confirm the participant reply action disappears.
13. Reopen only when further participant conversation is required.

Do not use real card data, passwords, OTPs, API keys or other secrets in support tests.
