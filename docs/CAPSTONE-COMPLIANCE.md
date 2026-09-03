# MSSE Capstone Faculty Submission — BloomAI Global Marketplace

This document maps the Quantic MSSE Capstone Faculty requirements to the current BloomAI Global Marketplace repository and deployed production evidence.

## Public Domain

**BloomAI Global Marketplace:** https://bloomaiglobalmarketplace.com/

The custom public domain is the canonical application URL for Faculty review. The Railway URL remains documented as the underlying production deployment endpoint and operational evidence.

## Essential links

| Evidence | Link |
|---|---|
| **Public Domain / canonical application** | [https://bloomaiglobalmarketplace.com/](https://bloomaiglobalmarketplace.com/) |
| Railway production application | [https://bloomai-web-production.up.railway.app/](https://bloomai-web-production.up.railway.app/) |
| Administrator sign-in | [Admin sign-in](https://bloomai-web-production.up.railway.app/admin-login.html) |
| Administrator dashboard | [Admin dashboard](https://bloomai-web-production.up.railway.app/admin.html) |
| Marketplace API documentation | [Swagger API docs](https://marketplace-api-production-c7cd.up.railway.app/docs) |
| Marketplace readiness | [API readiness](https://marketplace-api-production-c7cd.up.railway.app/health/ready) |
| AI inference readiness | [AI readiness](https://ai-inference-api-production.up.railway.app/health/ready) |
| GitHub repository | [BloomAI Global Marketplace](https://github.com/kadedipe/BloomAI-Global-Marketplace) |
| GitHub Actions | [CI workflow](https://github.com/kadedipe/BloomAI-Global-Marketplace/actions/workflows/ci.yml) |
| Pull-request history | [Closed PRs](https://github.com/kadedipe/BloomAI-Global-Marketplace/pulls?q=is%3Apr+is%3Aclosed) |
| Agile/Trello board | [BloomAI product backlog](https://trello.com/invite/b/6a359b640166be0bf5636001/ATTIe8e1ab12cb2c5e1b5e4827fd4cc8145a9434255E/bloomai-global-marketplace-product-backlog-board) |
| Recorded presentation | [YouTube presentation](https://youtube.com/live/AffW_CxeEks?feature=share) |
| README | [README.md](../README.md) |

## Faculty requirements and evidence

| Requirement | BloomAI evidence | Status |
|---|---|---|
| Working public web application | Canonical custom domain plus Railway deployment | Complete |
| Accessible documented repository | README, source, tests, CI, PR history and engineering documentation | Complete |
| Agile development | Trello backlog and three-sprint evidence | Complete |
| Design/testing documentation | `DESIGN-AND-TESTING.md`, automated tests and CI | Complete |
| AI capability | MobileNetV3 Small, 102 classes, top-five predictions and checksum-gated model | Complete |
| Secure identity | Secure HttpOnly sessions, customer/vendor/admin role enforcement and disabled public admin registration | Complete |
| Vendor marketplace | Product ownership, media, inventory/availability and order workflows | Complete |
| Production commerce | Server-authoritative checkout, inventory reservation, Paystack payment verification/webhooks | Production lifecycle validated |
| Fulfillment/refunds | Tracked/no-tracking delivery plus provider-backed admin refund execution | Production lifecycle validated |
| Administration/reporting | Executive KPIs, trends, segmentation, exports, world map and refund operations | Complete |
| Notifications | Persistent role-aware notifications and preferences | Complete |
| AI-assisted support | Contextual assistance with deterministic critical safety path | Complete |
| Persistent support cases | Human escalation, linked order, assignment, conversation and status lifecycle | Production lifecycle validated |
| Admin Support Inbox | Filtering, assignment, replies and status transitions | Production lifecycle validated |
| Latest-order support UX | Critical support defaults to the latest relevant accessible order | Complete |
| Resolved-case controls | Resolved/closed cases are participant read-only until admin reopen | Complete |
| CI/CD | GitHub Actions, container/model/supply-chain checks and Railway deployment | Complete |
| Recorded presentation | YouTube presentation | Recorded; add Google Drive MP4/MOV URL if Faculty requires it |
| Grader access | `quantic-grader` invited | User-confirmed |

## Validated production workflows

### Commerce

BloomAI has exercised checkout/payment, fulfillment to delivered, refund request/review/execution and final refunded state through the integrated application/provider workflow. Payment and refund states are not manually forged in the database.

### Support

The production support workflow has exercised critical participant assistance, latest-relevant-order context, explicit escalation, persistent case creation, administrator notification, Support Inbox visibility, admin reply, participant reply, resolution and participant notification. Resolved/closed cases are read-only for participants until an administrator reopens them.

## AI model evidence

BloomAI Vision uses MobileNetV3 Small for 102 flower classes. Production artifact SHA-256:

`9ee2f29556562a14a666ad8345b850b7aa11d26dc2e73b16a735d4d33b515dc9`

Recorded held-out metrics are **95.24% test accuracy** and **99.63% top-five accuracy**.

## Post-recording production hardening

The merged engineering history includes administrator analytics and segmentation (#14–#20), persistent notifications/email/profile media (#21–#25), marketplace commerce/inventory/fulfillment and production validation (#27–#31), checkout/auth/provider reliability (#32–#38), legitimate no-tracking delivery (#39), provider-backed refund execution (#40), AI support safety and deterministic critical handling (#41–#44), persistent support cases and Support Inbox (#45), and latest-order/resolved-case UX controls (#46).

Full evidence: [merged pull requests](https://github.com/kadedipe/BloomAI-Global-Marketplace/pulls?q=is%3Apr+is%3Aclosed).

## Faculty submission index

- [README](../README.md)
- [Design and testing](DESIGN-AND-TESTING.md)
- [Agile evidence](AGILE-EVIDENCE.md)
- [Demo script](DEMO-SCRIPT.md)
- [AI tooling disclosure](AI-TOOLING.md)
- [Production verification](PRODUCTION-VERIFICATION.md)
- [Production operations](PRODUCTION_OPERATIONS.md)
- [Production completion checklist](PRODUCTION-COMPLETION-CHECKLIST.md)
- [Commerce fulfillment](COMMERCE-FULFILLMENT.md)
- [Commerce hardening](COMMERCE-HARDENING.md)
- [Support Assistant](support-assistant.md)
- [Administrator access](admin-access.md)
- [Verified geocoding import](geocoding-import.md)

## Final submission gate

Before Faculty submission, confirm the custom domain, Railway application, API/readiness endpoints, GitHub repository, Trello board and presentation links while signed out/incognito; preserve a passing CI/deployment run; keep secrets and private payment data out of evidence; confirm `quantic-grader` access; and add the public-view Google Drive MP4/MOV URL if required by the Faculty hosting specification.

## Submission summary

BloomAI Global Marketplace now has a professional canonical public identity at **https://bloomaiglobalmarketplace.com/** in addition to its Railway production infrastructure. The project demonstrates an end-to-end AI-enabled marketplace with secure identity, commerce, payment/refund orchestration, fulfillment, AI inference, analytics, notifications, responsible AI support, persistent human escalation, CI/CD and production deployment evidence.
