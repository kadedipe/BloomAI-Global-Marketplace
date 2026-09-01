# MSSE Capstone Faculty Submission — BloomAI Global Marketplace

This document maps the Quantic MSSE Capstone Faculty requirements to the current BloomAI Global Marketplace repository and deployed production evidence. It distinguishes implemented/validated software from external provider configuration and Faculty-hosting actions.

The original capstone was deployed and demonstrated before the latest hardening cycle. Since that recording, BloomAI has evolved into a substantially stronger production capstone through administrator analytics, verified geographic reporting, persistent notifications, inventory-aware commerce, Paystack payment/refund workflows, fulfillment, AI-assisted support, persistent support cases and notification-driven human escalation.

## Essential links

| Evidence | Link |
|---|---|
| Production web application | [https://bloomai-web-production.up.railway.app/](https://bloomai-web-production.up.railway.app/) |
| Administrator sign-in | [https://bloomai-web-production.up.railway.app/admin-login.html](https://bloomai-web-production.up.railway.app/admin-login.html) |
| Administrator dashboard | [https://bloomai-web-production.up.railway.app/admin.html](https://bloomai-web-production.up.railway.app/admin.html) |
| Marketplace API documentation | [https://marketplace-api-production-c7cd.up.railway.app/docs](https://marketplace-api-production-c7cd.up.railway.app/docs) |
| Marketplace readiness | [https://marketplace-api-production-c7cd.up.railway.app/health/ready](https://marketplace-api-production-c7cd.up.railway.app/health/ready) |
| AI inference readiness | [https://ai-inference-api-production.up.railway.app/health/ready](https://ai-inference-api-production.up.railway.app/health/ready) |
| GitHub repository | [https://github.com/kadedipe/BloomAI-Global-Marketplace](https://github.com/kadedipe/BloomAI-Global-Marketplace) |
| GitHub Actions CI | [CI workflow](https://github.com/kadedipe/BloomAI-Global-Marketplace/actions/workflows/ci.yml) |
| Merged pull-request history | [Closed PRs](https://github.com/kadedipe/BloomAI-Global-Marketplace/pulls?q=is%3Apr+is%3Aclosed) |
| Agile/Trello board | [BloomAI product backlog](https://trello.com/invite/b/6a359b640166be0bf5636001/ATTIe8e1ab12cb2c5e1b5e4827fd4cc8145a9434255E/bloomai-global-marketplace-product-backlog-board) |
| Recorded presentation | [YouTube presentation](https://youtube.com/live/AffW_CxeEks?feature=share) |
| README | [README.md](../README.md) |

## Faculty requirements and current evidence

| Faculty requirement | Current BloomAI evidence | Status | Final action |
|---|---|---|---|
| Accessible documented repository | README, service source, tests, CI, PR history, contribution/security controls | Complete | Confirm `quantic-grader` retains access |
| Working deployed application | Production Railway web application and health/readiness endpoints | Complete | Final signed-out smoke test |
| Accessible agile board | Trello link plus `AGILE-EVIDENCE.md` | Complete (user-validated) | Recheck while signed out |
| At least three sprints | `AGILE-EVIDENCE.md` | Complete | Preserve stories, owners, acceptance criteria and completion state |
| Design/testing document | `DESIGN-AND-TESTING.md`, source-aligned tests and CI | Complete | Final proofreading |
| Architecture rationale | Service-oriented monorepo, PostgreSQL, Redis, Railway, Cloudinary, Paystack, optional AfterShip/Resend/OpenRouter-compatible support provider | Complete | None |
| Automated testing | Marketplace API tests/Ruff, web tests/build, AI API, Event Worker, model-contract tests, containers and supply-chain scan | Complete | Preserve final passing CI run |
| CI/CD and collaborative engineering | GitHub Actions, extensive PR history and Railway GitHub deployments | Complete | Preserve final deployment evidence |
| AI tooling evidence | `AI-TOOLING.md`, reproducible training code, model provenance and production verification | Complete | Keep disclosure current |
| Working AI capability | MobileNetV3 Small, 102 classes, top-five predictions, checksum-gated artifact | Complete | Capture browser evidence if desired |
| Secure identity | Secure HttpOnly session cookies, role enforcement, explicit admin bootstrap, disabled public admin registration | Complete | Verify customer/vendor/admin login paths |
| Marketplace media | Cloudinary product images and optional participant profile photos | Complete | Final upload/persistence smoke test |
| Vendor marketplace | Product create/edit/delete, ownership controls, availability/inventory management | Complete | Final smoke test |
| Production commerce | Server-authoritative quote/checkout, inventory reservations, cancellation/expiry, Paystack initialization/verification/webhooks | Production lifecycle validated | Retain provider test evidence; do not expose credentials |
| Fulfillment | Processing/shipped/delivered/cancelled states, optional tracking integration and legitimate no-tracking delivery methods | Complete for implemented scope | Do not fabricate tracking data |
| Refund workflow | Customer request, vendor/admin review, admin-only provider-backed Paystack refund execution and reconciliation | Production lifecycle validated | Preserve audit evidence; do not directly mutate payment state |
| Commerce readiness/audit | Admin-only readiness and order-audit tooling | Complete | Use read-only validator for future production checks |
| Administrator reporting | Executive KPIs, trends, vendor ranking, CSV/PDF, refund operations | Complete | Verify current dashboard |
| Participant segmentation | Organization-size/category taxonomy and admin profile editor | Complete | Preserve real classifications |
| Geographic reporting | Verified coordinates, interactive map and country fallback | Complete | Never fabricate coordinates |
| In-app notifications | Persistent role-aware notifications, unread/read controls | Complete | Production validated |
| Notification preferences | Per-user categories and mandatory critical administrator alerts | Complete | Recheck save/reload after major deploys |
| Transactional email | Resend integration with persisted in-app fallback | Implemented; provider/configuration dependent | Claim live email only after verified sender test |
| AI-assisted support | Contextual customer/vendor support with deterministic critical-safety path and optional external AI for non-critical assistance | Complete | Continue safety regression testing |
| Persistent support cases | Escalation creates case ID, category, priority, status, linked order, assignment, timestamps and conversation | Production lifecycle validated | Preserve case lifecycle evidence |
| Admin Support Inbox | Filtering, assignment, admin replies and status transitions | Production lifecycle validated | None |
| Support notification bot | Case opened/admin reply/participant reply/status-change notifications | Production lifecycle validated | None |
| Support privacy/safety | Accessible-context only; no password/OTP/full-card/API-key requests; no reasoning leakage; critical deterministic response | Complete | Maintain tests |
| Latest-order support UX | Critical support defaults to latest relevant accessible order and associates escalation with that order | Complete | Full history only on explicit request |
| Resolved-case controls | Resolved/closed cases participant read-only until explicit admin reopen | Complete | Maintain backend + UI enforcement |
| 15–20 minute recorded demo | YouTube presentation and `DEMO-SCRIPT.md` | Recorded; Faculty hosting format pending if required | Add public-view Google Drive MP4/MOV URL |
| Grader access | Repository collaborator settings | Complete — `quantic-grader` invited (user-confirmed) | Confirm access remains valid |
| Group Project Agreement final page | Not stored publicly because it may contain signatures/personal data | External action if group-based | Submit privately through Quantic dashboard |

## Validated production workflows

### Commerce lifecycle

BloomAI production has exercised an integrated commerce path including a real application order record through successful Paystack payment confirmation, fulfillment to delivered, refund request/review/execution and final refunded state. The application uses provider verification/webhooks and provider-backed refund execution rather than manually marking payment/refund state in the database.

The hardening work also introduced inventory reservation, reservation expiry, safe payment retry, response/reference collision protection, provider-failure handling, fulfillment tracking foundations, legitimate no-tracking delivery and read-only production commerce validation.

### Support lifecycle

The production support workflow has been exercised end to end:

1. Signed-in participant submits a critical unauthorized-payment concern.
2. BloomAI returns deterministic safety guidance using only the latest relevant accessible order context.
3. Participant explicitly escalates.
4. A persistent critical support case is created and linked to the relevant order.
5. Administrator receives a critical notification and sees the case in Support Inbox.
6. Administrator can assign the case and reply.
7. Participant receives the reply notification and can respond while the case is active.
8. Administrator resolves the case.
9. Participant receives the resolution notification.
10. Resolved/closed cases become participant read-only until explicitly reopened by an administrator.

This demonstrates AI assistance with a controlled human handoff rather than allowing the AI to execute sensitive commerce operations.

## AI model evidence

BloomAI Vision uses MobileNetV3 Small for 102 flower classes. The production model artifact is checksum-gated:

`9ee2f29556562a14a666ad8345b850b7aa11d26dc2e73b16a735d4d33b515dc9`

Recorded held-out metrics:

- Test accuracy: **95.24%**
- Top-five accuracy: **99.63%**

If the artifact is missing or invalid, AI readiness fails instead of fabricating predictions.

## Post-recording production-hardening evidence

The following pull requests demonstrate iterative engineering after the original Faculty evidence refresh:

| PR | Improvement | Evidence significance |
|---|---|---|
| [#14](https://github.com/kadedipe/BloomAI-Global-Marketplace/pull/14) | Admin reporting/segmentation | Protected administration and persisted participant classification |
| [#15](https://github.com/kadedipe/BloomAI-Global-Marketplace/pull/15) | Executive analytics/reports | KPIs, trends, conversion/retention and exports |
| [#16](https://github.com/kadedipe/BloomAI-Global-Marketplace/pull/16) | Interactive world map | Geographic analysis and fallback reporting |
| [#17](https://github.com/kadedipe/BloomAI-Global-Marketplace/pull/17) | Verified geocoding import | Data-quality controls; no fabricated coordinates |
| [#18](https://github.com/kadedipe/BloomAI-Global-Marketplace/pull/18) / [#19](https://github.com/kadedipe/BloomAI-Global-Marketplace/pull/19) | Admin bootstrap/sign-in + packaging | Secure production administrator provisioning |
| [#20](https://github.com/kadedipe/BloomAI-Global-Marketplace/pull/20) | Participant profile editor | Admin management of segmentation/location metadata |
| [#21](https://github.com/kadedipe/BloomAI-Global-Marketplace/pull/21) | Persistent notifications | Account/listing/order/payment notifications |
| [#22](https://github.com/kadedipe/BloomAI-Global-Marketplace/pull/22) | Safe admin test notifications | Delivery testing without fake commerce data |
| [#23](https://github.com/kadedipe/BloomAI-Global-Marketplace/pull/23) | Notification preferences | User controls + mandatory critical alerts |
| [#24](https://github.com/kadedipe/BloomAI-Global-Marketplace/pull/24) | Transactional email | Optional Resend delivery with in-app fallback |
| [#25](https://github.com/kadedipe/BloomAI-Global-Marketplace/pull/25) | Profile photos | Validated Cloudinary participant avatars |
| [#27](https://github.com/kadedipe/BloomAI-Global-Marketplace/pull/27) | Customer/vendor order flow | Marketplace purchasing foundation |
| [#28](https://github.com/kadedipe/BloomAI-Global-Marketplace/pull/28) | Inventory/fulfillment | Stock reservation and order lifecycle |
| [#29](https://github.com/kadedipe/BloomAI-Global-Marketplace/pull/29) | Commerce hardening | Quotes, reservation expiry, provider/shipping/refund state |
| [#30](https://github.com/kadedipe/BloomAI-Global-Marketplace/pull/30) | Production commerce validation | Admin readiness/audit tooling |
| [#31](https://github.com/kadedipe/BloomAI-Global-Marketplace/pull/31) | Optional AfterShip readiness | Tracked shipping optional, manual fallback retained |
| [#32](https://github.com/kadedipe/BloomAI-Global-Marketplace/pull/32)–[#38](https://github.com/kadedipe/BloomAI-Global-Marketplace/pull/38) | Checkout/auth/provider reliability | Logout race, CORS/provider failure handling, safe checkout and Paystack reference normalization |
| [#39](https://github.com/kadedipe/BloomAI-Global-Marketplace/pull/39) | No-tracking fulfillment | Local/vendor/pickup/independent-courier support without fake tracking |
| [#40](https://github.com/kadedipe/BloomAI-Global-Marketplace/pull/40) | Admin refund execution | Provider-backed Paystack refund workflow |
| [#41](https://github.com/kadedipe/BloomAI-Global-Marketplace/pull/41) | AI support assistant | Context-aware customer/vendor support |
| [#42](https://github.com/kadedipe/BloomAI-Global-Marketplace/pull/42) | Support grounding | Prevent unsupported internal-team/provider claims |
| [#43](https://github.com/kadedipe/BloomAI-Global-Marketplace/pull/43) | Support output/network hardening | Reasoning-leak prevention and safe network errors |
| [#44](https://github.com/kadedipe/BloomAI-Global-Marketplace/pull/44) | Deterministic critical support | Critical issues bypass external-model speculation |
| [#45](https://github.com/kadedipe/BloomAI-Global-Marketplace/pull/45) | Persistent support cases | Case records, Support Inbox and notification-driven conversation |
| [#46](https://github.com/kadedipe/BloomAI-Global-Marketplace/pull/46) | Latest-order/reopen UX | Relevant order association and resolved-case reply lock |

## Engineering narrative for Faculty

BloomAI demonstrates an end-to-end software engineering system rather than a standalone model demo. Public web delivery, marketplace APIs, AI inference and asynchronous event processing are separated into independently deployable services. PostgreSQL persists marketplace and communication state, Redis supports rate limiting/events, Cloudinary handles validated media, Paystack provides payment/refund orchestration, and optional external providers extend shipping, email and non-critical support generation without becoming single points of failure for core application state.

The commerce domain is explicitly defensive: prices are server-authoritative, inventory is reserved, provider responses are normalized, payment failures are translated into controlled API responses, refund execution is admin-only/provider-backed, and legitimate no-tracking delivery is supported instead of encouraging fabricated carrier data.

The support domain demonstrates responsible AI integration. The assistant is read-only with respect to commerce state. Critical issues are deterministic, grounded in the signed-in participant's latest relevant order and require explicit human escalation. Persistent cases provide a traceable participant/admin conversation and state machine. Resolved cases are locked from participant replies until an administrator intentionally reopens them.

The administration domain combines operational and analytical capability: participant segmentation, executive marketplace KPIs, exportable reports, refund operations, verified geographic analysis and a persistent Support Inbox.

## Faculty submission index

- [README.md](../README.md) — project overview, production links and capabilities.
- [CAPSTONE-COMPLIANCE.md](CAPSTONE-COMPLIANCE.md) — this requirement/evidence matrix.
- [DESIGN-AND-TESTING.md](DESIGN-AND-TESTING.md) — design, architecture and testing rationale.
- [AGILE-EVIDENCE.md](AGILE-EVIDENCE.md) — backlog and three-sprint evidence.
- [DEMO-SCRIPT.md](DEMO-SCRIPT.md) — final demonstration structure.
- [AI-TOOLING.md](AI-TOOLING.md) — AI tooling disclosure.
- [PRODUCTION-VERIFICATION.md](PRODUCTION-VERIFICATION.md) — production verification evidence.
- [PRODUCTION_OPERATIONS.md](PRODUCTION_OPERATIONS.md) — production/recovery procedures.
- [PRODUCTION-COMPLETION-CHECKLIST.md](PRODUCTION-COMPLETION-CHECKLIST.md) — final submission checklist.
- [COMMERCE-FULFILLMENT.md](COMMERCE-FULFILLMENT.md) — fulfillment/refund lifecycle.
- [COMMERCE-HARDENING.md](COMMERCE-HARDENING.md) — hardened commerce architecture.
- [support-assistant.md](support-assistant.md) — support-assistant safety and operations.
- [admin-access.md](admin-access.md) — secure administrator access.
- [geocoding-import.md](geocoding-import.md) — trusted coordinate import workflow.

## Remaining external submission gates

The repository and deployed application provide strong evidence for the software-engineering requirements. Before final submission:

1. Confirm `quantic-grader` still has the required repository access.
2. Recheck the production web application, API docs/readiness endpoints, GitHub repository, Trello board and presentation while signed out/incognito.
3. Preserve a final passing GitHub Actions run and successful Railway deployment.
4. Keep production credentials, payment data, OTPs, API keys and private identifiers out of screenshots/recordings.
5. Add the public-view Google Drive URL for the actual 15–20 minute MP4/MOV if Faculty requires Google Drive hosting. Keep the YouTube link as secondary evidence.
6. If a Group Project Agreement final page is required, submit it privately through the Quantic dashboard rather than committing signatures/IDs publicly.
7. Describe Resend/AfterShip/external support-AI capability according to actual provider configuration at submission time; do not overstate optional-provider availability.

## Submission summary

BloomAI now demonstrates a complete capstone progression from AI-enabled marketplace prototype to a production-hardened service-oriented system: secure identity, vendor catalog/media, inventory-aware commerce, verified payments/refunds, flexible fulfillment, executive analytics, persistent notifications, responsible AI support, human escalation, auditable support cases, automated testing, CI/CD and Railway deployment. The post-recording pull-request history provides explicit evidence of iterative engineering, defect correction, safety hardening and production validation.
