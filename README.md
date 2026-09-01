# BloomAI Global Marketplace

BloomAI is an AI-enabled botanical marketplace capstone by Kolapo Adedipe. The production system combines customer/vendor commerce, secure identity, inventory-aware checkout, Paystack payment and refund workflows, fulfillment, Cloudinary media, executive administration, persistent notifications, AI-assisted support with human escalation, independently verified flower inference, and asynchronous event processing in a service-oriented monorepo.

[![CI](https://github.com/kadedipe/BloomAI-Global-Marketplace/actions/workflows/ci.yml/badge.svg)](https://github.com/kadedipe/BloomAI-Global-Marketplace/actions/workflows/ci.yml)

## Live production system

| Resource | Link | Purpose |
|---|---|---|
| BloomAI Web | [Open production application](https://bloomai-web-production.up.railway.app/) | Customer/vendor marketplace, orders, notifications, support and AI Lab |
| Admin sign-in | [Open admin sign-in](https://bloomai-web-production.up.railway.app/admin-login.html) | Protected administrator authentication |
| Admin dashboard | [Open admin dashboard](https://bloomai-web-production.up.railway.app/admin.html) | Executive analytics, segmentation, refunds and Support Inbox |
| Marketplace API | [Open Swagger documentation](https://marketplace-api-production-c7cd.up.railway.app/docs) | Identity, commerce, support, notifications and administration APIs |
| Marketplace readiness | [Readiness endpoint](https://marketplace-api-production-c7cd.up.railway.app/health/ready) | Database-backed API readiness |
| AI Inference API | [AI readiness endpoint](https://ai-inference-api-production.up.railway.app/health/ready) | Checksum-gated MobileNetV3 readiness |
| GitHub repository | [BloomAI Global Marketplace](https://github.com/kadedipe/BloomAI-Global-Marketplace) | Source, tests, PR history and CI/CD evidence |
| GitHub Actions | [CI workflow](https://github.com/kadedipe/BloomAI-Global-Marketplace/actions/workflows/ci.yml) | Automated tests, builds, model contract and supply-chain checks |
| Pull requests | [Engineering history](https://github.com/kadedipe/BloomAI-Global-Marketplace/pulls?q=is%3Apr+is%3Aclosed) | Iterative engineering and review evidence |
| Trello board | [Product backlog](https://trello.com/invite/b/6a359b640166be0bf5636001/ATTIe8e1ab12cb2c5e1b5e4827fd4cc8145a9434255E/bloomai-global-marketplace-product-backlog-board) | Agile backlog and three-sprint evidence |
| Recorded presentation | [YouTube capstone presentation](https://youtube.com/live/AffW_CxeEks?feature=share) | 15–20 minute demonstration evidence |

## Production capabilities

### Identity, marketplace and media

- Customer and vendor registration/sign-in with expiring JWT authentication in Secure HttpOnly cookies.
- Role-aware authorization for customer, vendor and administrator operations.
- Public administrator registration is disabled; administrators are provisioned through a server-side bootstrap workflow.
- Vendor-owned product create, edit and delete operations with immediate marketplace updates.
- Validated JPEG/PNG/WebP product images and optional customer/vendor profile photos stored through Cloudinary.
- Inventory can be tracked, left untracked, set to sold out, or paused from checkout.

### Commerce, payments, fulfillment and refunds

- Server-authoritative order quotes and checkout; browser prices are never trusted as payment authority.
- Inventory reservation with expiry and restoration for cancelled/expired pending orders.
- Paystack hosted checkout, payment verification and signed webhook processing.
- Safe retry-payment flow using BloomAI-owned references and provider-response normalization.
- Order detail and receipt workflows.
- Fulfillment states: unfulfilled, processing, shipped, delivered and cancelled.
- Tracked shipping foundation with optional AfterShip integration.
- Legitimate no-tracking fulfillment for local delivery, vendor delivery, pickup and independent courier workflows; fake tracking numbers are never required.
- Customer refund requests, vendor/admin review, and administrator-only provider-backed Paystack refund execution.
- Refund provider status/reference reconciliation and protection against duplicate execution.
- Read-only administrator commerce readiness and order-audit tooling for production validation.

A complete production test order has exercised the lifecycle from checkout/payment through delivery and refund, demonstrating the integrated commerce path without manually changing payment/refund state in the database.

### AI flower identification

- Isolated 102-class MobileNetV3 Small inference service.
- Top-five predictions with confidence values in the production AI Lab.
- SHA-256 verification before model readiness succeeds.

Production model SHA-256: `9ee2f29556562a14a666ad8345b850b7aa11d26dc2e73b16a735d4d33b515dc9`.

Recorded held-out metrics: **95.24% test accuracy** and **99.63% top-five accuracy**. If the artifact is absent or invalid, readiness fails rather than returning fabricated classifications.

### Administration, analytics and geographic reporting

- Dedicated administrator sign-in and backend `Role.admin` enforcement.
- Executive KPIs: gross revenue, average order value, checkout conversion, repeat-purchase rate, active buyers, vendor/customer counts and geocoding coverage.
- Monthly revenue, customer acquisition, category growth, inactive-account detection and vendor performance ranking.
- Administrator-protected CSV/PDF reporting.
- Participant segmentation by organization size/category with an admin profile editor.
- Structured location fields plus verified latitude/longitude.
- Interactive world marketplace map with country-level fallback for participants awaiting coordinates.
- Trusted dry-run-first geocoding import; coordinates are never fabricated.
- Administrator refund operations for approved provider-backed refunds.

### Notifications and transactional communication

- Persistent in-app notifications for customers, vendors and administrators.
- Event-driven account, listing, order, payment, refund and support notifications.
- Unread counts, notification history, mark-read and mark-all-read controls.
- Administrator-only test notifications that do not create fake commerce activity.
- Per-user notification preferences with mandatory critical administrator alerts.
- Optional Resend transactional email while preserving in-app delivery if the email provider is unavailable.

### AI-assisted support and persistent support cases

BloomAI now includes a production support workflow for signed-in customers and vendors.

- Floating **BloomAI Support** assistant for orders, payments, refunds, delivery, listings and account issues.
- The assistant reads only marketplace context accessible to the signed-in participant.
- Critical payment/account/refund scenarios use deterministic safety responses rather than external-model speculation.
- The assistant never asks for passwords, OTPs, full card numbers, API keys or other secrets.
- Critical support defaults to the **latest relevant accessible order**, avoiding unnecessary multi-order data dumps.
- Full order history remains available when explicitly requested.
- Explicit human escalation creates a persistent support case and administrator notification.
- Cases store category, priority, status, linked order, assignment, timestamps and threaded participant/admin messages.
- Administrator **Support Inbox** supports filtering, assignment, replies and state transitions.
- Case states: `open`, `in_progress`, `waiting_on_user`, `resolved`, `closed`.
- Priorities: `normal`, `high`, `critical`.
- Admin replies notify participants; participant replies notify administrators; status changes notify participants.
- Resolved/closed cases are participant read-only until an administrator explicitly reopens them.
- Participant UI suppresses reply actions for resolved/closed cases.
- Critical support cases can automatically persist the latest relevant order association, e.g. `Order #6`.

Production validation has exercised the complete support lifecycle: critical assistant response → escalation → persistent case → admin notification → admin assignment/reply → participant reply → resolution → participant notification.

See [Support Assistant documentation](docs/support-assistant.md).

## Architecture

| Service / dependency | Directory/provider | Responsibility | Exposure |
|---|---|---|---|
| BloomAI Web | `apps/web` | Marketplace, vendor tools, orders, notifications, support, admin and AI Lab UI | Public |
| Marketplace API | `services/marketplace-api` | Identity, commerce, support, analytics, notifications, media and provider orchestration | Public |
| AI Inference API | `services/ai-api` | Image validation and MobileNetV3 inference | Public |
| Event Worker | `services/event-worker` | Asynchronous domain-event processing | Private |
| PostgreSQL | Railway managed | Users, products, orders, commerce state, notifications and support cases | Private |
| Redis | Railway managed | Rate limiting, events and cache foundation | Private |
| Cloudinary | Managed SaaS | Product/profile image storage and CDN | External |
| Paystack | Managed SaaS | Hosted checkout, verification and refunds | External |
| AfterShip | Optional managed SaaS | Tracked-shipping provider integration | External/optional |
| Resend | Managed SaaS | Optional transactional email | External/optional |
| OpenRouter-compatible AI | Optional provider | Non-critical support-assistant generation | External/optional |

The training notebooks, dataset preparation and reproducible MobileNetV3 training code remain in `ai-services` as model-development provenance and are excluded from runtime containers.

## Faculty submission evidence

This repository maps the Quantic MSSE Capstone requirements to explicit production evidence. The current production release goes substantially beyond the original recorded demonstration through administrator analytics, segmentation, geographic reporting, notifications, production commerce, fulfillment/refunds, AI-assisted support, persistent support cases and notification-driven human handoff.

| Faculty requirement | Evidence | Status |
|---|---|---|
| Accessible documented repository | README, source, tests, PR history and contribution controls | Complete |
| Deployed application | [BloomAI production](https://bloomai-web-production.up.railway.app/) | Complete |
| API evidence | [Marketplace API docs](https://marketplace-api-production-c7cd.up.railway.app/docs) | Complete |
| Agile task board | [Trello backlog](https://trello.com/invite/b/6a359b640166be0bf5636001/ATTIe8e1ab12cb2c5e1b5e4827fd4cc8145a9434255E/bloomai-global-marketplace-product-backlog-board) and [Agile evidence](docs/AGILE-EVIDENCE.md) | Complete |
| At least three sprints | [Agile evidence](docs/AGILE-EVIDENCE.md) | Complete |
| Design/testing report | [Design and testing](docs/DESIGN-AND-TESTING.md) | Complete |
| CI/CD | [GitHub Actions](https://github.com/kadedipe/BloomAI-Global-Marketplace/actions/workflows/ci.yml) and PR history | Complete |
| AI evidence | [AI tooling](docs/AI-TOOLING.md), `ai-services`, [production verification](docs/PRODUCTION-VERIFICATION.md) | Complete |
| Commerce | Quotes, checkout, Paystack verification, reservations, fulfillment and refunds | Production lifecycle validated |
| Administration/reporting | Protected admin, executive analytics, segmentation, exports, world map, refund operations | Complete |
| Notifications | Persistent role-aware notifications and preferences | Complete |
| Support workflow | AI-assisted support, persistent cases, human escalation and Support Inbox | Production lifecycle validated |
| Transactional email | Resend integration with in-app fallback | Provider/configuration dependent |
| 15–20 minute demo | [YouTube presentation](https://youtube.com/live/AffW_CxeEks?feature=share) and [demo script](docs/DEMO-SCRIPT.md) | Recorded; Faculty Google Drive MP4/MOV link still required if mandated |
| Grader access | Repository collaborator settings | `quantic-grader` invited (user-confirmed) |

### Post-recording production-hardening PR evidence

Key merged improvements include:

- [PR #14](https://github.com/kadedipe/BloomAI-Global-Marketplace/pull/14) — admin reporting/segmentation.
- [PR #15](https://github.com/kadedipe/BloomAI-Global-Marketplace/pull/15) — executive analytics and reports.
- [PR #16](https://github.com/kadedipe/BloomAI-Global-Marketplace/pull/16) — interactive world map.
- [PR #17](https://github.com/kadedipe/BloomAI-Global-Marketplace/pull/17) — verified geocoding import.
- [PR #18](https://github.com/kadedipe/BloomAI-Global-Marketplace/pull/18) / [#19](https://github.com/kadedipe/BloomAI-Global-Marketplace/pull/19) — secure admin bootstrap/sign-in and production packaging.
- [PR #20](https://github.com/kadedipe/BloomAI-Global-Marketplace/pull/20) — participant profile editor.
- [PR #21](https://github.com/kadedipe/BloomAI-Global-Marketplace/pull/21)–[#25](https://github.com/kadedipe/BloomAI-Global-Marketplace/pull/25) — persistent notifications, testing, preferences, transactional email and profile photos.
- [PR #27](https://github.com/kadedipe/BloomAI-Global-Marketplace/pull/27)–[#31](https://github.com/kadedipe/BloomAI-Global-Marketplace/pull/31) — marketplace ordering, inventory/fulfillment, commerce hardening, production validation and optional shipping-provider readiness.
- [PR #32](https://github.com/kadedipe/BloomAI-Global-Marketplace/pull/32)–[#38](https://github.com/kadedipe/BloomAI-Global-Marketplace/pull/38) — checkout/auth/provider/CORS reliability and Paystack response/reference hardening.
- [PR #39](https://github.com/kadedipe/BloomAI-Global-Marketplace/pull/39) — legitimate local/no-tracking fulfillment.
- [PR #40](https://github.com/kadedipe/BloomAI-Global-Marketplace/pull/40) — administrator refund execution workflow.
- [PR #41](https://github.com/kadedipe/BloomAI-Global-Marketplace/pull/41)–[#44](https://github.com/kadedipe/BloomAI-Global-Marketplace/pull/44) — AI support assistant, grounding/safety hardening, reasoning-leak prevention and deterministic critical support.
- [PR #45](https://github.com/kadedipe/BloomAI-Global-Marketplace/pull/45) — persistent support cases and notification-driven Support Inbox.
- [PR #46](https://github.com/kadedipe/BloomAI-Global-Marketplace/pull/46) — latest-order support context, linked-order escalation and resolved-case reply controls.

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
```

- Web: `http://localhost:5173`
- Marketplace API docs: `http://localhost:8000/docs`
- AI API docs: `http://localhost:8001/docs`

```bash
make test
make lint
```

## Railway production deployment

Railway Infrastructure as Code is defined in `.railway/railway.ts` and provisions independently deployable services, PostgreSQL and Redis.

```bash
npm --prefix .railway install
railway login
railway link
railway config plan
railway config apply
```

Important environment-variable groups include:

| Capability | Variables |
|---|---|
| Marketplace API | `JWT_SECRET`, `CORS_ORIGINS`, `ENABLE_API_DOCS`, `SENTRY_DSN` |
| Media | `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`, `PRODUCT_IMAGE_MAX_BYTES` |
| Paystack | `PAYSTACK_SECRET_KEY`, `PAYSTACK_CALLBACK_URL`, `PAYSTACK_CURRENCIES` |
| Email | `RESEND_API_KEY`, `RESEND_FROM_EMAIL`, `WEB_BASE_URL` |
| AI support | `SUPPORT_AI_API_KEY`, `SUPPORT_AI_BASE_URL`, `SUPPORT_AI_MODEL` |
| Optional tracking | `AFTERSHIP_API_KEY`, `AFTERSHIP_WEBHOOK_SECRET`, `AFTERSHIP_API_VERSION` |
| AI inference | `MODEL_GDRIVE_FILE_ID`, `MODEL_PATH`, `MODEL_SHA256`, `CORS_ORIGINS`, `SENTRY_DSN` |
| Web | `VITE_API_URL`, `VITE_AI_API_URL` |

Never commit production credentials.

## Engineering controls

- Non-root minimal containers and environment-only secrets.
- Argon2 password hashing, Secure HttpOnly cookies and role-based authorization.
- Public administrator registration disabled.
- Trusted-Origin CSRF validation and Redis-backed rate limiting.
- Typed request contracts and bounded/content-aware image validation.
- Server-authoritative commerce amounts and inventory reservation.
- Signed payment/shipping webhooks and provider-aware failure handling.
- Provider-backed admin-only refund execution rather than direct database payment manipulation.
- No fabricated geocoding coordinates or shipment tracking data.
- Deterministic critical-support safety path and explicit human escalation.
- Persistent support-case audit trail with participant/admin access controls.
- Preference-aware notifications with mandatory critical administrator alerts.
- PostgreSQL readiness, Alembic migrations, CI tests, container builds and vulnerability scanning.

## Current limitations

BloomAI remains a production-grade capstone/MVP rather than a finished commercial marketplace. Live-money operation still requires approved business/provider configuration, KYC/settlement controls and operational reconciliation. AfterShip is optional; legitimate no-tracking fulfillment remains supported. Transactional email depends on a verified Resend sender/domain. Precise map markers require verified coordinates. Broader moderation, accessibility/load testing, tested database restoration and multi-region disaster recovery remain roadmap work.

For Faculty submission, perform a final signed-out link check and add the public-view Google Drive URL for the actual MP4/MOV recording if the Faculty hosting specification requires it. Keep the YouTube link as secondary viewing evidence.

## License

MIT. Third-party packages retain their respective licenses.
