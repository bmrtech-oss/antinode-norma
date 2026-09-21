# NORMA-BDD Hardening Schedule (P10 / P50 / P80 Dates)

**Document:** `docs/SCHEDULE.md`
**Task:** H1-T02 (Phase H1 — Score and Timeline Credibility)
**Status:** Published
**Date:** 2026-09-21

---

## 1. Executive Summary

This schedule details the implementation timeline for all 18 tasks across the 5 hardening phases (H1–H5) defined in ADR-002. The timeline includes P10 (optimistic), P50 (expected), and P80 (committed) delivery dates with a 20% critical path buffer. **P80 is the official commitment date for stakeholder reporting.**

---

## 2. Phase-Level Timeline Overview

```text
Week:  1     2     3     4     5     6
H1     ███
H2     ██████████
H3           ██████
H4                 ██████
H5                       ██████
```

| Phase | P10 Date | P50 Date | P80 Target Commitment | Critical Path? |
|---|---|---|---|---|
| **H1 — Score and Timeline Credibility** | Week 1.0 | Week 1.2 | **Week 1.5** | **Yes** |
| **H2 — Enterprise Completeness** | Week 2.5 | Week 3.0 | **Week 3.5** | **Yes** |
| **H3 — Architectural Contradictions** | Week 2.5 | Week 3.0 | **Week 3.5** | No |
| **H4 — Operational Maturity** | Week 4.0 | Week 4.5 | **Week 5.0** | **Yes** |
| **H5 — Convergence, Buffer & Release** | Week 5.0 | Week 5.5 | **Week 6.5** | **Yes** |

---

## 3. Granular Task Schedule (18 Hardening Tasks)

| Task ID | Task Title | Track | P10 Target | P50 Target | P80 Target | Status |
|---|---|---|---|---|---|---|
| **H1-T01** | Publish score weighting rationale (`docs/SCORE_MODEL.md`) | Cross-track | Week 0.5 | Week 0.8 | Week 1.0 | **Completed** |
| **H1-T02** | Publish P50/P80 schedule (`docs/SCHEDULE.md`) | Cross-track | Week 0.8 | Week 1.0 | Week 1.2 | **Completed** |
| **H1-T03** | Publish approval SLA & delegation policy (`docs/APPROVALS.md`) | Cross-track | Week 1.0 | Week 1.2 | Week 1.5 | Pending |
| **H2-T01** | v4 → v5 data migration script & dry-run | Track A | Week 1.5 | Week 2.0 | Week 2.2 | Pending |
| **H2-T02** | Backup, restore & DR drills (`docs/DR.md`) | Track B | Week 1.8 | Week 2.2 | Week 2.5 | Pending |
| **H2-T03** | Observability stack (logs, metrics, traces, alerts) | Track B | Week 2.0 | Week 2.5 | Week 2.8 | Pending |
| **H2-T04** | Load & performance testing (`tests/load/`) | Track B | Week 2.2 | Week 2.8 | Week 3.0 | Pending |
| **H2-T05** | API versioning (`/v1/`) & deprecation policy | Track C | Week 2.5 | Week 3.0 | Week 3.2 | Pending |
| **H2-T06** | i18n string externalization (`locales/en.json`) | Track C | Week 2.5 | Week 3.0 | Week 3.5 | Pending |
| **H3-T01** | Plugin security model remediation (subprocess isolation) | A+B+C | Week 2.0 | Week 2.5 | Week 2.8 | Pending |
| **H3-T02** | Cache false-positive evaluation gate (FPR < 2%) | Track A | Week 2.2 | Week 2.8 | Week 3.0 | Pending |
| **H3-T03** | Migration reversibility correction & Alembic tests | Track A | Week 2.5 | Week 3.0 | Week 3.2 | Pending |
| **H3-T04** | Soft-gate timing documentation & CLI `--strict` flag | Track A | Week 2.5 | Week 3.0 | Week 3.5 | Pending |
| **H4-T01** | Cross-track regression gate in CI | Cross-track | Week 3.5 | Week 4.0 | Week 4.5 | Pending |
| **H4-T02** | Release checklist (`docs/RELEASE_CHECKLIST.md`) | Cross-track | Week 3.8 | Week 4.2 | Week 4.8 | Pending |
| **H4-T03** | Post-implementation re-scoring & delta publishing | Cross-track | Week 4.0 | Week 4.5 | Week 5.0 | Pending |
| **H5-T01** | Convergence buffer (1 week) | Cross-track | Week 4.5 | Week 5.0 | Week 5.8 | Pending |
| **H5-T02** | Documentation consolidation & cross-referencing | Cross-track | Week 4.8 | Week 5.2 | Week 6.0 | Pending |
| **H5-T03** | Hardening release (v2.1.0) | Cross-track | Week 5.0 | Week 5.5 | **Week 6.5** | Pending |

---

## 4. SLA & Approval Delegation Rules

1. **Track-Level Approvals:** Track leads approve task pull requests within their own track within a 72-hour SLA.
2. **Cross-Track Approvals:** Required for frozen shared files (`core/agent.py`, `cli.py`, `server/api.py`), security permissions, or public API breaking changes.
3. **Escalation Path:** If approval exceeds 72 hours, task status escalates automatically per `docs/ESCALATION.md`.
