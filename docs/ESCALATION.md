# Escalation Policy & Trigger Matrix — Antinode Norma

This document defines automated and agent escalation triggers, recovery actions,
and blocked task issue generation. The trigger matrix is aligned with ADR-003
Section 5.5 and is authoritative for the foundation release profile.

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
| **Optional Secret Missing** | Skip dependent feature | Log warning and continue |
| **Security Risk / Leak Detected** | Halt CI/CD pipeline immediately | Open security incident issue |
| **Low-Confidence Judge Score** | Pause automated acceptance | Route to SME review queue |
| **Knowledge Graph Unavailable (Q11, production)** | Fail closed | Block release and escalate |
| **Knowledge Graph Unavailable (Q11, development)** | Fail open | Warn and continue |
| **Knowledge Graph Unavailable (Q12)** | Fail open | Warn and continue |
| **Reuse Candidate Abandoned Upstream** | Reassess dependency | Evaluate adapter replacement and flag Tier 1 risk |
| **Tier 3 Task Should Be Tier 2** | Stop task execution | Produce evidence and escalate to track lead |

---

## 2. Escalation Artifacts

When an escalation trigger occurs:
1. An escalation summary JSON file is written to `build/escalation.json`.
2. A GitHub Issue is populated using the blocked task issue template (`.github/ISSUE_TEMPLATE/blocked_task.md`).

The issue must preserve the trigger, task identifier, evidence, attempted
remediation, owner, and explicit decision required from a human reviewer.

## 3. Resolution and Stop Rules

- An agent stops after two rejected plans or two failed verification attempts.
- A blocked task remains blocked until the required reviewer records a decision.
- A degraded external evaluation must be labeled `degraded`; cached or mock
  results must not be presented as live-provider evidence.
- Security findings always take precedence over ordinary task recovery.
