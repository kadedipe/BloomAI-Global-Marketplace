# Production verification evidence

Verified on 30–31 August 2026 against the Railway production environment.

| Capability | Evidence | Result |
|---|---|---|
| Marketplace readiness | `GET /health/ready` | HTTP 200, `{"status":"ready"}` |
| Database migration | Railway deployment `32141ac6-c750-4528-8039-d8012ac300e1` | Alembic `0001_initial -> 0002_product_media_orders` succeeded |
| Cloudinary configuration deployment | Railway deployment `5f421edb-9ac5-4223-a1df-973f74f8d0c1` | Healthy startup and HTTP 200 readiness |
| API documentation | `HEAD /docs` and rendered OpenAPI 3.1 UI | HTTP 200 |
| Web delivery | `HEAD https://bloomai-web-production.up.railway.app` | HTTP 200 |
| Registration | Railway request logs | HTTP 201 |
| Login/session | Login and authenticated `/auth/me` requests | HTTP 200 |
| Product discovery | `GET /api/v1/products` | HTTP 200 |
| Product media | Authenticated browser upload and persisted Cloudinary CDN URL | Product remained visible with managed HTTPS media |
| Product ownership controls | Vendor UI and protected update/delete endpoints | User-validated in the production rehearsal |
| AI readiness | Verified artifact download and `/health/ready` | HTTP 200; 102 classes loaded |
| AI CORS | Production web origin preflight | HTTP 200 with exact allow-origin |
| AI inference API | Multipart `image` upload to `/api/v1/classify` | HTTP 200 and exactly five predictions |
| AI inference browser | AI Lab upload of `flower.jpg` | Five ranked results rendered |
| Payment contracts | OpenAPI initialize and verification endpoints | Deployed; Paystack test-mode transaction evidence still required |

The active model is `mobilenet_v3_small` with artifact SHA-256 `9ee2f29556562a14a666ad8345b850b7aa11d26dc2e73b16a735d4d33b515dc9`. Its independently recorded test accuracy is 95.24% and top-five accuracy is 99.63%.

## Final submission evidence

- Production marketplace, Cloudinary media, authentication, ownership controls, API documentation and five AI predictions were user-validated.
- GitHub user `quantic-grader` was invited (user-confirmed).
- [The 15–20 minute presentation is available on YouTube](https://youtube.com/live/AffW_CxeEks?feature=share).
- Add the public-view Google Drive URL for the actual MP4/MOV to satisfy the Faculty hosting specification.
- Complete Paystack test checkout, signed webhook and order verification only if payments are claimed or demonstrated as fully operational.
- Capture or link the final passing CI run and successful Railway deployments where useful.
