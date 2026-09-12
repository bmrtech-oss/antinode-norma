# ADR-001: NORMA-BDD — Antinode Norma Platform Extension

**Single-file architecture decision record.**

---

## Metadata

| Field | Value |
|---|---|
| **ADR ID** | ADR-001 |
| **Version** | v6 (consolidated) |
| **Title** | Extend Antinode Norma into a deterministic, collaborative, enterprise-grade BDD platform |
| **Status** | Proposed |
| **Date** | 2026-09-12 |
| **Deciders** | Engineering Lead, QA Architect, Product Owner, Security Lead, UX Lead |
| **Supersedes** | v1–v5 |
| **Target Score** | ≥ 9.5 / 10 |
| **Target Duration** | 11–13 weeks (parallelized) |

---

## 1. Context

Antinode Norma is our own repository — a BDD agent that transforms user stories into Gherkin and executable tests, with INVEST input gates, MCP-native integration, codegen, and a pure-core design.

We need to extend it with deterministic output gates, CSV/XLSX ingest, prompt-hash caching, traceability enforcement, audit trail, an evaluation harness, a web UI, SSO/RBAC, execution maturity, an ecosystem layer, and collaboration features — reaching a **9.5 / 10** platform score.

v6 uses a **walking-skeleton, parallel-track** delivery model: end-to-end by week 5, three parallel tracks after the skeleton, converging at the end.

---

## 2. Decision

**We will extend Antinode Norma using a discovery-first agent workflow, with explicit operational controls, delivered via a walking skeleton and three parallel tracks.**

1. **No fork.** Work directly on our repository.
2. **Discovery-first tasks.** Every task defines *what* and *why*, never *how*. The agent inspects code, proposes a plan, waits for approval.
3. **Single product.** One package (`norma`), one CLI (`anorm`), one config file, one test suite.
4. **Walking skeleton at P4 (week 5).** End-to-end pipeline runs before widening.
5. **Split gates.** Hard gates (Q0–Q5) land before the agent; soft gates and judge (Q6–Q10) land after.
6. **Three parallel tracks after P4:** A (Quality), B (Execution), C (User-facing).
7. **Operational foundations first (P0).** Secrets, cost, git, rollback, escalation, UI spike.
8. **Scope: 83 tasks across 14 phases, 11–13 weeks** with 2–3 reviewers.
9. **Score target: 9.5 / 10.** Quality unchanged from v5; delivery faster.

---

## 3. Consequences

### Positive

- **Working system at week 5** (vs week 10 in sequential plans).
- **Parallel tracks** cut total duration from 14–18 weeks to 11–13.
- **Data-driven tuning:** eval harness exists before soft gates land.
- **Enterprise-ready:** SSO, RBAC, audit, approval, rollback, cost gates.
- **Ecosystem:** plugin API, SDK, collaboration, analytics.

### Negative

- **Requires 2–3 reviewers** for parallel execution. Sequential reverts to ~16 weeks.
- **14 phases, 83 tasks** — more coordination overhead.
- **New surface area:** frontend, auth, DB, plugin security.

### Neutral

- Scope is identical to v5. Score projection is unchanged.
- CLI remains the primary automation interface.

---

## 4. Alternatives Considered

| Alternative | Why rejected |
|---|---|
| Fork + wrapper (v1) | Unnecessary when we own the repo |
| Prescriptive code ADR (v2) | Stale code; brittle to repo evolution |
| Discovery-first without ops (v3) | Under-specified secrets, cost, rollback |
| Sequential phases (v5) | Walking skeleton delayed to week 10 |
| Build from scratch | Duplicates Norma's INVEST, codegen, MCP |

---

## 5. Operational Foundations

These apply to every phase and are prerequisites, not tasks.

### 5.1 Secrets

- `.env` git-ignored; `.env.example` committed.
- `python-dotenv` loads at CLI startup.
- Missing required secret → fail-fast with pointer to `.env.example`.
- CI secrets in GitHub Actions. No secrets in committed files, logs, or errors.
- `gitleaks` on every PR and on `main`.
- Quarterly rotation, tracked in `docs/SECRETS.md`.

**`.env.example` keys:**

```text
# LLM providers
OPENAI_API_KEY=
ANTHROPIC_API_KEY=

# Delivery
TESTRAIL_URL=
TESTRAIL_USER=
TESTRAIL_PASSWORD=
TESTRAIL_PROJECT_ID=
XRAY_BASE_URL=
XRAY_TOKEN=
XRAY_PROJECT_KEY=

# Notifications
SLACK_WEBHOOK_URL=
TEAMS_WEBHOOK_URL=

# Runtime overrides
NORMA_LLM_PROVIDER=openai
NORMA_LLM_MODEL=gpt-4o-mini
NORMA_CACHE_PATH=build/llm_cache.json
NORMA_LOG_PROMPTS=false
```

### 5.2 Cost Model

| Item | Value |
|---|---|
| Avg generation prompt | 2,000 in / 1,500 out tokens |
| Avg judge prompt | 3,000 in / 500 out tokens |
| Model | gpt-4o-mini |
| Cost per run (2 attempts + judge) | ~$0.003 |
| Cost per eval cycle (N=10) | ~$0.03 |
| Cost with 70% cache hit | ~$0.001/run |

**Cost gate:** eval fails if `cost_per_run > $0.02`. Every LLM call logged to `build/llm_cost.jsonl`.

### 5.3 Git Workflow

```
main                    ← stable, tagged releases
  └── norma-bdd         ← long-lived integration branch
        ├── task/P0-T01-secrets-strategy
        └── task/P4-T03-repair-loop
```

- One branch per task: `task/<PHASE>-<TASK-ID>-<slug>`.
- One PR per task, target `norma-bdd`, squash-merge.
- Required checks: lint, unit, integration, contracts (if API touched), gitleaks, cost gate (P6+).
- Commit convention: `<type>(<scope>): <subject>` + `Task:`, `Phase:`, `Track:` trailers.
- Merge freeze during phase exit gate validation.
- Tags on `main` only, annotated, format `v<major>.<minor>.<patch>`.

### 5.4 Rollback and Feature Flags

All high-risk changes gated by flags in `norma.config.yml`:

```yaml
features:
  unified_agent: false
  cache_exact: false
  cache_semantic: false
  governance_audit: false
  governance_approval: false
  auth_saml: false
  execution_cloud: false
  edge_discovery: false
```

Resolution: default → config → env (`NORMA_FEATURE_<NAME>`) → CLI.

**Lifecycle:** Introduce (flag off) → Soak (5 days on in non-prod) → Default-on → Retire (after 2 releases).

**Every high-risk task includes a soak plan.** Every PR is revertible with `git revert <sha>`.

### 5.5 Escalation Policy

| Trigger | Action |
|---|---|
| Plan rejected twice | Stop. Summarize. Require human decision. |
| Verification fails twice | Stop. Attach logs. Require human approval of next plan. |
| Task already done | Report with evidence. Propose closure. |
| Assumptions don't hold | Report mismatch. Wait for re-scoping. |
| External API down during eval | Skip eval. Mark `degraded`. Notify. |
| Cost exceeds threshold | Fail eval. Require prompt review. |
| Secret missing (required) | Fail-fast with pointer to `.env.example`. |
| Secret missing (optional) | Skip feature. Log warning. Continue. |
| Security issue detected | Stop immediately. Open security issue. |

Escalations produce `build/escalation.json` and a GitHub issue from `.github/ISSUE_TEMPLATE/blocked_task.md`.

### 5.6 Persistence

- SQLite (single-node) or PostgreSQL (multi-node).
- Alembic migrations; every migration reversible.
- Domains: `users`, `roles`, `sessions`, `features`, `scenarios`, `approvals`, `comments`, `executions`, `artifacts`, `audit_events`.
- When `features.database` is off, platform runs in v4 file-based mode.

### 5.7 Frontend Stack

- React 18 + TypeScript + Vite + Tailwind + React Query + Recharts.
- Deployed as static build served by FastAPI or nginx.
- OIDC Authorization Code + PKCE; tokens in memory, not `localStorage`.
- WCAG 2.1 AA; Lighthouse ≥ 90.

### 5.8 Plugin Security

- Plugins trusted once installed. No sandboxing.
- `plugin.yaml` declares permissions: `read:features`, `write:gates`, `network:external`, etc.
- Capability object passed to hooks; permission enforcement at runtime.
- Curated registry with CI scanning (`bandit`, `pip-audit`, `gitleaks`).
- Hook failure logged, not fatal.

### 5.9 Track Coordination

| Track | Lead | Owns |
|---|---|---|
| A | QA Architect | `gates/`, `evaluate/`, `cache/`, `governance/`, `hybrid/`, `server/mcp_server.py`, `delivery/` |
| B | Engineering Lead | `execution/`, `codegen/`, `core/runner.py` |
| C | UX Lead | `ui/`, `server/api.py`, `server/routes/`, `server/auth/`, `collaboration/`, `analytics/` |

- Weekly 30-min sync.
- Frozen after P4: `core/agent.py`. After P3b: `core/types.py`. After P6: `cli.py`. After P9-T02: `server/api.py`.
- Capacity: 1 reviewer → ~16 weeks; 2 reviewers → ~13 weeks; 3 → ~11 weeks.

---

## 6. Agent Workflow Contract

```text
1. DISCOVER  — read ADR; inspect repo; cite files read; note blockers
2. PLAN      — files + reasons, interfaces, tests, verification, cost,
               rollback (if high-risk), track, risks, LOC estimate
3. WAIT      — print "AWAITING APPROVAL — reply APPROVE, REJECT, or AMEND". Stop.
4. IMPLEMENT — after APPROVE only; one file at a time; re-approve on deviations
5. VERIFY    — run declared commands + full regression + contract tests
6. REPORT    — files with line counts, tests, deviations, PR link, next task
```

---

## 7. Target Repository Structure

```text
antinode-norma/
├── core/                          # extended
│   ├── quality.py                 # Norma: INVEST
│   ├── gherkin_generator.py       # + cache wiring
│   ├── validator.py               # becomes Q0
│   ├── parser.py, schemas.py, runner.py
│   ├── config.py                  # + gates/cache/gov/delivery/hybrid/features
│   ├── agent.py                   # NEW: unified pipeline
│   ├── normalize.py               # NEW
│   ├── types.py                   # NEW: TestCase, DomainModel, GateResult, Verdict
│   ├── prompts.py                 # NEW
│   ├── model_loader.py            # NEW
│   └── features.py                # NEW: flag resolver
├── gates/                         # NEW: Q0-Q10
│   ├── types.py, aggregate.py, norma_validator.py
│   ├── syntax.py, rspec_guard.py, traceability.py, duplicates.py
│   ├── declarative.py, reuse.py, outline.py, state.py
│   ├── semantic.py, prompts.py, runner.py
├── ingest_structured/             # NEW: csv.py, xlsx.py, story.py
├── cache/                         # NEW: exact.py, semantic.py
├── governance/                    # NEW: audit.py, approval.py, trace.py
├── hybrid/                        # NEW: discovery.py, review.py
├── delivery/                      # NEW: testrail.py, xray.py
├── evaluate/                      # NEW: metrics.py, cost.py
├── execution/                     # NEW: parallel, retry, artifacts, reporters, cloud, flake
├── ui/                            # NEW: React app
├── ecosystem/                     # NEW: plugins, sdk, marketplace
├── collaboration/                 # NEW: comments, notifications
├── analytics/                     # NEW: trends, coverage, dashboards
├── server/                        # extended
│   ├── mcp_server.py              # + tools
│   ├── api.py                     # NEW: FastAPI
│   ├── auth/                      # NEW: oidc, saml, session, roles, middleware
│   ├── routes/                    # NEW
│   └── schemas.py                 # NEW
├── codegen/, connectors/          # unchanged
├── tests/                         # extended
│   ├── unit/, integration/, connectors/
│   ├── contracts/                 # NEW: public API
│   ├── ui/, auth/, execution/, plugins/
│   └── eval/                      # golden dataset + metrics
├── cli.py                         # extended
├── model.yaml                     # NEW
├── norma.config.yml               # extended
├── .env.example                   # NEW
├── docker-compose.yml             # NEW
├── Dockerfile.api, Dockerfile.ui  # NEW
├── pyproject.toml                 # extended
└── docs/
    ├── adr/ADR-001-norma-bdd-platform.md   ← this file
    ├── ARCHITECTURE.md, QUALITY_GATES.md, CONFIGURATION.md
    ├── SECRETS.md, COST.md, GIT_WORKFLOW.md, ROLLBACK.md, ESCALATION.md
    ├── TRACKS.md, UI.md, AUTH.md, EXECUTION.md, PLUGINS.md
    └── CHANGELOG.md
```

---

## 8. Phased Implementation Plan

**14 phases. 83 tasks. 11–13 weeks parallelized (16 sequential).**

| Phase | Track | Tasks | Duration | Purpose |
|---|---|---|---|---|
| P0 | — | 6 | Week 1 | Foundations + UI spike |
| P1 | — | 7 | Week 2 | Baseline, IR, contracts |
| P2 | — | 6 | Week 3 | Structured ingest |
| P3a | — | 5 | Week 4 | Hard gates Q0–Q5 |
| **P4** | — | **6** | **Week 5** | **Walking skeleton** |
| P5 | A | 7 | Week 6 | Eval + cache + cost |
| P6 | A | 3 | Week 7 | MCP tools |
| P3b | A | 5 | Week 8 | Soft gates + Q10 |
| P7 | A | 6 | Week 9 | Governance + delivery |
| P8 | B | 7 | Week 6–9 | Execution maturity |
| P9 | C | 8 | Week 8–11 | Web UI |
| P10 | C | 6 | Week 10 | SSO + RBAC |
| P11 | A+B+C | 7 | Week 10–12 | Ecosystem + collaboration |
| P12 | — | 4 | Week 13 | Analytics + release |

### Timeline

```text
Week:  1   2   3   4   5   6   7   8   9  10  11  12  13
P0     ██
P1         ██
P2             ██
P3a                ██
P4                     ██  ← Walking skeleton
P5                         ██
P6                             ██  ← MCP available
P3b                                ██
P7                                     ██
P8                         ████████  ← Execution (parallel)
P9                                 ████████  ← UI (parallel)
P10                                        ██
P11                                        █████  ← Convergence
P12                                             ██
```

### Task Index

| Phase | Task | Title | Track | Approval |
|---|---|---|---|---|
| P0 | T01 | Secrets strategy | — | Yes |
| P0 | T02 | Cost model documentation | — | Yes |
| P0 | T03 | Git workflow documentation | — | Yes |
| P0 | T04 | Rollback and feature flags | — | Yes |
| P0 | T05 | Escalation policy | — | No |
| P0 | T06 | UI spike | — | Yes |
| P1 | T01 | Establish baseline | — | No |
| P1 | T02 | Public API contract tests | — | Yes |
| P1 | T03 | Shared IR | — | Yes |
| P1 | T04 | Domain model loader | — | Yes |
| P1 | T05 | Extend configuration schema | — | Yes |
| P1 | T06 | Header normalization module | — | No |
| P1 | T07 | Phase 1 checkpoint | — | No |
| P2 | T01 | CSV ingester | — | No |
| P2 | T02 | XLSX ingester | — | Conditional |
| P2 | T03 | Story adapter | — | No |
| P2 | T04 | Unified normalize | — | No |
| P2 | T05 | CLI subcommands | — | Yes |
| P2 | T06 | Phase 2 integration test | — | No |
| P3a | T01 | Gate types, aggregator, Q0 | — | No |
| P3a | T02 | Q1 syntax + Q2 no-RSpec | — | No |
| P3a | T03 | Q3/Q4 traceability | — | No |
| P3a | T04 | Q5 duplicates | — | No |
| P3a | T05 | Gate runner + validation | — | Yes |
| P4 | T01 | Prompt builders | — | Yes |
| P4 | T02 | Agent skeleton | — | Yes |
| P4 | T03 | Repair loop | — | Yes |
| P4 | T04 | Refactor Norma path (flagged) | — | Yes |
| P4 | T05 | Repair loop integration test | — | No |
| P4 | T06 | Phase 4 checkpoint | — | No |
| P5 | T01 | Exact prompt cache | A | No |
| P5 | T02 | Wire cache (flagged) | A | Yes |
| P5 | T03 | Semantic cache (flagged) | A | Yes |
| P5 | T04 | Evaluation harness | A | Yes |
| P5 | T05 | Cost tracker | A | No |
| P5 | T06 | Eval CI job | A | Yes |
| P5 | T07 | Phase 5 checkpoint | A | No |
| P6 | T01 | MCP tools | A | No |
| P6 | T02 | MCP integration test | A | No |
| P6 | T03 | Phase 6 checkpoint | A | No |
| P3b | T01 | Q6 declarative style | A | Yes |
| P3b | T02 | Q7 reuse | A | No |
| P3b | T03 | Q8 outline | A | No |
| P3b | T04 | Q9 state model | A | No |
| P3b | T05 | Q10 semantic judge + wire | A | Yes |
| P7 | T01 | Audit trail | A | No |
| P7 | T02 | Approval gate | A | No |
| P7 | T03 | Traceability renderer | A | No |
| P7 | T04 | Wire governance (flagged) | A | Yes |
| P7 | T05 | TestRail delivery | A | No |
| P7 | T06 | Xray delivery + docs | A | No |
| P8 | T01 | Parallel execution | B | No |
| P8 | T02 | Retry with backoff | B | No |
| P8 | T03 | Artifact capture | B | No |
| P8 | T04 | Reporters | B | No |
| P8 | T05 | Cloud runners | B | Yes |
| P8 | T06 | Flake detection | B | No |
| P8 | T07 | Execution history + docs | B | No |
| P9 | T01 | API foundation | C | Yes |
| P9 | T02 | Feature viewer endpoint | C | No |
| P9 | T03 | Frontend scaffold | C | Yes |
| P9 | T04 | Feature review page | C | No |
| P9 | T05 | Approval queue page | C | Yes |
| P9 | T06 | Traceability + audit pages | C | No |
| P9 | T07 | Dashboard | C | No |
| P9 | T08 | UI deployment + docs | C | Yes |
| P10 | T01 | User and role model | C | Yes |
| P10 | T02 | OIDC integration | C | Yes |
| P10 | T03 | SAML integration (flagged) | C | Yes |
| P10 | T04 | Permission middleware | C | Yes |
| P10 | T05 | User action audit | C | No |
| P10 | T06 | Admin settings + docs | C | Yes |
| P11 | T01 | Plugin manifest and registry | A+B+C | Yes |
| P11 | T02 | Plugin hooks and lifecycle | A+B+C | Yes |
| P11 | T03 | Plugin SDK package | A+B+C | Yes |
| P11 | T04 | Comments and mentions | A+B+C | No |
| P11 | T05 | Notifications | A+B+C | Yes |
| P11 | T06 | Analytics dashboard | A+B+C | No |
| P11 | T07 | Phase 11 docs and eval | A+B+C | Yes |
| P12 | T01 | Cross-track regression | — | No |
| P12 | T02 | Documentation consolidation | — | Yes |
| P12 | T03 | Analytics polish | — | No |
| P12 | T04 | Release | — | Yes |

---

## 9. Phase Details

### Phase 0 — Operational Foundations

**Goal:** Establish secrets, cost, git, rollback, escalation, UI spike.
**Exit criteria:** All foundation docs exist; `.env.example` committed; gitleaks passes; UI spike report written.

- **P0-T01** Secrets strategy. Deliver: `.env.example`, `docs/SECRETS.md`, gitleaks CI hook, fail-fast check. Approval: Yes.
- **P0-T02** Cost model. Deliver: `docs/COST.md` with baseline, gates, cache ROI. Approval: Yes.
- **P0-T03** Git workflow. Deliver: `docs/GIT_WORKFLOW.md`, PR template. Approval: Yes.
- **P0-T04** Rollback + flags. Deliver: `core/features.py`, `docs/ROLLBACK.md`. Approval: Yes.
- **P0-T05** Escalation policy. Deliver: `docs/ESCALATION.md`, blocked-task issue template. Approval: No.
- **P0-T06** UI spike. Deliver: `spike/ui/` PoC, `docs/UI.md` seed, go/no-go recommendation. Approval: Yes.

### Phase 1 — Baseline and Shared IR

**Goal:** Confirm repo state, lock public contracts, introduce IR.
**Exit criteria:** Norma's tests pass; contracts locked; IR + config extended.

- **P1-T01** Establish baseline. Record SHA, Python version, test counts.
- **P1-T02** Public API contract tests. Lock CLI, MCP tools, `generate_feature`. Approval: Yes.
- **P1-T03** Shared IR. `TestCase`, `DomainModel`, `GateResult`, `Verdict`. Approval: Yes.
- **P1-T04** Domain model loader. `model.yaml` + loader. Approval: Yes.
- **P1-T05** Extend config schema. `gates`, `cache`, `governance`, `delivery`, `hybrid`, `features`. Approval: Yes.
- **P1-T06** Header normalization. `core/schema.py` with aliases + `split_multi`.
- **P1-T07** Phase 1 checkpoint.

### Phase 2 — Structured Ingest

**Goal:** CSV + XLSX ingest, normalized, wired to CLI.
**Exit criteria:** `anorm generate-from-csv` and `generate-from-xlsx` produce valid `.feature`.

- **P2-T01** CSV ingester. `CSVIngester.ingest(path) -> list[TestCase]`.
- **P2-T02** XLSX ingester. `XLSXIngester(sheet_name).ingest(path)`. Approval: conditional on new dep.
- **P2-T03** Story adapter. `story_to_case(story: dict) -> TestCase`.
- **P2-T04** Unified normalize. `normalize(source, kind, model) -> list[TestCase]`.
- **P2-T05** CLI subcommands. `generate-from-csv`, `generate-from-xlsx`. Approval: Yes.
- **P2-T06** Phase 2 integration test.

### Phase 3a — Hard Gates (Q0–Q5)

**Goal:** Syntax, no-RSpec, traceability, duplicates. Plus Q0 Norma validator.
**Exit criteria:** Gates implemented, runner works, validated against Norma's output.

- **P3a-T01** Gate types, aggregator, Q0.
- **P3a-T02** Q1 syntax + Q2 no-RSpec.
- **P3a-T03** Q3/Q4 traceability.
- **P3a-T04** Q5 duplicates.
- **P3a-T05** Gate runner + validation report. Approval: Yes.

### Phase 4 — Unified Agent (Walking Skeleton)

**Goal:** End-to-end CSV → agent → hard gates → `.feature` with repair loop.
**Exit criteria:** **First end-to-end milestone.**

- **P4-T01** Prompt builders. Approval: Yes.
- **P4-T02** Agent skeleton. Single-attempt generation + Q0–Q5. Approval: Yes.
- **P4-T03** Repair loop. Error-feedback retry, max 3 attempts. Approval: Yes.
- **P4-T04** Refactor Norma path behind flag. Approval: Yes (high-risk).
- **P4-T05** Repair loop integration test.
- **P4-T06** Phase 4 checkpoint. Declare tracks open.

### Phase 5 — Eval Harness and Cache (Track A)

**Goal:** Measure the skeleton, enable determinism.
**Exit criteria:** Eval thresholds met; cache proves byte-identical reruns.

- **P5-T01** Exact prompt cache.
- **P5-T02** Wire cache behind flag. Approval: Yes.
- **P5-T03** Semantic cache behind flag. Approval: Yes.
- **P5-T04** Evaluation harness. Golden file at `tests/eval/golden/account_details.feature`. Approval: Yes.
- **P5-T05** Cost tracker. `evaluate/cost.py`.
- **P5-T06** Eval CI job with cost gate. Approval: Yes.
- **P5-T07** Phase 5 checkpoint.

### Phase 6 — MCP Tools (Track A)

**Goal:** Expose the pipeline to AI assistants.
**Exit criteria:** MCP tools callable end-to-end.

- **P6-T01** MCP tools: `generate_from_csv`, `generate_from_xlsx`, `run_quality_gates`, `assess_story`.
- **P6-T02** MCP integration test.
- **P6-T03** Phase 6 checkpoint.

### Phase 3b — Soft Gates and Semantic Judge (Track A)

**Goal:** Add Q6–Q10 now that the pipeline runs and is measurable.
**Exit criteria:** Q6–Q10 wired into verdict.

- **P3b-T01** Q6 declarative style. Approval: Yes (pattern list policy).
- **P3b-T02** Q7 reuse.
- **P3b-T03** Q8 outline.
- **P3b-T04** Q9 state model.
- **P3b-T05** Q10 semantic judge + wire. Approval: Yes.

### Phase 7 — Governance and Delivery (Track A)

**Goal:** Audit, approval, traceability renderer, TestRail/Xray delivery.
**Exit criteria:** Approved feature reaches TestRail/Xray in test mode.

- **P7-T01** Audit trail. Immutable, content-hashed.
- **P7-T02** Approval gate. Pending/approved/rejected states.
- **P7-T03** Traceability renderer.
- **P7-T04** Wire governance behind flags. Approval: Yes.
- **P7-T05** TestRail delivery adapter.
- **P7-T06** Xray delivery adapter + docs.

### Phase 8 — Execution Maturity (Track B)

**Goal:** Match dedicated runners on parallel, retries, artifacts, cloud, flake detection.
**Exit criteria:** Tests run in parallel; artifacts captured; flake reports generated.

- **P8-T01** Parallel execution.
- **P8-T02** Retry with backoff.
- **P8-T03** Artifact capture (screenshots, video, traces).
- **P8-T04** Reporters (JUnit, Allure, HTML).
- **P8-T05** Cloud runners (BrowserStack, Sauce Labs, LambdaTest). Approval: Yes.
- **P8-T06** Flake detection.
- **P8-T07** Execution history + docs.

### Phase 9 — Web UI (Track C)

**Goal:** Review, approval, traceability, and dashboard on top of stable API.
**Exit criteria:** Reviewers can log in, view features, approve or reject, see audit.

- **P9-T01** API foundation (FastAPI). Approval: Yes.
- **P9-T02** Feature viewer endpoint.
- **P9-T03** Frontend scaffold (React + Vite + Tailwind). Approval: Yes.
- **P9-T04** Feature review page (Gherkin + gates + trace).
- **P9-T05** Approval queue page. Approval: Yes.
- **P9-T06** Traceability + audit pages.
- **P9-T07** Dashboard.
- **P9-T08** UI deployment + docs. Approval: Yes.

### Phase 10 — SSO and RBAC (Track C)

**Goal:** Enterprise auth + role enforcement.
**Exit criteria:** OIDC login works; roles enforced; actions audited.

- **P10-T01** User and role model. Approval: Yes.
- **P10-T02** OIDC integration. Approval: Yes (security).
- **P10-T03** SAML integration (flagged). Approval: Yes.
- **P10-T04** Permission middleware. Approval: Yes.
- **P10-T05** User action audit.
- **P10-T06** Admin settings + docs. Approval: Yes.

**Roles:** `admin`, `reviewer`, `generator`, `viewer`. Full permission matrix in §10.

### Phase 11 — Ecosystem and Collaboration (Convergent)

**Goal:** Plugin API, comments, notifications, analytics.
**Exit criteria:** Plugins load safely; users comment; notifications fire.

- **P11-T01** Plugin manifest + registry. Approval: Yes.
- **P11-T02** Plugin hooks + lifecycle. Approval: Yes.
- **P11-T03** Plugin SDK package. Approval: Yes.
- **P11-T04** Comments and mentions.
- **P11-T05** Notifications (email, Slack, Teams). Approval: Yes.
- **P11-T06** Analytics dashboard.
- **P11-T07** Phase 11 docs and eval. Approval: Yes.

### Phase 12 — Analytics, Polish, Release

**Goal:** Consolidate, final regression, release.
**Exit criteria:** Full suite passes; eval thresholds met; version tagged.

- **P12-T01** Cross-track regression.
- **P12-T02** Documentation consolidation. Approval: Yes.
- **P12-T03** Analytics polish. Lighthouse ≥ 90.
- **P12-T04** Release (v2.0.0). Approval: Yes.

---

## 10. Quality Gate Thresholds (ADR-002, consolidated)

### Hard gates

| Gate | Description |
|---|---|
| Q0 | Norma validator passes |
| Q1 | Valid Gherkin syntax |
| Q2 | No RSpec tokens (`describe`, `context`, `expect`, `should`, `let`, `before`, `after`) |
| Q3 | Every `TestCase.id` appears as `@`-tag |
| Q4 | No orphan tags |
| Q5 | No duplicate scenario names |

### Soft gates

| Gate | Threshold | Rationale |
|---|---|---|
| Q6 | Declarative style ≥ 0.90 | 90% intent-level steps |
| Q7 | Step reuse ≥ 0.90 | Encourages reusable vocabulary |
| Q8 | Outline usage = 1.00 | Combinatorial cases must use Scenario Outline |
| Q9 | State keywords = 1.00 | Target scenarios contain Given, When, Then |
| Q10 | Semantic judge ≥ 0.85 | LLM-judge agreement with experts ~80–90% |

### Aggregate

| Metric | Threshold |
|---|---|
| `hard_pass` | true |
| `soft_score` | ≥ 0.85 |
| `sem_score` | ≥ 0.85 |

### Eval thresholds

| Metric | Threshold | Rationale |
|---|---|---|
| `pass_rate` | ≥ 0.95 | Literature: 93.3% LLM syntax correctness |
| `first_attempt_syntax_rate` | ≥ 0.90 | Baseline + margin |
| `avg_attempts` | ≤ 1.50 | Target 80% first-attempt pass |
| `determinism_score` | ≥ 0.80 | Cache target 1.0; cold-cache variance |
| `ecr_at_1` | ≥ 0.80 | LAJ-Gherkin research |
| `avg_sem_score` | ≥ 0.85 | Same as Q10 |
| `cost_per_run` | ≤ $0.02 | 10× baseline |

**Re-baselining:** After P5-T04, thresholds re-validated. Any change requires an amendment.

---

## 11. LLM Provider Strategy (ADR-003, consolidated)

### Protocol

```python
class LLMClient(Protocol):
    def complete(self, prompt: str, system: str = "") -> str: ...
```

### Implementations

| Provider | Module | Use case |
|---|---|---|
| OpenAI | `llm/openai.py` | Default cloud |
| Anthropic | `llm/anthropic.py` | Long-context alternative |
| OpenRouter | `llm/openrouter.py` | Multi-provider routing |
| Ollama | `llm/local.py` | Privacy-sensitive |
| Mock | `llm/mock.py` | Tests |

### Default config

```yaml
llm:
  provider: openai
  model: gpt-4o-mini
  temperature: 0.2
  cache: true
  cache_path: build/llm_cache.json
```

- Missing key for selected provider → fail-fast.
- Provider error → retry once with backoff; escalate on second failure.
- Malformed JSON from judge → log; gate fails; retry.
- Cost logged per call.
- Model versions pinned where supported.
- Prompt logging off by default; `NORMA_LOG_PROMPTS=true` enables.

---

## 12. Authentication and Authorization (ADR-010, consolidated)

### Authentication

- **Primary:** OIDC (Auth Code + PKCE).
- **Secondary:** SAML 2.0 (flag `features.auth_saml`).
- **Dev fallback:** local `admin` when auth config absent (warning logged).

### Session

- HttpOnly cookie, Secure, SameSite=Lax.
- 8-hour lifetime; silent refresh.
- Server-side store (SQLite/Postgres).

### Roles and permissions

| Permission | admin | reviewer | generator | viewer |
|---|---|---|---|---|
| `features:read` | ✅ | ✅ | ✅ | ✅ |
| `features:generate` | ✅ | ❌ | ✅ | ❌ |
| `features:approve` | ✅ | ✅ | ❌ | ❌ |
| `features:reject` | ✅ | ✅ | ❌ | ❌ |
| `comments:write` | ✅ | ✅ | ✅ | ❌ |
| `executions:read` | ✅ | ✅ | ✅ | ✅ |
| `executions:run` | ✅ | ❌ | ✅ | ❌ |
| `audit:read` | ✅ | ✅ | ❌ | ✅ |
| `users:manage` | ✅ | ❌ | ❌ | ❌ |
| `settings:manage` | ✅ | ❌ | ❌ | ❌ |

Enforcement via `@requires("permission")` decorator. Unauthenticated → 401. Missing permission → 403.

Every write action logged to `audit_events` with `user_id`, `action`, `resource`, `result`, `ip`, `user_agent`.

---

## 13. Plugin Security Model (ADR-011, consolidated)

- **Trust:** Plugins trusted once installed. No sandbox.
- **Install:** Explicit `pip install` by admin. Discovery via entry points.
- **Manifest:** `plugin.yaml` declares name, version, author, permissions, hooks.
- **Permissions:** `read:features`, `write:gates`, `network:external`, `read:secrets`, `write:delivery`, etc.
- **Capability object:** Hooks receive capability, not internals.
- **CI scanning:** `bandit`, `pip-audit`, `gitleaks`, manifest schema validation.
- **Runtime:** Load failure → skip; hook failure → logged, non-fatal; hook timeout 5s → killed.
- **Revocation:** Admin disables per-project; compromised plugins removed from registry.

---

## 14. Track Coordination (ADR-012, consolidated)

### Ownership

| Track | Lead | Owns |
|---|---|---|
| A | QA Architect | `gates/`, `evaluate/`, `cache/`, `governance/`, `hybrid/`, `server/mcp_server.py`, `delivery/` |
| B | Engineering Lead | `execution/`, `codegen/`, `core/runner.py` |
| C | UX Lead | `ui/`, `server/api.py`, `server/routes/`, `server/auth/`, `collaboration/`, `analytics/` |

### Freezes

| File | Frozen after | Owner |
|---|---|---|
| `core/agent.py` | P4 | A |
| `core/types.py` | P3b | A |
| `cli.py` | P6 | cross-track |
| `server/api.py` | P9-T02 | C |

### Weekly sync

- 30 minutes every Monday.
- Agenda: blockers, shared-file conflicts, convergence approaching, cost + eval status.
- Minutes in `docs/TRACKS.md`.

### Convergence points

- **P4:** agent interface frozen; tracks fork.
- **P7:** governance wraps agent output.
- **P11:** ecosystem extends all tracks.
- **P12:** analytics reads all tracks.

### Capacity

| Reviewers | Tracks | Timeline |
|---|---|---|
| 1 | 1 | ~16 weeks |
| 2 | 2 | ~13 weeks |
| 3 | 3 | ~11 weeks |

---

## 15. Score Projection

| Dimension | Weight | Score | Contribution |
|---|---|---|---|
| Gherkin generation quality | 20% | 9.5 | 1.90 |
| Determinism / reproducibility | 12% | 9.5 | 1.14 |
| Traceability | 10% | 9.5 | 0.95 |
| Input flexibility | 8% | 9.0 | 0.72 |
| Enterprise readiness | 10% | 9.5 | 0.95 |
| Codegen | 4% | 8.0 | 0.32 |
| Execution | 8% | 8.5 | 0.68 |
| UI / UX | 10% | 8.5 | 0.85 |
| Collaboration | 5% | 7.5 | 0.38 |
| Ecosystem / plugins | 5% | 8.0 | 0.40 |
| Extensibility | 4% | 9.5 | 0.38 |
| Documentation | 2% | 9.0 | 0.18 |
| Cost efficiency | 2% | 9.0 | 0.18 |
| **Total** | **100%** | | **9.53** |

**Projected: 9.5 / 10.**

---

## 16. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Soft gates late; hard gates miss issues | Medium | Medium | P3b lands 3 weeks after P3a; eval catches regressions |
| UI blocked on API instability | Medium | High | API frozen at P6; contract tests |
| Track divergence | Low | Medium | Weekly sync; frozen shared files |
| Eval golden file staleness | Low | Low | Re-validate after each gate addition |
| UI spike fails | Low | High | Fallback to CLI-only v2.0 |
| Reviewer capacity | High | Medium | Cap concurrent tracks at reviewer count |
| Cost overrun | Medium | Medium | Cost gate; cache; prompt review |
| Plugin security incident | Low | High | Curated registry; capability enforcement |
| DB migration breaks deploy | Low | High | Every migration reversible; CI tests forward + backward |

---

## 17. Definition of Done

A task is Done when:

- [ ] Discovery cited at least one file inspected, with paths
- [ ] Plan output before any implementation
- [ ] Plan included cost, UI impact, DB migration (if applicable), and rollback plan (if high-risk)
- [ ] Track stated (A / B / C / cross-track); cross-track files flagged
- [ ] Explicit APPROVE received (or "No" gate respected)
- [ ] All declared files created/modified
- [ ] All declared tests pass
- [ ] Verification commands run and output shown
- [ ] Norma's full regression suite passes
- [ ] Contract tests pass if public API, CLI, MCP, or UI routes touched
- [ ] No secret leaks introduced
- [ ] No deviations from plan, or deviations re-approved
- [ ] Docs updated per phase requirement
- [ ] Report output with next task ID and PR link

A phase is Done when all its tasks are Done and the phase exit gate passes.

---

## 18. Status Tracking

| Phase | Track | Status | Tasks Done | Blocked By |
|---|---|---|---|---|
| P0 — Foundations | — | Not started | 0/6 | — |
| P1 — Baseline + IR | — | Not started | 0/7 | P0 |
| P2 — Structured ingest | — | Not started | 0/6 | P1 |
| P3a — Hard gates | — | Not started | 0/5 | P2 |
| P4 — Walking skeleton | — | Not started | 0/6 | P3a |
| P5 — Eval + cache | A | Not started | 0/7 | P4 |
| P6 — MCP tools | A | Not started | 0/3 | P5 |
| P3b — Soft gates | A | Not started | 0/5 | P6 |
| P7 — Governance + delivery | A | Not started | 0/6 | P3b |
| P8 — Execution | B | Not started | 0/7 | P4 |
| P9 — Web UI | C | Not started | 0/8 | P6 |
| P10 — SSO + RBAC | C | Not started | 0/6 | P9 |
| P11 — Ecosystem + collaboration | A+B+C | Not started | 0/7 | P7, P8, P10 |
| P12 — Analytics + release | — | Not started | 0/4 | P11 |

---

## 19. Key Metrics

| Metric | Value |
|---|---|
| Total tasks | 83 |
| Total phases | 14 |
| Parallel tracks | 3 |
| Walking skeleton | Week 5 |
| MCP available | Week 7 |
| Execution runs | Week 9 |
| UI live | Week 11 |
| Release | Week 13 |
| Total duration (parallel) | 11–13 weeks |
| Total duration (sequential) | ~16 weeks |
| Projected platform score | 9.5 / 10 |

---

## 20. Appendix — Agent Prompt

The prompt to start execution lives alongside this ADR or in the team's runbook. It instructs the agent to:

1. Read this ADR at `docs/adr/ADR-001-norma-bdd-platform.md`.
2. Begin at Phase P0, Task P0-T01.
3. Follow the Discovery → Plan → Wait → Implement → Verify → Report cycle.
4. Never implement without explicit APPROVE.
5. Escalate per §5.5 after 2 failed attempts.

For the full prompt text, see the team's agent runbook or the previous conversation turn where it was defined.

---

**End of ADR-001 v6 (consolidated).**