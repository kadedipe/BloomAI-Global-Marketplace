# BloomAI Global Marketplace

> **Public Domain:** https://bloomaiglobalmarketplace.com/

BloomAI is an AI-enabled botanical marketplace capstone by Kolapo Adedipe. The production system combines customer/vendor commerce, secure identity, inventory-aware checkout, Paystack payment and refund workflows, fulfillment, Cloudinary media, executive administration, persistent notifications, AI-assisted support with human escalation, independently verified flower inference, and asynchronous event processing in a service-oriented monorepo.

## Public access

The canonical public-facing domain for BloomAI Global Marketplace is **https://bloomaiglobalmarketplace.com/**. The Railway application URL remains available as the underlying production deployment endpoint.

| Resource | Link |
|---|---|
| Public Domain | [BloomAI Global Marketplace](https://bloomaiglobalmarketplace.com/) |
| Railway Production Web | [Production deployment](https://bloomai-web-production.up.railway.app/) |
| Admin sign-in | [Administrator sign-in](https://bloomai-web-production.up.railway.app/admin-login.html) |
| Admin dashboard | [Administrator dashboard](https://bloomai-web-production.up.railway.app/admin.html) |
| Marketplace API | [Swagger documentation](https://marketplace-api-production-c7cd.up.railway.app/docs) |
| Marketplace readiness | [API readiness](https://marketplace-api-production-c7cd.up.railway.app/health/ready) |
| AI readiness | [AI inference readiness](https://ai-inference-api-production.up.railway.app/health/ready) |
| GitHub repository | [Source repository](https://github.com/kadedipe/BloomAI-Global-Marketplace) |
| GitHub Actions | [CI workflow](https://github.com/kadedipe/BloomAI-Global-Marketplace/actions/workflows/ci.yml) |
| Trello board | [Product backlog](https://trello.com/invite/b/6a359b640166be0bf5636001/ATTIe8e1ab12cb2c5e1b5e4827fd4cc8145a9434255E/bloomai-global-marketplace-product-backlog-board) |
| Recorded presentation | [YouTube capstone presentation](https://youtube.com/live/AffW_CxeEks?feature=share) |

## Production capabilities

BloomAI includes secure customer/vendor identity, vendor product management, Cloudinary media, inventory-aware server-authoritative checkout, Paystack payment verification and provider-backed refunds, tracked and legitimate no-tracking fulfillment, persistent notifications, executive analytics, participant segmentation, verified geographic reporting, and an AI-assisted support workflow with persistent human escalation.

### AI flower identification

BloomAI Vision uses an isolated 102-class MobileNetV3 Small inference service and returns top-five predictions. The production model artifact is checksum-gated with SHA-256 `9ee2f29556562a14a666ad8345b850b7aa11d26dc2e73b16a735d4d33b515dc9`. Recorded held-out performance is **95.24% test accuracy** and **99.63% top-five accuracy**.

### Commerce and fulfillment

Commerce uses server-authoritative quotes and prices, inventory reservation and expiry, Paystack hosted checkout and verification, safe payment retry, order receipts, fulfillment states, optional tracked shipping, legitimate local/vendor/pickup/independent-courier delivery without fabricated tracking, customer refund requests, vendor/admin review and administrator-only Paystack refund execution.

A production test order has exercised checkout/payment, delivery and refund through the integrated application/provider lifecycle rather than direct database state changes.

### Administration and analytics

The protected administrator experience includes executive KPIs, revenue/customer trends, vendor performance, CSV/PDF reporting, participant segmentation, verified-coordinate geographic reporting, interactive world mapping, refund operations, notification administration and a persistent Support Inbox.

### Notifications and support

BloomAI persists role-aware in-app notifications and preferences, with optional Resend email delivery. Signed-in customers/vendors can use BloomAI Support for orders, payments, refunds, delivery, listings and account issues. Critical issues use deterministic safety responses, default to the latest relevant accessible order, and require explicit participant escalation. Escalation creates a persistent support case with linked order, priority/status, threaded messages, administrator notifications and human follow-up. Resolved/closed cases are participant read-only until an administrator explicitly reopens them.

## Architecture

| Component | Responsibility |
|---|---|
| `apps/web` | Marketplace, vendor tools, orders, notifications, support, administration and AI Lab UI |
| `services/marketplace-api` | Identity, commerce, support, analytics, notifications, media and provider orchestration |
| `services/ai-api` | Image validation and MobileNetV3 inference |
| `services/event-worker` | Asynchronous domain-event processing |
| PostgreSQL | Marketplace, commerce, notification and support-case persistence |
| Redis | Rate limiting, events and cache foundation |
| Cloudinary | Product/profile media |
| Paystack | Checkout, verification and refunds |
| AfterShip | Optional tracked-shipping integration |
| Resend | Optional transactional email |
| OpenRouter-compatible provider | Optional non-critical AI support generation |

## Faculty submission evidence

The canonical deployed application link for Faculty submission is now the **BloomAI public domain: https://bloomaiglobalmarketplace.com/**. The Railway URL is retained as deployment/operations evidence.

| Faculty requirement | Evidence | Status |
|---|---|---|
| Public deployed application | [https://bloomaiglobalmarketplace.com/](https://bloomaiglobalmarketplace.com/) | Complete |
| Underlying Railway deployment | [Railway production web](https://bloomai-web-production.up.railway.app/) | Complete |
| Repository | [GitHub](https://github.com/kadedipe/BloomAI-Global-Marketplace) | Complete |
| API evidence | [Marketplace API docs](https://marketplace-api-production-c7cd.up.railway.app/docs) | Complete |
| Agile evidence | [Trello backlog](https://trello.com/invite/b/6a359b640166be0bf5636001/ATTIe8e1ab12cb2c5e1b5e4827fd4cc8145a9434255E/bloomai-global-marketplace-product-backlog-board) and [Agile evidence](docs/AGILE-EVIDENCE.md) | Complete |
| Design/testing | [Design and testing report](docs/DESIGN-AND-TESTING.md) | Complete |
| CI/CD | [GitHub Actions](https://github.com/kadedipe/BloomAI-Global-Marketplace/actions/workflows/ci.yml) | Complete |
| AI evidence | [AI tooling](docs/AI-TOOLING.md) and [production verification](docs/PRODUCTION-VERIFICATION.md) | Complete |
| Commerce lifecycle | Checkout, payment, fulfillment and refund | Production lifecycle validated |
| Support workflow | AI assistance, persistent cases, human escalation and Support Inbox | Production lifecycle validated |
| Recorded demo | [YouTube presentation](https://youtube.com/live/AffW_CxeEks?feature=share) | Recorded; add Faculty-required Google Drive MP4/MOV URL if applicable |

## Submission index

- [Faculty compliance matrix](docs/CAPSTONE-COMPLIANCE.md)
- [Design and testing report](docs/DESIGN-AND-TESTING.md)
- [Agile and sprint evidence](docs/AGILE-EVIDENCE.md)
- [Final demonstration plan](docs/DEMO-SCRIPT.md)
- [AI tooling disclosure](docs/AI-TOOLING.md)
- [Production verification](docs/PRODUCTION-VERIFICATION.md)
- [Production operations](docs/PRODUCTION_OPERATIONS.md)
- [Production completion checklist](docs/PRODUCTION-COMPLETION-CHECKLIST.md)
- [Commerce fulfillment](docs/COMMERCE-FULFILLMENT.md)
- [Commerce hardening](docs/COMMERCE-HARDENING.md)
- [Support Assistant](docs/support-assistant.md)
- [Administrator access](docs/admin-access.md)
- [Verified geocoding import](docs/geocoding-import.md)

## Local development

```bash
cp .env.example .env
docker compose up --build
make test
make lint
```

## Production deployment

Railway Infrastructure as Code is defined in `.railway/railway.ts`. Production credentials and provider secrets remain environment-only and must never be committed.

## Engineering controls

BloomAI uses Secure HttpOnly authentication cookies, role-based authorization, disabled public administrator registration, Trusted-Origin CSRF validation, Redis-backed rate limiting, server-authoritative commerce values, signed provider webhooks, provider-backed refunds, validated media, verified geocoding only, versioned Alembic migrations, automated tests, container builds and supply-chain scanning.

## Honest limitations

BloomAI is a production-grade capstone/MVP rather than a completed commercial marketplace. Optional external capabilities such as live transactional email and tracked-shipping providers depend on their production configuration. Precise map markers require verified coordinates. Faculty-specific external submission items, including a Google Drive-hosted MP4/MOV if required, remain separate from repository implementation.

## License

MIT. Third-party packages retain their respective licenses.
