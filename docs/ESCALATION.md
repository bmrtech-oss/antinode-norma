# Escalation Policy & Trigger Matrix — Antinode Norma

This document defines automated and agent escalation triggers, recovery actions, and blocked task issue generation.

---

## 1. Escalation Trigger Matrix

| Trigger | Automated Action | Required Resolution |
|---|---|---|
| **Plan Rejected Twice** | Stop task execution immediately | Summarize options and await explicit human decision |
| **Verification Fails Twice** | Stop task execution, attach failure logs | Require human approval of updated plan |
| **Task Already Completed** | Stop execution, provide evidence | Propose task closure |
| **Assumptions Do Not Hold** | Report mismatch | Pause task until requirement re-scoping |
| **External API Down During Eval** | Skip live eval, mark status `degraded` | Log warning and proceed with cached mock eval |
| **Cost Gate Exceeded (> $0.02)** | Fail eval cycle | Require prompt review and optimization |
| **Required Secret Missing** | Fail-fast at startup | Pointer to `.env.example` and missing key |
| **Security Risk / Leak Detected** | Halt CI/CD pipeline immediately | Open security incident issue |

---

## 2. Escalation Artifacts

When an escalation trigger occurs:
1. An escalation summary JSON file is written to `build/escalation.json`.
2. A GitHub Issue is populated using the blocked task issue template (`.github/ISSUE_TEMPLATE/blocked_task.md`).
