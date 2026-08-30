# Production verification evidence

Verified on 30 August 2026 against the Railway production environment.

| Capability | Evidence | Result |
|---|---|---|
| Marketplace readiness | `GET /health/ready` | HTTP 200, `{"status":"ready"}` |
| API documentation | `HEAD /docs` and rendered OpenAPI 3.1 UI | HTTP 200 |
| Web delivery | `HEAD https://bloomai-web-production.up.railway.app` | HTTP 200 |
| Registration | Railway request logs | HTTP 201 |
| Login/session | Login and authenticated `/auth/me` request logs | HTTP 200 |
| Product discovery | `GET /api/v1/products` request logs | HTTP 200 |
| AI readiness | Verified artifact download and `/health/ready` | HTTP 200; 102 classes loaded |
| AI CORS | Production web origin preflight to AI API | HTTP 200 with exact allow-origin |
| AI inference | Multipart `image` upload to `/api/v1/classify` | HTTP 200 and exactly five predictions |

The active model is `mobilenet_v3_small` with artifact SHA-256 `9ee2f29556562a14a666ad8345b850b7aa11d26dc2e73b16a735d4d33b515dc9`. The independently recorded test accuracy is 95.24% and top-five accuracy is 99.63%. Direct API verification does not replace the final incognito browser rehearsal and recorded Faculty demonstration.
