# Platform Architecture — Antinode Norma BDD Platform

This document describes the high-level architecture, internal data structures, pipeline execution model, and module interactions for the Antinode Norma BDD Platform (v2.0).

---

## 1. Architectural Overview

Antinode Norma is an enterprise-grade, collaborative BDD platform that transforms unstructured or semi-structured user requirements into validated Gherkin `.feature` specifications and executable test suites.

```text
[User Story / Requirement / Ingest Source]
                   │
                   ▼
       [Structured Ingestion Layer]
          (CSV, XLSX, Story Adapter)
                   │
                   ▼
         [Unified Intermediate Representation (IR)]
        (TestCase, DomainModel, GateResult, Verdict)
                   │
                   ▼
       [NormaAgent Pipeline & Repair Loop]
      (Prompt Builders, LLM Call, Quality Gates Q0–Q10)
                   │
         ┌─────────┴─────────┐
         ▼                   ▼
[Quality Gates Evaluation] [Governance & Delivery]
 (Hard Q0-Q5, Soft Q6-Q10)  (Audit Hash, Approval Gate,
                             Traceability, TestRail, Xray)
         │                   │
         └─────────┬─────────┘
                   ▼
    [Execution Maturity & Distribution]
    (Parallel Runner, Cloud Grids, Artifact Capture)
                   │
                   ▼
    [Ecosystem, Collaboration & UI]
    (FastAPI / REST API, React SPA, OIDC/RBAC, Plugins)
```

---

## 2. Core Components & Modules

### 2.1 Intermediate Representation (`antinode_norma/core/types.py`)
- **`TestCase`**: Represents a single scenario requirement with ID, title, description, tags, Given/When/Then steps, and metadata.
- **`DomainModel`**: Holds domain entities, definitions, and relationships parsed from `model.yaml`.
- **`GateResult`**: Outcome of a single quality gate evaluation, including score, status, and feedback messages.
- **`Verdict`**: Aggregated result across all hard and soft gates, determining pass/fail status and repair necessity.

### 2.2 Quality Gate System (`antinode_norma/gates/`)
- **Hard Gates (Q0–Q5)**: Hard criteria required for valid Gherkin generation:
  - **Q0**: Basic Gherkin & INVEST validator.
  - **Q1**: Gherkin syntax correctness.
  - **Q2**: No RSpec / non-Gherkin keywords (`describe`, `it`, `should`).
  - **Q3/Q4**: Traceability tags (`@TestCase.id`) present on scenarios without orphan tags.
  - **Q5**: No duplicate scenario names.
- **Soft Gates & Judge (Q6–Q10)**: Style, reuse, and semantic quality checks:
  - **Q6**: Declarative style score (≥ 0.90 threshold).
  - **Q7**: Step vocabulary reuse (≥ 0.90 threshold).
  - **Q8**: Scenario Outline usage for tabular parameters (= 1.00 threshold).
  - **Q9**: State transitions / Given-When-Then structure (= 1.00 threshold).
  - **Q10**: LLM Semantic Judge evaluation (≥ 0.85 threshold).

### 2.3 Unified Agent & Repair Loop (`antinode_norma/core/agent.py`)
- **`NormaAgent`**: Orchestrates feature generation and quality assessment.
- **Repair Loop**: When quality gates fail during single-pass generation, `NormaAgent` enters an error-feedback repair loop (up to 3 attempts), sending failing gate messages back to the LLM to auto-correct Gherkin syntax and quality issues.

### 2.4 Governance & Delivery (`antinode_norma/governance/`, `antinode_norma/delivery/`)
- **Audit Trail**: SHA-256 content-hashed immutable event logging.
- **Approval Gate**: Reviewer workflow managing `pending`, `approved`, and `rejected` states.
- **Traceability Renderer**: Maps requirements to scenarios, gates, and delivery target links.
- **Delivery Adapters**: Syncs approved Gherkin features to external test management systems (TestRail, Xray).

### 2.5 Execution Maturity (`antinode_norma/execution/`)
- **Parallel Executor**: Multithread/multiprocess parallel scenario runner.
- **Retry & Flake Detector**: Backoff retries and execution flake scoring.
- **Artifact Capture & Reporters**: Screenshot/video/trace capture with JUnit, Allure, and HTML reporters.
- **Cloud Grid Drivers**: Support for BrowserStack, Sauce Labs, and LambdaTest.

### 2.6 Web UI, Auth & Ecosystem (`antinode_norma/server/`, `antinode_norma/ecosystem/`, `antinode_norma/collaboration/`)
- **FastAPI Server**: REST API providing feature endpoints, approvals, audit logs, comments, notifications, and analytics. All routes versioned under `/v1/` prefix per ADR-002 (§H2-T05).
- **React SPA**: Static SPA served at `/` with interactive dashboard, feature viewer, approval queue, and externalized i18n (`ui/src/locales/en.json`) per ADR-002 (§H2-T06).
- **SSO & RBAC**: OIDC (PKCE) and SAML 2.0 authentication with role-based access control (`admin`, `reviewer`, `generator`, `viewer`).
- **Plugin System**: Manifest-driven plugin registry with brokered secret isolation (`SecretBroker`), restricted filesystem scope, and domain allowlists per ADR-002 (§H3-T01).

---

## 3. Post-Implementation Hardening (ADR-002)

The architecture includes the post-implementation hardening layer (ADR-002 Tasks H1–H5):
- **Backup & DR (`antinode_norma/core/backup.py`)**: SQLite `VACUUM INTO` snapshots with integrity verification (`PRAGMA quick_check`). See `docs/DR.md`.
- **v4 → v5 Migration (`antinode_norma/core/migrate_v4.py`)**: Idempotent data migration with `--dry-run` support. See `docs/MIGRATION.md`.
- **Observability Stack (`antinode_norma/utils/observability.py`)**: Prometheus metrics, `/health`, `/metrics`, and request correlation IDs.
- **Cross-Track Regression Gate (`bin/run_regression_gate.py`)**: CI release gate executing unit tests, walking skeleton, load tests, and DR smoke checks. See `docs/RELEASE_CHECKLIST.md`.
- **Hardening Summary**: Complete task mapping and verification details are recorded in `docs/HARDENING_SUMMARY.md`.
