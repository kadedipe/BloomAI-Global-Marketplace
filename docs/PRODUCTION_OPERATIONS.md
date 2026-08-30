# BloomAI production operations

## Custom domains

Choose three domains you control:

- `app.example.com` → BloomAI Web
- `api.example.com` → Marketplace API
- `ai.example.com` → AI Inference API

Create each Railway custom domain, add the DNS records Railway displays, and wait for TLS. Then update API CORS, the two web Vite URLs, and the GitHub repository variables `PRODUCTION_WEB_URL`, `PRODUCTION_MARKETPLACE_URL`, and `PRODUCTION_AI_URL`. Keep the generated Railway domains until all custom-domain smoke tests pass.

## Database migrations

Marketplace startup executes `alembic upgrade head` before Uvicorn. The initial revision safely adopts existing production tables and creates them only when absent.

```bash
cd services/marketplace-api
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

Review generated migrations and test upgrade and downgrade against a disposable database.

## Error tracking

Set `SENTRY_DSN` independently on Marketplace API and AI Inference API. Keep it unset to disable Sentry. Set `SENTRY_TRACES_SAMPLE_RATE` to control tracing (default `0.1`). Configure alerts for new production errors, error-rate regression, p95 latency, failed model initialization, and database connectivity.

## Backups and recovery

In **BloomAI PostgreSQL → Backups**, enable Railway native Daily, Weekly, and Monthly backups. Enable point-in-time recovery when supported by the current plan. Create a manual recovery point before destructive migrations.

Quarterly, restore a backup into an isolated environment and record its timestamp, restore duration, row-count checks, smoke-test result, and achieved recovery time. A backup is not verified until a restore succeeds.

## Smoke tests

The `Production smoke tests` GitHub Actions workflow runs every six hours and on demand. It checks the web app, both APIs, PostgreSQL readiness, marketplace contract, AI metadata, and a real multipart inference request. After custom-domain activation, update repository variables instead of editing the workflow.
