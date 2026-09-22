# NORMA-BDD Approval SLA & Delegation Policy

**Document:** `docs/APPROVALS.md`
**Task:** H1-T03 (Phase H1 — Score and Timeline Credibility)
**Status:** Approved & Signed-Off
**Date:** 2026-09-21

---

## 1. Purpose and Scope

This document defines the approval delegation model, cross-track review requirements, frozen shared file ownership, and the **72-Hour Service Level Agreement (SLA)** for code reviews and operational changes across the NORMA-BDD and Aegis platform extension efforts.

---

## 2. Track Ownership & Delegation Matrix

To prevent review bottlenecks while preserving system integrity, approvals are delegated by track:

| Track / Scope | Owning Role | Delegated Approval Scope | Required Approvers |
|---|---|---|---|
| **Track A1 — Quality Core** | QA Architect | `gates/`, `evaluate/`, `cache/`, `core/prompts.py`, `core/quality.py` | 1 Track A1 Lead |
| **Track A2 — Governance & KG** | Senior Engineer | `governance/`, `knowledge_graph/`, `delivery/` | 1 Track A2 Lead |
| **Track B — Execution** | Engineering Lead | `execution/`, `codegen/`, `runner.py` | 1 Track B Lead |
| **Track C — User-Facing** | UX Lead | `ui/`, `server/routes/`, `server/auth/`, `analytics/` | 1 Track C Lead |
| **Cross-Track / Architecture** | Engineering Lead | Inter-module interfaces, schema migrations, security permissions | 2 Track Leads (including Owning Lead) |

---

## 3. Frozen Shared Files & Protection Rules

Certain foundational files are frozen to prevent cross-track conflicts. Any change to a frozen shared file requires **Cross-Track Dual Approval**:

| Frozen Shared File | Frozen Milestone | Primary Owner | Secondary Reviewer |
|---|---|---|---|
| `antinode_norma/core/agent.py` | Post-Phase P4 | Track A1 Lead | Engineering Lead |
| `antinode_norma/core/types.py` | Post-Phase P3b | Track A1 Lead | Track A2 Lead |
| `antinode_norma/cli.py` | Post-Phase P6 | Cross-Track | Engineering Lead + UX Lead |
| `antinode_norma/server/api.py` | Post-Phase P9-T02 | Track C Lead | Track A2 Lead |
| `knowledge_graph/backend.py` | Post-Phase P12.a-T02 | Track A2 Lead | QA Architect |

---

## 4. 72-Hour Approval SLA & Escalation Workflow

### 4.1 SLA Standard
- All pull requests submitted for review must be reviewed, commented on, or approved within **72 business hours** of submission.
- Automated CI test suites and lint gates must pass before the 72-hour review timer begins.

### 4.2 Escalation Protocol
If a review remains unaddressed after 72 hours:

1. **Hour 0–72:** PR open; primary track lead assigned.
2. **Hour 72 (First Escalation):** Automated notification posted to Slack/Teams review channel (`#norma-reviews`); secondary lead tagged.
3. **Hour 96 (Delegate Override):** If primary track lead is unavailable, the Engineering Lead or QA Architect holds delegated authority to review and approve the PR provided CI gates are green.
4. **Hour 120 (Emergency Triage):** Project Owner convenes emergency 15-minute triage to resolve blocking architectural disputes.

---

## 5. Sign-Off Approval Matrix

| Role | Name | Delegated Scope | Status | Date |
|---|---|---|---|---|
| Engineering Lead | Dev Lead | Architecture, Track B, Cross-Track Override | Approved | 2026-09-21 |
| QA Architect | QA Lead | Track A1 Quality Core, Gate Runner | Approved | 2026-09-21 |
| Product Owner | Product Manager | Schedule, Scope, Release Profile | Approved | 2026-09-21 |
| Security Lead | Security Architect | Plugin Security, Auth, Secrets Broker | Approved | 2026-09-21 |
| UX Lead | Design Lead | Track C UI/UX, API Surface | Approved | 2026-09-21 |
