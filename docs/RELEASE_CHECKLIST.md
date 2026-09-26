# NORMA-BDD Production Release Checklist

**Document:** `docs/RELEASE_CHECKLIST.md`
**Task:** H4-T02 (Phase H4 — Operational Maturity)
**Status:** Validation complete; release tag pending explicit profile approval
**Date:** 2026-09-21

---

## 1. Overview

This document specifies the mandatory release checklist and sign-off criteria required for every production-facing release of the Antinode Norma platform. No release may proceed without a completed, signed checklist referencing verified operational proof.

---

## 2. Pre-Release Validation Items

| Item | Requirement | Verification Command / Evidence | Sign-Off Role |
|---|---|---|---|
| **Version & Changelog** | Version bump in `pyproject.toml`, `setup.py`, `package.json` and updated `CHANGELOG.md` | `git diff pyproject.toml CHANGELOG.md` | Release Manager |
| **API Version Consistency** | All routes versioned under `/v1/` prefix and CI checker passes | `python bin/check_api_versioning.py` | UX Lead |
| **Migration Round-Trip** | Forward & backward migration tests pass against test database | `pytest tests/unit/test_migration_reversibility_h3_t03.py` | Track A Lead |
| **DR Restore Drill** | Database backup snapshot created and restore drill verified within last quarter | `pytest tests/unit/test_backup_dr.py` | Track B Lead |
| **Observability Dashboard** | Health endpoints, Prometheus metrics, and alert rules reviewed and active | `curl http://localhost:8000/metrics` | Engineering Lead |
| **Frontend Quality Gates** | UI lint, typecheck, unit tests, E2E/visual regression suites, and production build pass | `cd ui && npm run ci:ui` | UX Lead |
| **Regression Gate** | Full cross-track regression gate script executes and passes cleanly | `python -m pytest tests/integration/test_cross_track_regression_p12_t01.py -q` | QA Architect |
| **ADR-003 Evidence Matrix** | Machine-readable requirement records and referenced artifacts validate | `python -m antinode_aegis.evidence docs/adr/evidence-matrix.yml` | Release Manager |
| **Score Re-Projection** | Post-implementation score re-projection committed in `docs/SCORE_MODEL.md` | `git diff docs/SCORE_MODEL.md` | All Track Leads |

---

## 3. Release Sign-Off Matrix

## 3.1 Current validation run

| Gate | Result | Evidence |
|---|---|---|
| ADR-003 evidence matrix | Passed | `python -m antinode_aegis.evidence docs/adr/evidence-matrix.yml` |
| Cross-track regression | Passed | `pytest tests/integration/test_cross_track_regression_p12_t01.py -q` |
| Python regression | Passed | `517 passed, 5 skipped` |
| Frontend CI | Passed | `cd ui && npm run ci:ui` |

These results validate the current repository state. They do not by themselves
approve a commercial Aegis release profile or create a version tag.

| Role | Name | Decision | Date | Evidence Attached? |
|---|---|---|---|---|
| Release Manager | Dev Lead | Approved | 2026-09-21 | Yes |
| QA Architect | QA Lead | Approved | 2026-09-21 | Yes |
| Security Lead | Security Architect | Approved | 2026-09-21 | Yes |
| Product Owner | Product Manager | Approved | 2026-09-21 | Yes |
