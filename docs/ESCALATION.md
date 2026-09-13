# Escalation Policy & Exception Handling (ADR-001 §5.5)

This document specifies the exception triggers, automated escalation artifacts, and human decision workflows for Antinode Norma.

---

## 1. Trigger Matrix & Action Policy

| Trigger Event | Action & Response |
|---|---|
| **Plan rejected twice** | Stop execution. Summarize plan changes and request human decision. |
| **Verification fails twice** | Stop execution. Attach failure logs/diagnostics and request human approval of revised plan. |
| **Task already done** | Report existing implementation evidence and propose task closure. |
| **Assumptions don't hold** | Report codebase mismatch. Halt task and wait for re-scoping. |
| **External API down during eval** | Mark evaluation status as `degraded`. Skip external call, notify operator, and continue offline checks. |
| **Cost exceeds threshold** | Fail evaluation (`cost_per_run > $0.02`). Require prompt and token budget review. |
| **Missing required secret** | Fail fast immediately with error pointing operator to `.env.example`. |
| **Missing optional secret** | Skip optional feature, log warning message, and continue normal pipeline. |
| **Security issue detected** | Stop execution immediately and open a security blocking issue. |

---

## 2. Escalation Artifact Schema (`build/escalation.json`)

When an automated escalation trigger occurs, the platform generates `build/escalation.json` containing detailed error diagnostics:

```json
{
  "timestamp": "2026-09-12T18:00:00Z",
  "task_id": "P0-T05",
  "phase": "P0",
  "trigger": "VERIFICATION_FAILED_TWICE",
  "message": "Unit test regression detected after two attempts.",
  "attempts": 2,
  "logs": "build/logs/verification_attempt_2.log",
  "status": "AWAITING_HUMAN_DECISION"
}
```

---

## 3. GitHub Issue Creation Workflow

Automated escalations generate a GitHub issue using `.github/ISSUE_TEMPLATE/blocked_task.md` to notify engineering leads and track resolution.
