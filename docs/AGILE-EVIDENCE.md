# Agile delivery evidence

Task board: [BloomAI Global Marketplace Product Backlog](https://trello.com/invite/b/6a359b640166be0bf5636001/ATTIe8e1ab12cb2c5e1b5e4827fd4cc8145a9434255E/bloomai-global-marketplace-product-backlog-board)

## Roles

| Role | Owner |
|---|---|
| Product Owner | Kolapo Adedipe |
| Scrum Master | Kolapo Adedipe (individual-project assumption; update if team-based) |
| Code Owner | `@kadedipe` |

## Definition of done

A story is done when acceptance criteria are satisfied, relevant tests pass, documentation is updated, CI passes, peer/code-owner review is complete and the increment can be demonstrated in the deployed environment.

## Sprint 1 — Product conception and AI prototype

Goal: validate the botanical marketplace and flower-classification use case.

- Created product vision, initial backlog and architecture diagrams.
- Developed flower-training and prediction experiments.
- Defined customer, vendor and AI user journeys.
- Demo evidence: add recording link if one exists.

## Sprint 2 — Marketplace service foundation

Goal: provide a secure transactional service and deployable web experience.

- Implemented registration/login and role-based authorization.
- Added product creation and public product discovery.
- Added PostgreSQL persistence, typed API contracts and health endpoints.
- Created the responsive React marketplace shell.
- Added Docker packaging and automated tests.
- Demo evidence: add recording link if one exists.

## Sprint 3 — Production engineering and submission readiness

Goal: achieve reproducible Railway deployment and score-5 capstone evidence.

- Separated web, marketplace API, AI API and event worker services.
- Added Redis-backed asynchronous domain events.
- Added Railway Infrastructure as Code, private managed data services and health checks.
- Added CI builds, linting, security scanning, design/testing documentation and demonstration plan.
- Final demo evidence: replace `DEMO_VIDEO_URL` after recording.

## Required board hygiene before submission

The Trello board—not this retrospective summary—is the source of truth. Ensure each story has acceptance criteria, sprint assignment, owner, completion status and evidence link. Do not mark planned features as delivered unless they work in production.

