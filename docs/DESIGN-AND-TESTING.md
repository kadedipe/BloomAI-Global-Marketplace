# Design and testing report

## 1. Product scope

BloomAI connects botanical vendors and customers and provides an isolated AI capability for flower identification. The demonstrable release supports user registration, authentication, role-based vendor listing creation, public product discovery, service health reporting and safe image submission. AI prediction is feature-gated until a validated checkpoint is deployed; the API returns an explicit unavailable response instead of misleading results.

## 2. Quality attributes

The architecture prioritizes availability, security, evolvability, testability, observability and cost control. Transactional requests remain independent from AI inference and background work, allowing each workload to fail or scale separately.

## 3. Architecture

| Component | Responsibility | Data/communication |
|---|---|---|
| React web | Customer/vendor experience, media preview and Paystack redirect checkout | HTTPS to public APIs and Paystack hosted checkout |
| Marketplace API | Identity, authorization, catalog, media and payment orchestration | PostgreSQL; Redis throttling/events; Cloudinary; Paystack |
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

Passwords are Argon2-hashed. JWTs are signed, expiring and stored in Secure HttpOnly cookies, with bearer authorization retained for non-browser clients. Cookie-authenticated mutations require a trusted Origin, reducing cross-site request forgery risk. Redis-backed throttles protect authentication, product/media writes and payment initialization. Inputs are constrained by typed schemas; image MIME type, content and size are validated. Paystack amounts are calculated server-side, webhook signatures use HMAC-SHA512 and successful payments are accepted only when reference, amount and currency match the stored order. Containers run as non-root users and secrets are preserved in Railway rather than committed.

## 5.1 Product media

Vendors upload JPEG, PNG or WebP files to the Marketplace API. The API validates content with Pillow and uploads through server-held Cloudinary credentials into a vendor-specific folder. Products store the secure CDN URL and public identifier. Ownership rules protect update/delete operations, and the web uses preview, lazy loading and a local fallback image.

## 5.2 Payments

The first payment phase uses Paystack hosted checkout. BloomAI creates a pending order from the authoritative database price, sends the amount in minor units, redirects to Paystack, and confirms payment through both an idempotent signed webhook and authenticated verification endpoint. The platform does not claim vendor split payouts; those require vendor KYC, settlement, refunds, disputes and reconciliation controls.

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

- The verified MobileNetV3 Small artifact is provisioned from controlled external storage and checked against the documented SHA-256 before loading.
- Checkout/payment, inventory reservation, vendor moderation and email delivery are roadmap items, not claimed features.
- Versioned Alembic migrations run before application startup; upgrade and downgrade paths must be exercised against a disposable database for each schema change.
- Redis lists provide simple queueing but not durable acknowledgements. Production scale should adopt Redis Streams or a managed durable queue with a dead-letter policy.
- Load, accessibility, browser E2E and model-quality tests should be added before commercial launch.
