# BloomAI Global Marketplace

BloomAI is an AI-enabled botanical marketplace capstone by Kolapo Adedipe. It demonstrates secure marketplace transactions, independently deployable AI inference, event-driven processing and production engineering in a service-oriented monorepo.

> Production application: `DEPLOYED_APP_URL` — replace immediately after Railway deployment.
> Final demonstration: `DEMO_VIDEO_URL` — replace after uploading the 15–20 minute MP4 to Google Drive.

[![CI](https://github.com/kadedipe/BloomAI-Global-Marketplace/actions/workflows/ci.yml/badge.svg)](https://github.com/kadedipe/BloomAI-Global-Marketplace/actions/workflows/ci.yml)

## Capstone evidence

- [Faculty compliance matrix](docs/CAPSTONE-COMPLIANCE.md)
- [Design and testing report](docs/DESIGN-AND-TESTING.md)
- [Agile and three-sprint evidence](docs/AGILE-EVIDENCE.md)
- [Final demonstration plan](docs/DEMO-SCRIPT.md)
- [AI tooling disclosure](docs/AI-TOOLING.md)
- [Trello Scrum board](https://trello.com/invite/b/6a359b640166be0bf5636001/ATTIe8e1ab12cb2c5e1b5e4827fd4cc8145a9434255E/bloomai-global-marketplace-product-backlog-board)

Before submission, add GitHub user `quantic-grader` as a repository collaborator and complete every pending external action in the compliance matrix.

## Architecture

| Service | Directory | Responsibility | Exposure |
|---|---|---|---|
| BloomAI Web | `apps/web` | React customer/vendor experience | Public |
| Marketplace API | `services/marketplace-api` | Authentication, authorization and catalog | Public |
| AI Inference API | `services/ai-api` | Safe image validation and model boundary | Public |
| Event Worker | `services/event-worker` | Asynchronous domain-event processing | Private |
| PostgreSQL | Railway managed | Durable relational state | Private |
| Redis | Railway managed | Event queue/cache foundation | Private |

The original training notebooks remain in `ai-services` as research provenance and are excluded from runtime images.

## Demonstrable capabilities

- Register customer or vendor accounts and authenticate with expiring JWTs
- Enforce vendor-only product creation
- Persist and discover marketplace listings
- Submit bounded JPEG/PNG/WebP files to an isolated AI service
- Process versioned `product.created` events outside the request cycle
- Inspect service liveness/readiness and structured Railway logs

The AI service does not fabricate a classification when its validated model is absent. It returns an explicit unavailable response until the model artifact and adapter are provisioned.

## Local development

```bash
cp .env.example .env
docker compose up --build
```

- Web: `http://localhost:5173`
- Marketplace API docs: `http://localhost:8000/docs`
- AI API docs: `http://localhost:8001/docs`

Run quality checks:

```bash
make test
make lint
```

## Railway production deployment

Railway configuration is defined in `.railway/railway.ts` using current project-level Infrastructure as Code.

```bash
npm --prefix .railway install
railway login
railway link
railway config plan
railway config apply
```

Then generate public domains for the web and both APIs. Set:

| Service | Variable | Value |
|---|---|---|
| Marketplace API | `JWT_SECRET` | At least 32 cryptographically random characters |
| Marketplace API | `CORS_ORIGINS` | Final BloomAI Web HTTPS URL |
| AI API | `CORS_ORIGINS` | Final BloomAI Web HTTPS URL |
| BloomAI Web | `VITE_API_URL` | Final Marketplace API HTTPS URL |
| BloomAI Web | `VITE_AI_API_URL` | Final AI API HTTPS URL |

The IaC graph connects APIs and the worker to PostgreSQL/Redis through Railway reference variables and private networking. See [.railway/README.md](.railway/README.md) for the apply workflow.

## API example

```bash
export API="https://YOUR-MARKETPLACE-API.up.railway.app"
curl -X POST "$API/api/v1/auth/register" -H 'content-type: application/json' \
  -d '{"email":"vendor@example.com","password":"strong-password","name":"Bloom Vendor","role":"vendor"}'
curl -X POST "$API/api/v1/auth/login" -H 'content-type: application/json' \
  -d '{"email":"vendor@example.com","password":"strong-password"}'
```

## Engineering controls

- Non-root minimal containers and environment-only secrets
- Argon2 password hashing, short-lived JWTs and role-based authorization
- Typed request contracts and bounded image uploads
- PostgreSQL readiness and process liveness checks
- Pull-request tests, linting, four container builds and high-severity vulnerability scanning
- Code ownership, contribution policy, PR template and structured user stories
- Current Railway IaC, environment separation and independent scaling

## Honest limitations

Checkout/payment, inventory reservation, email delivery and vendor moderation are roadmap items. The committed flower-training code is not automatically production-compatible; model provenance and evaluation must be documented before enabling live inference. See the design report for risks and next steps.

## License

MIT. Third-party packages retain their respective licenses.
