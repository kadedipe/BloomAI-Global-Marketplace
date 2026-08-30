# Agile delivery evidence

Task board: [BloomAI Global Marketplace Product Backlog](https://trello.com/invite/b/6a359b640166be0bf5636001/ATTIe8e1ab12cb2c5e1b5e4827fd4cc8145a9434255E/bloomai-global-marketplace-product-backlog-board)

## Roles

| Role | Owner |
|---|---|
| Product Owner | Kolapo Adedipe |
| Scrum Master | Kolapo Adedipe (individual-project assumption; update if team-based) |
| Code Owner | `@kadedipe` |

## Definition of done

A story is done when acceptance criteria are satisfied, relevant tests pass, documentation is updated, CI passes, code-owner review is complete and the increment can be demonstrated in the deployed environment.

## Sprint 1 — Product conception and AI prototype

Goal: validate the botanical marketplace and flower-classification use case.

- Created the product vision, initial backlog and architecture.
- Developed flower-training and prediction experiments.
- Defined customer, vendor and AI user journeys.
- Preserved notebooks and training provenance in `ai-services`.
- Demo evidence: add the real sprint increment recording link if available.

## Sprint 2 — Marketplace service foundation

Goal: provide a secure transactional service and deployable web experience.

- Implemented registration, login, session restoration and role-based authorization.
- Added product creation and public product discovery.
- Added PostgreSQL persistence, typed API contracts and health endpoints.
- Created the responsive React marketplace.
- Added Docker packaging and automated tests.
- Demo evidence: add the real sprint increment recording link if available.

## Sprint 3 — Production engineering and submission readiness

Goal: deliver a reproducible Railway deployment and highest-band Capstone evidence.

- Separated web, Marketplace API, AI API and event worker services.
- Retrained and deployed a 102-class MobileNetV3 Small model with 95.24% held-out accuracy.
- Added Redis-backed events and rate limiting, PostgreSQL migrations and health checks.
- Added secure vendor sessions, CSRF Origin validation and ownership-aware product edit/delete.
- Added validated Cloudinary uploads, persisted CDN URLs, previews and image fallbacks.
- Added Paystack initialization, signed webhook and payment-verification contracts.
- Added Railway Infrastructure as Code, managed data services, Sentry integration and production runbooks.
- Added CI, frontend unit tests, staging Playwright E2E, container builds and supply-chain scanning.
- Verified the production marketplace, managed product image and five browser AI predictions.
- Final demo evidence: add the public-view 15–20 minute Google Drive MP4 URL after recording.

## Required board hygiene before submission

The Trello board—not this retrospective summary—is the source of truth. Before submission:

- Confirm the board opens without authentication.
- Assign every delivered story to a sprint and owner.
- Include acceptance criteria, constituent tasks and completion state.
- Link relevant pull requests, CI runs, production evidence and sprint demos.
- Do not mark planned commercial capabilities as delivered unless they work in production.
