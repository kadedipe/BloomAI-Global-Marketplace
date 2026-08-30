# MSSE Capstone compliance matrix

This matrix maps the Quantic MSSE Capstone Handbook requirements to repository and production evidence. Status is conservative: external actions are not counted as complete until their links and access have been verified from a signed-out browser.

| Faculty requirement | Evidence | Status | Completion action |
|---|---|---|---|
| Accessible, documented GitHub repository | README, service source, tests, CI and PR history | Complete | Invite GitHub user `quantic-grader` before submission |
| Working deployed web application | [BloomAI production](https://bloomai-web-production.up.railway.app), Railway IaC and health checks | Complete | Rehearse the complete user journey immediately before recording |
| Accessible agile task board | Trello link in README and `AGILE-EVIDENCE.md` | External verification required | Confirm signed-out access; update delivered stories, owners, acceptance criteria and completion states |
| At least three sprints | `AGILE-EVIDENCE.md` | Documented | Add real sprint meeting and increment-demo links where available |
| Design and testing document | `DESIGN-AND-TESTING.md` | Complete | Final proofreading |
| Architecture patterns and rationale | Design report, monorepo boundaries and operational documentation | Complete | None |
| Deployment choice and cost implications | Design report, Railway IaC and production runbook | Complete | Add current plan-cost evidence if Faculty expects it |
| Automated testing and rationale | Service, model-contract and frontend tests; CI; staging E2E workflow | Complete | Capture final passing CI evidence |
| CI/CD collaboration | `.github/workflows/ci.yml`, pull requests and Railway GitHub deployment | Complete | Capture the final successful workflow/deployment |
| Appropriate AI tooling evidence | `AI-TOOLING.md`, training provenance and production model verification | Complete | Keep disclosure current |
| Working AI capability | MobileNetV3 Small, 102 classes, five predictions in production | Complete | Capture browser evidence during the final rehearsal |
| Managed product media | Cloudinary upload, persisted CDN URL, preview and fallback behavior | Complete | Capture create/edit/delete ownership evidence |
| Payment foundation | Server-authoritative Paystack initialization and verification contracts | Implemented; external test required | Configure Paystack test mode and evidence checkout, webhook and verification |
| 15–20 minute recorded demonstration | `DEMO-SCRIPT.md` | External action required | Record one MP4 with screen share, voice, visible presenter and required ID; upload to Google Drive with “Anyone with the link can view” |
| Group Project Agreement final page | Not stored because it contains signatures/personal data | External action if group-based | Submit directly through the Quantic dashboard |

## Current rubric projection

The repository, deployed application, AI inference, production architecture, testing and CI/CD evidence support a highest-band trajectory. A score-5 submission is not yet claimed because grader access, signed-out Trello verification, final Paystack evidence (if demonstrated), real sprint evidence and the final 15–20 minute public-view recording remain external completion steps.

## Final submission gate

Do not submit until all of the following are true:

- GitHub user `quantic-grader` can access the repository.
- Every README, Trello and Google Drive link works in a signed-out/incognito browser.
- Trello reflects at least three sprints, owners, acceptance criteria and completed user stories.
- The production rehearsal covers registration, persistent sign-in, Cloudinary product publishing, edit/delete ownership, logout, API documentation and five AI predictions.
- The final MP4 is 15–20 minutes, includes the required presenter/ID evidence and is shared as “Anyone with the link can view.”
- The final video URL replaces the pending statement in the README.
