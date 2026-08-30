# BloomAI Global Marketplace

BloomAI is an AI-enabled botanical marketplace capstone by Kolapo Adedipe. The production system combines a vendor marketplace, managed product media, secure authentication, payment orchestration, independent flower inference and asynchronous event processing in a service-oriented monorepo.

[![CI](https://github.com/kadedipe/BloomAI-Global-Marketplace/actions/workflows/ci.yml/badge.svg)](https://github.com/kadedipe/BloomAI-Global-Marketplace/actions/workflows/ci.yml)

## Live production system

| Resource | Link | Purpose |
|---|---|---|
| BloomAI Web | [Open the production application](https://bloomai-web-production.up.railway.app) | Customer, vendor and AI Lab experience |
| Marketplace API | [Open API documentation](https://marketplace-api-production-c7cd.up.railway.app/docs) | Authentication, catalog, media and payment APIs |
| Marketplace readiness | [Health endpoint](https://marketplace-api-production-c7cd.up.railway.app/health/ready) | Database-backed readiness check |
| AI Inference API | [AI readiness endpoint](https://ai-inference-api-production.up.railway.app/health/ready) | Verified model readiness |
| Source repository | [GitHub repository](https://github.com/kadedipe/BloomAI-Global-Marketplace) | Monorepo, CI/CD and engineering evidence |
| Agile board | [Trello product backlog](https://trello.com/invite/b/6a359b640166be0bf5636001/ATTIe8e1ab12cb2c5e1b5e4827fd4cc8145a9434255E/bloomai-global-marketplace-product-backlog-board) | Product backlog and sprint evidence |

## Demonstrated production capabilities

- Register and sign in as a customer or vendor using expiring JWT authentication in Secure HttpOnly cookies.
- Preserve authenticated browser sessions, log out safely and enforce vendor-only operations.
- Create, edit and delete vendor-owned products with immediate marketplace updates.
- Validate JPEG, PNG and WebP uploads, store product media in Cloudinary and render resilient placeholders.
- Initialize Paystack hosted checkout from server-authoritative product prices and verify payment references.
- Identify flowers through an isolated 102-class MobileNetV3 Small service and return five ranked predictions.
- Process versioned domain events through a private Redis-backed worker.
- Apply versioned Alembic migrations to Railway PostgreSQL before application startup.
- Monitor service liveness/readiness, Railway logs and Sentry telemetry.
- Build and test the monorepo through GitHub Actions, container checks and supply-chain scanning.

The production AI artifact is verified with SHA-256 `9ee2f29556562a14a666ad8345b850b7aa11d26dc2e73b16a735d4d33b515dc9`. Its recorded held-out accuracy is 95.24%, with 99.63% top-five accuracy. If the artifact is missing or invalid, the service fails readiness instead of returning fabricated classifications.

## Architecture

| Service | Directory | Responsibility | Exposure |
|---|---|---|---|
| BloomAI Web | `apps/web` | React customer, vendor and AI Lab experience | Public |
| Marketplace API | `services/marketplace-api` | Identity, authorization, catalog, Cloudinary media and Paystack orchestration | Public |
| AI Inference API | `services/ai-api` | Image validation and MobileNetV3 inference | Public |
| Event Worker | `services/event-worker` | Asynchronous domain-event processing | Private |
| PostgreSQL | Railway managed | Users, products and orders | Private |
| Redis | Railway managed | Rate limiting, events and cache foundation | Private |
| Cloudinary | Managed SaaS | Product image storage and CDN delivery | External |
| Paystack | Managed SaaS | Hosted payment checkout and verification | External |

The original training notebooks, dataset preparation and reproducible MobileNetV3 training code remain in `ai-services` as model-development provenance and are excluded from runtime containers.

## MSSE Faculty submission evidence

This repository maps the Quantic MSSE Capstone requirements to explicit evidence. Items marked **External action** must be completed outside source control before submission.

| Faculty requirement | Evidence | Status |
|---|---|---|
| Accessible, documented software repository | This README, service source, tests and contribution controls | Complete |
| Deployed web application link | [BloomAI production](https://bloomai-web-production.up.railway.app) | Complete |
| Agile task board | [Trello board](https://trello.com/invite/b/6a359b640166be0bf5636001/ATTIe8e1ab12cb2c5e1b5e4827fd4cc8145a9434255E/bloomai-global-marketplace-product-backlog-board) and [agile evidence](docs/AGILE-EVIDENCE.md) | Verify public access and update all stories |
| At least three sprints | [Agile and sprint evidence](docs/AGILE-EVIDENCE.md) | Documented; add real meeting/demo links where available |
| Design, architecture and testing report | [Design and testing report](docs/DESIGN-AND-TESTING.md) | Complete |
| CI/CD and collaborative engineering | [GitHub Actions CI](.github/workflows/ci.yml), PR history and [production operations](docs/PRODUCTION_OPERATIONS.md) | Complete |
| AI tooling and model evidence | [AI tooling disclosure](docs/AI-TOOLING.md), `ai-services` and [production verification](docs/PRODUCTION-VERIFICATION.md) | Complete |
| Final 15–20 minute demonstration | [Demonstration script](docs/DEMO-SCRIPT.md) | **External action:** record one MP4 and add its public-view Google Drive link here |
| Grader access | Repository collaborator settings | **External action:** invite GitHub user `quantic-grader` |
| Group agreement final page | Quantic submission dashboard | **External action if group-based:** submit privately; do not commit signatures or IDs |

### Submission index

- [Faculty compliance matrix](docs/CAPSTONE-COMPLIANCE.md)
- [Design and testing report](docs/DESIGN-AND-TESTING.md)
- [Agile and three-sprint evidence](docs/AGILE-EVIDENCE.md)
- [Final demonstration plan](docs/DEMO-SCRIPT.md)
- [AI tooling disclosure](docs/AI-TOOLING.md)
- [Production verification evidence](docs/PRODUCTION-VERIFICATION.md)
- [Production operations and recovery](docs/PRODUCTION_OPERATIONS.md)
- [Production completion checklist](docs/PRODUCTION-COMPLETION-CHECKLIST.md)

Before submitting, verify every link in a signed-out browser, bring the Trello board up to date, add `quantic-grader`, complete the rehearsal, record the final demonstration and replace the pending video statement above with the public-view Google Drive URL.

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

| Service | Variables |
|---|---|
| Marketplace API | `JWT_SECRET`, `CORS_ORIGINS`, `ENABLE_API_DOCS`, `SENTRY_DSN` |
| Product media | `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`, `PRODUCT_IMAGE_MAX_BYTES` |
| Payments | `PAYSTACK_SECRET_KEY`, `PAYSTACK_CALLBACK_URL` |
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

- Non-root minimal containers and environment-only secrets
- Argon2 password hashing, short-lived JWTs, Secure HttpOnly cookies and role-based authorization
- Trusted-Origin CSRF validation and Redis-backed rate limiting
- Typed request contracts, content-aware image validation and bounded uploads
- Cloudinary CDN media with ownership-aware update/delete behavior
- Server-authoritative Paystack amounts, signed webhooks and idempotent verification
- PostgreSQL readiness, process liveness and versioned Alembic migrations
- Pull-request tests, frontend tests, staging E2E, container builds and vulnerability scanning
- Code ownership, contribution policy, PR template and structured user stories
- Railway IaC, private managed dependencies, Sentry integration and independent scaling

## Honest limitations

The deployed release is a production-grade capstone/MVP, not a completed commercial marketplace. Paystack must remain in test mode until end-to-end payment, webhook, refund and reconciliation procedures are verified and the business account is approved. Vendor split payouts require KYC and settlement controls. Inventory reservation, transactional email, moderation workflows, accessibility/load testing, tested database restoration and multi-region disaster recovery remain roadmap work.

## License

MIT. Third-party packages retain their respective licenses.
