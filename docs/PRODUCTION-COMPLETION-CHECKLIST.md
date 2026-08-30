# Production and Faculty completion checklist

## Repository-controlled work

- [x] Railway monorepo services, managed PostgreSQL and Redis
- [x] Alembic migrations
- [x] Secure cookie authentication and vendor authorization
- [x] MobileNetV3 102-class inference with checksum verification
- [x] Cloudinary upload integration, validation, preview and fallback
- [x] Vendor-owned product update/delete APIs and tests
- [x] Cookie mutation Origin/CSRF protection
- [x] Redis-backed endpoint throttling
- [x] Paystack hosted checkout, authoritative order totals, signed webhooks and verification
- [x] Frontend unit tests and staging Playwright workflow
- [ ] Merge only after CI, migration review and staging E2E pass

## External production controls

- [ ] Configure Cloudinary production credentials in Railway
- [ ] Configure Paystack **test** secret and webhook; complete test-mode checkout/refund rehearsal
- [ ] Complete Paystack business verification before live keys
- [ ] Verify Railway daily/weekly/monthly backups
- [ ] Restore a backup into an isolated environment and record RPO/RTO
- [ ] Configure Sentry error, latency, model initialization and database alerts
- [ ] Configure uptime and Railway budget alerts
- [ ] Configure staging URLs and E2E vendor GitHub secrets
- [ ] Run staging Playwright workflow successfully
- [ ] Configure custom domains and repeat CORS/smoke tests

## Faculty submission

- [ ] Ensure Trello is accessible and every delivered story has sprint, owner, acceptance criteria, status and evidence
- [ ] Add sprint planning/review dates and available demo links
- [ ] Seed three polished, non-test products
- [ ] Complete incognito end-to-end rehearsal
- [ ] Record one 15–20 minute MP4 with required presenter, camera, voice and ID evidence
- [ ] Upload video to Google Drive with “Anyone with the link can view”
- [ ] Replace `DEMO_VIDEO_URL` in all evidence
- [ ] Add `quantic-grader` and verify repository access externally
- [ ] Submit the signed Group Project Agreement final page when applicable
