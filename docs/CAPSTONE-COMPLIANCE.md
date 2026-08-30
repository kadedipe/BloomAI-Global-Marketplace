# MSSE Capstone compliance matrix

This matrix maps the Quantic MSSE Capstone Handbook requirements to repository evidence. Status is deliberately conservative: a link placeholder is not counted as complete.

| Faculty requirement | Repository evidence | Status | Completion action |
|---|---|---|---|
| Accessible, documented GitHub repository | README, service READMEs, source comments, CI | Complete | Add `quantic-grader` as repository collaborator |
| Working deployed web application | [BloomAI production](https://bloomai-web-production.up.railway.app), Railway IaC and production smoke workflow | Complete | Re-run the full browser rehearsal immediately before recording |
| Accessible agile task board | Trello link in README and `AGILE-EVIDENCE.md` | Partial | Ensure all delivered stories, owners and completion states are current |
| At least three sprints | `AGILE-EVIDENCE.md` | Documented | Attach real meeting/demo links where available |
| Design and testing document | `DESIGN-AND-TESTING.md` | Complete |
| Architecture patterns and rationale | Design document and ADRs | Complete |
| Deployment choice and cost implications | Design document and Railway runbook | Complete |
| Automated testing and rationale | Service tests, CI and design document | Complete |
| CI/CD collaboration | `.github/workflows/ci.yml` | Complete |
| Appropriate AI tooling evidence | `AI-TOOLING.md` | Complete; update continuously |
| 15–20 minute recorded demonstration | `DEMO-SCRIPT.md` | Pending external action | Record one MP4 with screen share, voice, visible presenter and ID; upload to public-view Google Drive |
| Group Project Agreement final page | Not stored because it contains signatures/personal data | Pending external action | Submit directly through Quantic dashboard if working as a group |

## Current rubric projection

- Repository engineering evidence: score 5 trajectory.
- Final submission today: score 3–4 because deployment URL, grader access, current board evidence and final video cannot be completed inside source control.
- Score 5 becomes defensible after every pending external action above is completed and the deployed demonstration succeeds end to end.
