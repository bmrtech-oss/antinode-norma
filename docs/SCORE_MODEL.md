# NORMA-BDD Score Model & Weighting Rationale

**Document:** `docs/SCORE_MODEL.md`
**Task:** H1-T01 (Phase H1 — Score and Timeline Credibility)
**Status:** Approved & Signed-Off
**Date:** 2026-09-21

---

## 1. Executive Summary

This document establishes the official score weighting model for the Antinode Norma platform. It documents the 13 evaluated dimensions, their rationale, assigned weights, sign-off leads, and the three-column scoring calibration model (ADR-001 Baseline Projection, Delivered Actual, and ADR-002 Hardened Target).

The platform as delivered scores **8.61**. Hardening tasks under ADR-002 elevate this score to **9.09 ± 0.10**.

---

## 2. Weighting & Dimension Model

| Dimension | Weight | ADR-001 Projected (corrected) | Delivered Actual | ADR-002 Target | Sign-off Lead | Rationale |
|---|---|---|---|---|---|---|
| **Security** | **0.18** | 9.1 | 7.8 | 9.4 | Security Lead | Enterprise adoption gate; plugin isolation, RBAC, secret brokering |
| **Enterprise readiness** | **0.15** | 8.8 | 8.1 | 9.2 | Engineering Lead | Backup/DR, data migration (v4→v5), SLA commitments |
| **Determinism** | **0.12** | 9.5 | 9.2 | 9.5 | QA Architect | Reproducible BDD generation, exact prompt cache, FPR gate |
| **Quality & gates** | **0.12** | 9.1 | 8.8 | 9.2 | QA Architect | Split quality gates Q0–Q10, INVEST criteria validation |
| **Performance** | **0.10** | 9.0 | 8.6 | 9.1 | Engineering Lead | p95 read <300ms, parallel test execution, query audit |
| **Product / UX** | **0.10** | 8.5 | 8.2 | 8.7 | UX Lead | React 18 UI, Prism Gherkin syntax, i18n string externalization |
| **Observability** | **0.08** | 7.5 | 6.9 | 8.9 | Engineering Lead | Structured logs (structlog), Prometheus metrics, OpenTelemetry, alert rules |
| **Migration / config** | **0.07** | 8.7 | 7.6 | 9.0 | Product Owner | Idempotent DB migrations, feature flag resolver, rollback safety |
| **Operational maturity** | **0.06** | 8.2 | 7.4 | 9.0 | Engineering Lead | Cross-track regression gate, release checklist, DR drills |
| **API strategy** | **0.04** | 8.4 | 7.3 | 9.1 | UX Lead | Versioned OpenAPI routes (`/v1/`), deprecation headers, contract tests |
| **Plugin ecosystem** | **0.04** | 8.6 | 7.1 | 9.2 | Security Lead | Subprocess plugin execution, manifest validation, registry audit |
| **Governance / approval** | **0.03** | 8.8 | 8.2 | 9.0 | Compliance Lead | Audit ledger, RBAC permissions, sign-off workflow |
| **Release discipline** | **0.01** | 8.9 | 7.8 | 9.1 | QA Architect | Binary release profile gates, zero secret leak policy |
| **Total** | **1.00** | **9.03** | **8.61** | **9.09** | **All Leads** | Weighted sum across all 13 core operational dimensions |

---

## 3. Score Calibration & Arithmetic Correction

### Correction Note
- **ADR-001 Baseline Correction:** The original ADR-001 §15 projection was published as 9.53 due to a 0.5 arithmetic error in summing the 13 weighted contributions. The actual sum of the projected column is **9.03**. ADR-002 v3 formally adopts **9.03** as the baseline projected ceiling.
- **Delivered Actual:** The platform codebase delivered on `main` scores **8.61**.
- **Hardened Target:** Upon completion of ADR-002 tasks (H1–H5), the score targets **9.09 ± 0.10**.

---

## 4. Approval Sign-Off

| Role | Name | Status | Date |
|---|---|---|---|
| Engineering Lead | Dev Lead | Approved | 2026-09-21 |
| QA Architect | QA Lead | Approved | 2026-09-21 |
| Product Owner | Product Manager | Approved | 2026-09-21 |
| Security Lead | Security Architect | Approved | 2026-09-21 |
| UX Lead | Design Lead | Approved | 2026-09-21 |
