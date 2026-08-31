# BloomAI Global Marketplace

BloomAI is an AI-enabled botanical marketplace capstone by Kolapo Adedipe. The production system combines customer and vendor commerce, managed product and profile media, secure authentication, payment orchestration, a protected executive administration experience, persistent notifications, optional transactional-email delivery, independent flower inference and asynchronous event processing in a service-oriented monorepo.

[![CI](https://github.com/kadedipe/BloomAI-Global-Marketplace/actions/workflows/ci.yml/badge.svg)](https://github.com/kadedipe/BloomAI-Global-Marketplace/actions/workflows/ci.yml)

## Live production system

| Resource | Link | Purpose |
|---|---|---|
| BloomAI Web | [Open the production application](https://bloomai-web-production.up.railway.app) | Customer, vendor and AI Lab experience |
| Admin dashboard | [Open admin sign-in](https://bloomai-web-production.up.railway.app/admin-login.html) | Protected executive analytics and participant administration |
| Marketplace API | [Open API documentation](https://marketplace-api-production-c7cd.up.railway.app/docs) | Authentication, catalog, media, notification and payment APIs |
| Marketplace readiness | [Health endpoint](https://marketplace-api-production-c7cd.up.railway.app/health/ready) | Database-backed readiness check |
| AI Inference API | [AI readiness endpoint](https://ai-inference-api-production.up.railway.app/health/ready) | Verified model readiness |
| Source repository | [GitHub repository](https://github.com/kadedipe/BloomAI-Global-Marketplace) | Monorepo, CI/CD and engineering evidence |
| Agile board | [Trello product backlog](https://trello.com/invite/b/6a359b640166be0bf5636001/ATTIe8e1ab12cb2c5e1b5e4827fd4cc8145a9434255E/bloomai-global-marketplace-product-backlog-board) | Product backlog and three-sprint evidence |
| Recorded presentation | [Watch the 15–20 minute Capstone presentation](https://youtube.com/live/AffW_CxeEks?feature=share) | Product demonstration and engineering evidence |

## Demonstrated production capabilities

### Marketplace and identity

- Register and sign in as a customer or vendor using expiring JWT authentication in Secure HttpOnly cookies.
- Preserve authenticated browser sessions, log out safely and enforce role-aware customer, vendor and administrator authorization.
- Keep public administrator registration disabled; production administrators are provisioned through an idempotent server-side bootstrap workflow.
- Create, edit and delete vendor-owned products with immediate marketplace updates.
- Validate JPEG, PNG and WebP product uploads, store media in Cloudinary and render resilient placeholders.
- Allow customers and vendors to optionally upload, replace or remove a personal profile photo. Profile photos use validated Cloudinary-backed image storage and remain optional.
- Initialize Paystack hosted checkout from server-authoritative product prices and verify payment references.

### AI capability

- Identify flowers through an isolated 102-class MobileNetV3 Small inference service.
- Return five ranked predictions with confidence values through the production AI Lab.
- Verify the production model artifact by SHA-256 before readiness succeeds.

The production AI artifact is verified with SHA-256 `9ee2f29556562a14a666ad8345b850b7aa11d26dc2e73b16a735d4d33b515dc9`. Its recorded held-out accuracy is 95.24%, with 99.63% top-five accuracy. If the artifact is missing or invalid, the service fails readiness instead of returning fabricated classifications.

### Administration, analytics and segmentation

- Protect `/admin.html` behind a dedicated administrator authentication flow and backend `Role.admin` authorization.
- Display executive marketplace KPIs including gross revenue, average order value, checkout conversion, repeat-purchase rate, vendor/customer counts and geocoding coverage.
- Report monthly revenue, customer acquisition, category growth, inactive accounts and vendor performance rankings.
- Export administrator-protected CSV and PDF executive reports.
- Persist participant segmentation by organization size and category and expose an administrator profile editor for customer/vendor classification.
- Store structured participant location fields and verified latitude/longitude for precise geographic reporting.
- Render an interactive world marketplace map using stored participant coordinates, while retaining country-level fallback reporting for records that have not been geocoded.
- Import trusted verified geocoding data through a dry-run-first administrative workflow instead of fabricating coordinates from country names.

### Notifications

- Persist in-app notifications for customers, vendors and administrators.
- Generate event-driven notifications for account creation, listings, orders and payment-status changes.
- Show unread counts, notification history, mark-as-read and mark-all-read controls in both marketplace and administrator experiences.
- Provide an administrator-only test-notification facility for customer, vendor and admin roles without creating fake orders, payments or analytics activity.
- Let each user configure in-app notification categories for account activity, orders, payments, vendor activity and general system events.
- Keep critical administrator alerts mandatory even when general system notifications are disabled.
- Include opt-in transactional email delivery through Resend. Email delivery remains unavailable until the production sender/domain and Railway environment variables are configured; in-app notifications remain independent of provider availability.

### Production engineering

- Process versioned domain events through a private Redis-backed worker.
- Apply versioned Alembic migrations to Railway PostgreSQL before application startup.
- Monitor service liveness/readiness, Railway logs and optional Sentry telemetry.
- Build and test the monorepo through GitHub Actions, container checks, model-contract tests and supply-chain scanning.

## Architecture

| Service / dependency | Directory or provider | Responsibility | Exposure |
|---|---|---|---|
| BloomAI Web | `apps/web` | React customer, vendor, notification, profile-photo, administrator and AI Lab experience | Public |
| Marketplace API | `services/marketplace-api` | Identity, authorization, catalog, participant profiles, analytics, notifications, Cloudinary media and Paystack orchestration | Public |
| AI Inference API | `services/ai-api` | Image validation and MobileNetV3 inference | Public |
| Event Worker | `services/event-worker` | Asynchronous domain-event processing | Private |
| PostgreSQL | Railway managed | Users, participant profiles, products, orders, notifications and notification preferences | Private |
| Redis | Railway managed | Rate limiting, events and cache foundation | Private |
| Cloudinary | Managed SaaS | Product and optional customer/vendor profile image storage/CDN delivery | External |
| Paystack | Managed SaaS | Hosted payment checkout and verification | External |
| Resend | Managed SaaS | Optional transactional email delivery when configured | External |

The original training notebooks, dataset preparation and reproducible MobileNetV3 training code remain in `ai-services` as model-development provenance and are excluded from runtime containers.

## MSSE Faculty submission evidence

This repository maps the Quantic MSSE Capstone requirements to explicit evidence. The current implementation goes beyond the original recorded demonstration by adding administrator analytics, participant segmentation, verified geographic reporting, persistent notifications, notification preferences, optional email-delivery integration and customer/vendor profile photos. These additions are documented as post-recording production hardening and do not invalidate the recorded demonstration.

The presentation has been recorded and `quantic-grader` has been invited. The YouTube recording is linked below; Faculty’s specified Google Drive-hosted MP4/MOV copy remains the final strict-format verification item.

| Faculty requirement | Evidence | Status |
|---|---|---|
| Accessible, documented software repository | This README, service source, tests, contribution controls and PR history | Complete |
| Deployed web application link | [BloomAI production](https://bloomai-web-production.up.railway.app) | Complete |
| Agile task board | [Trello board](https://trello.com/invite/b/6a359b640166be0bf5636001/ATTIe8e1ab12cb2c5e1b5e4827fd4cc8145a9434255E/bloomai-global-marketplace-product-backlog-board) and [agile evidence](docs/AGILE-EVIDENCE.md) | Complete (user-validated) |
| At least three sprints | [Agile and sprint evidence](docs/AGILE-EVIDENCE.md) | Complete |
| Design, architecture and testing report | [Design and testing report](docs/DESIGN-AND-TESTING.md) | Complete |
| CI/CD and collaborative engineering | [GitHub Actions CI](.github/workflows/ci.yml), merged PR history and [production operations](docs/PRODUCTION_OPERATIONS.md) | Complete |
| AI tooling and model evidence | [AI tooling disclosure](docs/AI-TOOLING.md), `ai-services` and [production verification](docs/PRODUCTION-VERIFICATION.md) | Complete |
| Production marketplace capability | Authenticated customer/vendor marketplace, Cloudinary media, Paystack foundation and profile photos | Complete for implemented scope |
| Administration and reporting | Protected administrator bootstrap/sign-in, segmentation, executive analytics, CSV/PDF export and world map | Complete |
| Notification workflow | Persistent role-aware notifications, preferences and production-safe admin delivery testing | Complete |
| Transactional email foundation | Resend integration and opt-in preference support | Implemented; production provider configuration required |
| Final 15–20 minute demonstration | [Recorded presentation](https://youtube.com/live/AffW_CxeEks?feature=share) and [demonstration script](docs/DEMO-SCRIPT.md) | Recorded and linked; add the actual public-view Google Drive MP4/MOV URL to satisfy the Faculty hosting specification |
| Grader access | Repository collaborator settings | Complete — `quantic-grader` invited (user-confirmed) |
| Group agreement final page | Quantic submission dashboard | **External action if group-based:** submit privately; do not commit signatures or IDs |

### Post-recording production-hardening evidence

The following merged pull requests capture substantial improvements completed after the original Faculty evidence refresh:

- PR #14 — administrator reporting, analytics and participant segmentation.
- PR #15 — executive KPIs, trend analytics and downloadable CSV/PDF reporting.
- PR #16 — geocoded interactive world marketplace map with country fallback.
- PR #17 — trusted verified geocoding import workflow.
- PR #18/#19 — secure administrator bootstrap/sign-in and production CLI packaging.
- PR #20 — administrator participant profile editor.
- PR #21 — persistent in-app marketplace notifications.
- PR #22 — administrator-controlled production-safe notification testing.
- PR #23 — user notification preferences and mandatory critical administrator alerts.
- PR #24 — opt-in transactional email integration.
- PR #25 — optional customer and vendor profile photos.

### Submission index

- [Faculty compliance matrix](docs/CAPSTONE-COMPLIANCE.md)
- [Design and testing report](docs/DESIGN-AND-TESTING.md)
- [Agile and three-sprint evidence](docs/AGILE-EVIDENCE.md)
- [Final demonstration plan](docs/DEMO-SCRIPT.md)
- [AI tooling disclosure](docs/AI-TOOLING.md)
- [Production verification evidence](docs/PRODUCTION-VERIFICATION.md)
- [Production operations and recovery](docs/PRODUCTION_OPERATIONS.md)
- [Production completion checklist](docs/PRODUCTION-COMPLETION-CHECKLIST.md)

Before submitting, perform one final signed-out link check and supplement the YouTube presentation evidence with the public-view URL of the actual MP4/MOV uploaded to Google Drive. Keep the YouTube link as convenient secondary viewing evidence.

## Local development

```bash
cp .env.example .env
docker compose up --build
```

- Web: `http://localhost:5173`
- Marketplace API docs: `http://localhost:8000/docs`
- AI API docs: `http://localhost:8001/docs`

Run the quality checks:

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

Production secrets and environment-specific values remain in Railway. Key variables include:

| Service / capability | Variables |
|---|---|
| Marketplace API | `JWT_SECRET`, `CORS_ORIGINS`, `ENABLE_API_DOCS`, `SENTRY_DSN` |
| Product and profile media | `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`, `PRODUCT_IMAGE_MAX_BYTES` |
| Payments | `PAYSTACK_SECRET_KEY`, `PAYSTACK_CALLBACK_URL`, `PAYSTACK_CURRENCIES` |
| Transactional email | `RESEND_API_KEY`, `RESEND_FROM_EMAIL`, `WEB_BASE_URL` |
| AI API | `MODEL_GDRIVE_FILE_ID`, `MODEL_PATH`, `MODEL_SHA256`, `CORS_ORIGINS`, `SENTRY_DSN` |
| BloomAI Web | `VITE_API_URL`, `VITE_AI_API_URL` |

Never commit production credentials. See [.railway/README.md](.railway/README.md) and [production operations](docs/PRODUCTION_OPERATIONS.md) for deployment and recovery procedures.

## API example

```bash
export API="https://marketplace-api-production-c7cd.up.railway.app"
curl -X POST "$API/api/v1/auth/register" \
  -H 'content-type: application/json' \
  -d '{"email":"vendor@example.com","password":"strong-password","name":"Bloom Vendor","role":"vendor"}'
```

Use a unique test address and do not place real credentials in terminal recordings or committed files.

## Engineering controls

- Non-root minimal containers and environment-only secrets.
- Argon2 password hashing, short-lived JWTs, Secure HttpOnly cookies and role-based authorization.
- Public administrator registration disabled; administrator provisioning is explicit and server-side.
- Trusted-Origin CSRF validation and Redis-backed rate limiting.
- Typed request contracts, content-aware image validation and bounded uploads.
- Cloudinary CDN media with ownership-aware product updates and optional user profile-photo controls.
- Server-authoritative Paystack amounts, signed webhooks and idempotent verification.
- Preference-aware in-app notifications with administrator-only delivery testing and protected critical alerts.
- Transactional email kept opt-in and provider-gated so provider failure does not remove the in-app delivery path.
- Verified geocoding only; no fabricated participant coordinates.
- PostgreSQL readiness, process liveness and versioned Alembic migrations.
- Pull-request tests, frontend tests, staging E2E, container builds and vulnerability scanning.
- Code ownership, contribution policy, PR template and structured user stories.
- Railway IaC, private managed dependencies, Sentry integration and independent scaling.

## Honest limitations

The deployed release is a production-grade capstone/MVP, not a completed commercial marketplace. Paystack should remain in test mode until end-to-end payment, webhook, refund and reconciliation procedures are verified and the business account is approved. Vendor split payouts require KYC and settlement controls. Transactional email code is implemented, but live email requires a verified Resend sender/domain and production Railway configuration. Precise participant map markers require verified latitude/longitude and are intentionally absent when only a country is known. Inventory reservation, moderation workflows, accessibility/load testing, tested database restoration and multi-region disaster recovery remain roadmap work.

## License

MIT. Third-party packages retain their respective licenses.
