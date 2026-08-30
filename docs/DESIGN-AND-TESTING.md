# Design and testing report

## 1. Product scope

BloomAI connects botanical vendors and customers and provides an isolated AI capability for flower identification. The demonstrable release supports user registration, authentication, role-based vendor listing creation, public product discovery, service health reporting and safe image submission. AI prediction is feature-gated until a validated checkpoint is deployed; the API returns an explicit unavailable response instead of misleading results.

## 2. Quality attributes

The architecture prioritizes availability, security, evolvability, testability, observability and cost control. Transactional requests remain independent from AI inference and background work, allowing each workload to fail or scale separately.

## 3. Architecture

| Component | Responsibility | Data/communication |
|---|---|---|
| React web | Customer and vendor experience | HTTPS to public APIs |
| Marketplace API | Identity, authorization and catalog transactions | PostgreSQL; Redis event queue |
| AI API | Upload validation and model inference boundary | Model artifact mounted at runtime |
| Event worker | Asynchronous domain-event processing | Private Redis connection |
| PostgreSQL | Durable users and products | Railway private network |
| Redis | Decoupled event queue/cache foundation | Railway private network |

### Patterns and rationale

- **Service-oriented monorepo:** independent deployments with atomic cross-service review.
- **Layered API:** schemas, persistence, security and domain events have separate modules.
- **Repository/unit-of-work behavior:** SQLAlchemy sessions scope database work to requests.
- **Role-based access control:** customer, vendor and admin permissions are explicit.
- **Event-driven processing:** catalog writes enqueue versioned events; slow notifications do not extend request latency.
- **Health endpoint pattern:** liveness checks process state; readiness checks database connectivity.
- **Twelve-factor configuration:** deployment-specific settings and secrets come from environment variables.
- **Fail-safe AI boundary:** missing/unverified models cause explicit 503/501 errors.

## 4. Key decisions and trade-offs

PostgreSQL is selected over document storage because users, vendors and orders are relational and require transactional integrity. Redis is introduced only for ephemeral events/cache, never as the source of truth. FastAPI offers typed contracts and automatic OpenAPI documentation. React/Vite provides a small static production bundle.

Railway is the recommended cloud target because it supports isolated monorepo services, managed PostgreSQL/Redis, private networking, health checks, GitHub deployments and integrated logs. Its usage-based cost is appropriate for a capstone/MVP but can rise with always-on workers and replicas. Local Docker Compose is the zero-cloud-cost development option. For a high-volume commercial system, reserved compute, managed object storage, a durable queue and multi-region database strategy should be evaluated.

## 5. Security and privacy

Passwords are Argon2-hashed. JWTs are signed, expiring and sent through bearer authorization. Inputs are constrained by typed schemas; image MIME type and size are bounded. Containers run as non-root users. Secrets are preserved in Railway rather than committed. CI includes dependency/source vulnerability scanning. Production should additionally use a custom domain, WAF/rate limiting, email verification, secret rotation and database backups.

## 6. Testing strategy

| Test level | Evidence | Purpose |
|---|---|---|
| Unit | worker event parsing | Verify deterministic domain behavior cheaply |
| API/component | marketplace auth and health; AI health and upload rejection | Validate contracts and security boundaries |
| Build | Vite production build and four Docker builds | Detect packaging/runtime regressions |
| Static analysis | Ruff | Detect Python defects and inconsistent code |
| Supply chain | Anchore scan | Block known high-severity dependency/file vulnerabilities |
| Deployment smoke | Railway runbook health and API checks | Verify managed dependencies and routing |

Tests run on every pull request and push to `main`. CI concurrency cancels superseded builds. A change is mergeable only when Python tests, frontend compilation, container builds and supply-chain scanning pass.

## 7. Known limitations and roadmap

- The trained flower model is not committed because model provenance, compatibility and size must be verified.
- Checkout/payment, inventory reservation, vendor moderation and email delivery are roadmap items, not claimed features.
- Startup schema creation is adequate for the current additive prototype; versioned Alembic migrations are required before incompatible schema changes.
- Redis lists provide simple queueing but not durable acknowledgements. Production scale should adopt Redis Streams or a managed durable queue with a dead-letter policy.
- Load, accessibility, browser E2E and model-quality tests should be added before commercial launch.

