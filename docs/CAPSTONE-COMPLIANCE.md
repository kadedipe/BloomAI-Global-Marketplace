# MSSE Capstone compliance matrix

This matrix maps the Quantic MSSE Capstone Handbook requirements to repository and production evidence. Status is conservative: external actions are not counted as complete until their links and access have been verified from a signed-out browser.

| Faculty requirement | Evidence | Status | Completion action |
|---|---|---|---|
| Accessible, documented GitHub repository | README, service source, tests, CI and PR history | Complete | `quantic-grader` invited (user-confirmed) |
| Working deployed web application | [BloomAI production](https://bloomai-web-production.up.railway.app), Railway IaC and health checks | Complete | Rehearse the complete user journey immediately before recording |
| Accessible agile task board | Trello link in README and `AGILE-EVIDENCE.md` | Complete (user-validated) | Perform one final signed-out access check immediately before submission |
| At least three sprints | `AGILE-EVIDENCE.md` | Complete | Preserve real meeting/demo links where available |
| Design and testing document | `DESIGN-AND-TESTING.md` | Complete | Final proofreading |
| Architecture patterns and rationale | Design report, monorepo boundaries and operational documentation | Complete | None |
| Deployment choice and cost implications | Design report, Railway IaC and production runbook | Complete | Add current plan-cost evidence if Faculty expects it |
| Automated testing and rationale | Service, model-contract and frontend tests; CI; staging E2E workflow | Complete | Capture final passing CI evidence |
| CI/CD collaboration | `.github/workflows/ci.yml`, pull requests and Railway GitHub deployment | Complete | Capture the final successful workflow/deployment |
| Appropriate AI tooling evidence | `AI-TOOLING.md`, training provenance and production model verification | Complete | Keep disclosure current |
| Working AI capability | MobileNetV3 Small, 102 classes, five predictions in production | Complete | Capture browser evidence during the final rehearsal |
| Managed product media | Cloudinary upload, persisted CDN URL, preview and fallback behavior | Complete | Capture create/edit/delete ownership evidence |
| Payment foundation | Server-authoritative Paystack initialization and verification contracts | Implemented; external test required | Configure Paystack test mode and evidence checkout, webhook and verification |
| 15–20 minute recorded demonstration | [YouTube presentation](https://youtube.com/live/AffW_CxeEks?feature=share) and `DEMO-SCRIPT.md` | Recorded; hosting format pending | Add the actual Google Drive MP4 URL with “Anyone with the link can view” to satisfy the Faculty specification |
| Group Project Agreement final page | Not stored because it contains signatures/personal data | External action if group-based | Submit directly through the Quantic dashboard |

## Current rubric projection

The repository, deployed application, AI inference, Cloudinary media, production architecture, testing, CI/CD, agile evidence, grader invitation and recorded presentation support a highest-band trajectory. The remaining strict-format risk is that the supplied presentation link resolves to YouTube while the Faculty handbook specifies the actual MP4/MOV hosted on Google Drive. Paystack test evidence is required only if payments are claimed or demonstrated as fully operational.

## Final submission gate

Do not submit until all of the following are true:

- Confirm the `quantic-grader` invitation is accepted or otherwise grants the required access.
- Recheck every README, Trello, YouTube and Google Drive link in a signed-out/incognito browser.
- Preserve three-sprint stories, owners, acceptance criteria, tasks and completion states on Trello.
- Retain the successful production rehearsal covering registration, persistent sign-in, Cloudinary publishing, product ownership controls, logout, API documentation and five AI predictions.
- Upload the actual 15–20 minute MP4/MOV to Google Drive, enable “Anyone with the link can view,” and add that direct file-view URL beside the YouTube recording.
