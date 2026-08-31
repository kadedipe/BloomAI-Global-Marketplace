# MSSE Capstone Faculty submission compliance matrix

This document maps the Quantic MSSE Capstone Handbook requirements to the current BloomAI Global Marketplace repository and production evidence. Status is deliberately conservative: repository implementation is distinguished from external configuration, payment-provider validation and Faculty-hosting requirements.

The core capstone deliverable was already deployed and demonstrated. Since the original Faculty evidence refresh, the project has received substantial production-hardening updates through merged pull requests #14–#25, including administrator analytics, participant segmentation, verified geographic reporting, notifications, notification preferences, transactional-email integration and optional customer/vendor profile photos.

## Faculty requirements and current evidence

| Faculty requirement | Current BloomAI evidence | Status | Final action |
|---|---|---|---|
| Accessible, documented GitHub repository | README, service source, tests, CI, PR history, contribution/security files | Complete | Confirm `quantic-grader` retains required repository access |
| Working deployed web application | [BloomAI production](https://bloomai-web-production.up.railway.app), Railway deployment and health checks | Complete | Perform final signed-out production smoke test |
| Accessible agile task board | Trello link in README and `AGILE-EVIDENCE.md` | Complete (user-validated) | Recheck Trello while signed out immediately before submission |
| At least three sprints | `AGILE-EVIDENCE.md` | Complete | Preserve stories, owners, acceptance criteria and completion state |
| Detailed design and testing document | `DESIGN-AND-TESTING.md` plus source-aligned tests and CI | Complete | Final proofreading only |
| Architecture decisions and rationale | Service-oriented monorepo, PostgreSQL, Redis, Railway, Cloudinary, Paystack, Resend and isolated AI inference documented in README/design evidence | Complete | None |
| Deployment choice and cost implications | Railway IaC, managed PostgreSQL/Redis, managed external providers and production operations documentation | Complete for architecture | Add current plan-cost screenshots only if Faculty explicitly requests current billing evidence |
| Automated testing and rationale | Python service tests, model-contract tests, React tests/build, staging E2E, Docker builds and supply-chain scanning | Complete | Preserve a final passing CI run |
| CI/CD and collaborative engineering | `.github/workflows/ci.yml`, pull-request history, Railway GitHub deployments and production smoke workflow | Complete | Preserve final deployment evidence |
| Appropriate AI tooling evidence | `AI-TOOLING.md`, reproducible training code, model provenance and production verification | Complete | Keep disclosure unchanged unless new AI development tooling is added |
| Working AI capability | MobileNetV3 Small, 102 classes, top-five predictions and checksum-gated production artifact | Complete | Capture browser evidence in final rehearsal if desired |
| Managed marketplace media | Cloudinary-backed product uploads plus optional customer/vendor profile photos | Complete | Verify upload/replace/remove flow in production |
| Secure user identity | JWT session cookies, customer/vendor roles, explicit administrator provisioning and disabled public admin registration | Complete | Verify customer, vendor and admin login paths |
| Vendor marketplace | Vendor-owned product create/edit/delete, ownership enforcement and public catalog | Complete | Final production smoke test |
| Payment foundation | Server-authoritative Paystack initialization, verification and signed-webhook contracts | Implemented; external validation still required for a full operational-payment claim | Use Paystack test mode and preserve checkout/webhook/verification evidence before claiming fully operational payments |
| Administrator reporting | Protected admin dashboard, KPI analytics, vendor performance, retention/conversion metrics, CSV/PDF export | Complete | Verify current production dashboard loads with administrator session |
| Participant segmentation | Organization-size/category taxonomy and administrator profile editor | Complete | Preserve real classifications; avoid presenting inferred legal/business facts as verified data |
| Geographic reporting | Structured location fields, verified-coordinate workflow, interactive world map and country fallback | Complete | Add coordinates only when verified; never fabricate latitude/longitude |
| In-app notifications | Persistent customer/vendor/admin notifications, unread counts, mark-read and mark-all-read | Complete | Production delivery already validated across roles; retain smoke-test evidence |
| Safe notification testing | Administrator-only role-targeted test facility that creates no fake order/payment/analytics activity | Complete | Use for future delivery checks instead of contaminating marketplace metrics |
| Notification preferences | Per-user account/order/payment/vendor/system categories with mandatory critical administrator alerts | Complete | Recheck save/reload behavior after production deployment changes |
| Transactional email foundation | Resend integration, user opt-in, provider-aware availability and in-app fallback | Implemented; production configuration pending | Configure verified sender/domain and Railway variables before claiming live email delivery |
| Optional customer/vendor profile photos | Nullable avatar fields, Cloudinary-backed JPEG/PNG/WebP upload, replace/remove controls, mobile-accessible UI | Complete | Recheck persistence after refresh for one customer and one vendor account |
| 15–20 minute recorded demonstration | [YouTube presentation](https://youtube.com/live/AffW_CxeEks?feature=share) and `DEMO-SCRIPT.md` | Recorded; Faculty hosting format pending | Upload the actual MP4/MOV to Google Drive, set “Anyone with the link can view,” and add the direct file-view URL |
| Grader access | Repository collaborator settings | Complete — `quantic-grader` invited (user-confirmed) | Confirm invitation/access remains valid |
| Group Project Agreement final page | Intentionally not stored in the public repository because it may contain signatures/personal data | External action if group-based | Submit privately through the Quantic dashboard |

## Post-recording production-hardening evidence

The following merged pull requests materially extend the system beyond the version represented in the earlier Faculty documentation:

| PR | Improvement | Evidence significance |
|---|---|---|
| #14 | Admin reporting, analytics and participant segmentation | Demonstrates role-aware administration, persisted segmentation and marketplace reporting |
| #15 | Executive analytics and CSV/PDF reports | Adds measurable business KPIs, trends, retention/conversion metrics and downloadable reports |
| #16 | Geocoded interactive world marketplace map | Adds structured geography, mapping, coverage metrics and country fallback |
| #17 | Trusted verified geocoding import | Demonstrates data-quality controls and explicit avoidance of fabricated coordinates |
| #18 | Production administrator bootstrap and sign-in | Adds secure administrator provisioning and a dedicated protected login flow |
| #19 | Bootstrap scripts in production image | Makes the admin bootstrap workflow available in Railway deployment |
| #20 | Admin participant profile editor | Adds working administrator management of segmentation and location metadata |
| #21 | Persistent in-app notifications | Adds account/listing/order/payment notifications and unread/read state |
| #22 | Administrator test-notification facility | Adds production-safe delivery verification without fake marketplace transactions |
| #23 | Notification preferences | Adds per-user category controls and mandatory critical admin alerts |
| #24 | Transactional email notifications | Adds Resend-backed opt-in email architecture while retaining the in-app channel |
| #25 | Customer/vendor profile photos | Adds optional personal avatars with validated Cloudinary-backed persistence |

## Updated engineering narrative for Faculty

BloomAI now demonstrates more than a basic CRUD marketplace. The system separates public web delivery, marketplace APIs, AI inference and asynchronous event processing; persists business and communication state in PostgreSQL; uses Redis for rate limiting/event infrastructure; stores validated media in Cloudinary; integrates Paystack through server-authoritative payment contracts; and provides a protected administrator reporting plane.

The administrative domain now includes participant segmentation, executive metrics, exportable reports and geography-aware analysis. Geographic accuracy is deliberately governed: precise markers are shown only when explicit verified coordinates exist, while country-level fallback prevents ungeocoded participants from disappearing from reports.

The communication domain now includes persistent in-app notifications, role-aware delivery, a safe administrator test facility, user category preferences and an opt-in transactional-email integration. Critical administrator system alerts remain mandatory. Email-provider failure does not remove the persisted in-app delivery path.

The customer/vendor experience now also includes optional profile photos. These are not required for account use; users without an image retain the normal fallback account presentation. Existing Cloudinary controls are reused rather than introducing a second media stack.

## Current rubric projection

The repository supports a strong highest-band trajectory across working software, architecture, testing, AI engineering, CI/CD, agile evidence and deployment. The latest production-hardening work strengthens the submission because it demonstrates iterative engineering after initial deployment: secure administration, observability-oriented analytics, explicit data-governance choices, persisted notification state, configurable communication preferences and user-profile media.

The remaining submission risks are external rather than architectural:

1. The Faculty handbook specifies the actual recorded MP4/MOV hosted on Google Drive. The current public evidence includes YouTube, so the direct public-view Google Drive file URL should still be added.
2. Paystack should not be described as fully production-operational until test-mode checkout, webhook and reconciliation evidence has been captured.
3. Resend transactional email is implemented in code but should not be described as live until a verified sender/domain and the required Railway environment variables are configured.

## Final submission gate

Do not submit the final Faculty package until all of the following are true:

- Confirm `quantic-grader` has the required repository access.
- Recheck the GitHub repository, deployed BloomAI web app, Trello board, presentation links and any Google Drive evidence while signed out/incognito.
- Preserve the completed three-sprint evidence with stories, ownership, acceptance criteria and completion states.
- Preserve a final passing GitHub Actions run and successful Railway deployment.
- Rehearse customer registration/sign-in, vendor sign-in and product ownership controls.
- Rehearse product image upload and optional profile-photo upload/replace/remove behavior.
- Rehearse the administrator sign-in and executive analytics dashboard.
- Verify participant segmentation and the map’s explicit “awaiting coordinates” behavior for records without trusted latitude/longitude.
- Verify in-app notifications and preference save/reload behavior.
- Treat transactional email as provider-configuration pending unless a real verified sender test has succeeded.
- Keep Paystack in test mode until checkout/webhook/verification evidence is complete.
- Upload the actual 15–20 minute MP4/MOV to Google Drive, enable “Anyone with the link can view,” and place that direct URL beside the YouTube recording in the README and submission portal.

## Faculty submission index

- `README.md` — project overview, deployment links, capabilities and submission summary.
- `docs/CAPSTONE-COMPLIANCE.md` — this Faculty requirement/evidence matrix.
- `docs/DESIGN-AND-TESTING.md` — design, architecture, testing rationale and deployment choices.
- `docs/AGILE-EVIDENCE.md` — backlog and three-sprint evidence.
- `docs/DEMO-SCRIPT.md` — final demonstration structure.
- `docs/AI-TOOLING.md` — AI tooling disclosure.
- `docs/PRODUCTION-VERIFICATION.md` — production verification evidence.
- `docs/PRODUCTION_OPERATIONS.md` — operations, recovery and production procedures.
- `docs/PRODUCTION-COMPLETION-CHECKLIST.md` — final production/submission checklist.
