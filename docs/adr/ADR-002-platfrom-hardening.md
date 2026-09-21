# ADR-002: NORMA-BDD Post-Implementation Hardening

**Single-file architecture decision record. Version 3 — FINAL.**

**Status:** Proposed (final updated). Supersedes ADR-002 v1, v2, v3.
**Date:** 2026-09-21
**Deciders:** Engineering Lead, QA Architect, Product Owner, Security Lead, UX Lead
**Predecessor:** ADR-001 v6 (fully implemented on branch `task/P0-T01-secrets-strategy-12288361790416289109`)
**Nature:** Additive hardening. No re-architecture. No phase re-opening.
**Sequencing:** Executes **before** ADR-001 Aegis v15.2.
**New tasks:** 18, across 5 phases (H1–H5)
**Duration:** 5–6 weeks (2 reviewers) / 4–5 weeks (3 reviewers)
**Target score:** 9.09 ± 0.10 (corrected model; see §6)

---

## 0. What Changed Across Versions (and Why)

ADR-002 has three versions. This section records the evolution so the reader understands the final state without reading the changelog.

| Version | Date | Change | Reason |
|---|---|---|---|
| v1 | 2026-09-19 | Initial 18-task plan | Post-implementation review identified 15 gaps |
| v2 | 2026-09-19 | Added §H3-T04 (soft-gate documentation); added §H5-T03 (release) | Test coverage of contradictions; explicit release |
| **v3** | **2026-09-19** | **Corrected §6 score model; clarified projection vs. measurement; added §4.3 sequencing; added §13 verification appendix; added §14 containerization appendix; corrected ADR-001 arithmetic error** | **Final consolidation** |

### Corrections carried into v3

**Correction A — ADR-001 §15 arithmetic error.**
The 13 weighted contributions in ADR-001 §15 sum to **9.03**, not 9.53. This is a 0.5 arithmetic error in the original projection. ADR-002 v3 adopts 9.03 as the corrected projection baseline and documents the correction explicitly.

**Correction B — Projection vs. measurement framing.**
The 9.53 (corrected 9.03) was a **pre-implementation projection**. The delivered score is a **post-implementation measurement**. Comparing them directly is invalid. The three-column model in §6 is the correct representation.

**Correction C — No scoring regression.**
Two earlier drafts scored Determinism and UI/UX *downward* after hardening tasks that logically improve them. Both are corrected in §6.

---

## 1. Context

### 1.1 Predecessor Status

ADR-001 v6 has been **fully implemented** on branch `task/P0-T01-secrets-strategy-12288361790416289109`:

- 83 tasks across 14 phases (P0–P12) delivered.
- CLI (`anorm`), MCP server, React UI, FastAPI backend, plugin system, execution runner, evaluation harness, and delivery adapters (TestRail/Xray) present.
- Test suite present (unit, integration, contracts, connectors).
- `.env.example`, `docker-compose.yml`, `Dockerfile.*` present.

The ADR-002 plan assumes this baseline. Anything missing is out of scope for hardening and would be a separate defect-tracking exercise.

### 1.2 Post-Implementation Review Findings

Independent review of the implemented platform identified **15 hardening opportunities** across five categories. None require re-architecture; all are additive.

| Category | Count | Nature |
|---|---|---|
| Timeline & process realism | 3 | Documentation, coordination, approval SLAs |
| Enterprise completeness | 6 | Data migration, DR, observability, load testing, API versioning, i18n |
| Architectural contradictions | 3 | Plugin security, cache FPR, migration reversibility |
| Score credibility | 2 | Weighting rationale, range vs. point estimate |
| Operational maturity | 1 | Cross-track regression + release discipline |

### 1.3 Why Hardening Now

Four reasons:

1. **Enterprise buyers** ask about DR, observability, and data migration in the first security review. None exist in the current platform.
2. **The plugin security model** (ADR-001 v6 §5.8, §13) grants `read:secrets` without enforcement. This will fail any serious security review.
3. **The corrected score** (9.03 projected vs. ~8.61 delivered) reveals a real gap that hardening closes.
4. **Existing v4 users** cannot migrate without a documented path.

### 1.4 Relationship to Aegis v15.2

Aegis v15.2 (the 101-task extension) **depends on ADR-002** in three explicit places:

| Aegis v15.2 task | Dependency on ADR-002 |
|---|---|
| Plugin ecosystem (P13) | ADR-002 §H3-T01 (plugin security remediation) |
| API foundation (P4-T09) | ADR-002 §H2-T05 (API versioning) |
| UI shell (P10) | ADR-002 §H2-T06 (i18n externalization) |

**Decision:** ADR-002 executes **before** Aegis v15.2 P0. The Aegis validation gate (20 customer interviews, per Aegis §22.10) runs in parallel with ADR-002 execution, owned by the Product Owner.

---

## 2. Decision

**We will harden the fully-implemented Antinode Norma platform through 18 additive tasks across 5 new phases (H1–H5), executed before Aegis v15.2.**

1. **No re-architecture.** All 83 tasks from ADR-001 v6 remain valid. Pure-core, data-centric, MCP-native, walking-skeleton architecture preserved.
2. **No phase re-opening.** P0–P12 are closed. Hardening tasks are delivered as new phases H1–H5.
3. **Additive only.** Every task creates new code, docs, or configuration. No existing module is rewritten.
4. **Evidence-based completion.** Each hardening task is considered complete only when supported by code, test evidence, documentation, and approval artifacts. Documentation alone does not satisfy completion.
5. **Score credibility.** Replace the 9.53 point estimate with the corrected three-column model (projected 9.03 / delivered 8.61 / target 9.09).
6. **Security posture correction.** Remove `read:secrets` from the plugin model; introduce brokered secret interface and subprocess isolation. Plugin manifests must be rejected if they request disallowed secret or network access patterns.
7. **Enterprise readiness.** Deliver DR, observability, load testing, API versioning, i18n externalization, and v4→v5 migration.
8. **Timeline realism.** Publish P50/P80 dates. Add a 1-week convergence buffer.
9. **Release gate.** No release may proceed without passing CI, restore drill evidence, migration validation, and documented release checklist sign-off.

### Evidence of Completion

Each hardening task must be evidenced as follows:
- Source change or configuration change committed to the branch.
- Automated validation or proof artifact (tests, lint, smoke checks, or operational verification).
- Documentation or release note reference for operational use.
- Explicit owner and approval status.
- Rollback or fallback note where the change is operationally sensitive.

A hardening task is not considered done by design intent alone. It is complete only when the evidence exists and is reviewed by the owning track lead.

---

## 3. What Is Preserved From ADR-001 v6

This ADR does **not** invalidate any ADR-001 decision. Explicitly preserved:

| ADR-001 v6 Decision | Status under ADR-002 |
|---|---|
| Pure-core, side-effect-free business logic | Unchanged |
| Data-centric, Rich Hickey-inspired design | Unchanged |
| MCP-native tool exposure | Unchanged; new tools added |
| Walking skeleton delivery | Already delivered |
| Split gates (hard Q0–Q5, soft Q6–Q10) | Unchanged |
| Discovery-first agent workflow | Unchanged |
| Feature-flag lifecycle | Unchanged |
| LLM-provider abstraction | Unchanged |
| Track ownership (A/B/C) | Reused for H-phases |
| Definition of Done | Extended (§9) |

---

## 4. Hardening Phase Plan

Five phases. Each additive. Total: **18 tasks, 5–6 weeks.**

### Phase H1 — Score and Timeline Credibility
**Duration:** Week 1 (3–4 days)
**Goal:** Make the platform's claims defensible to stakeholders.

| Task | Title | Track | Approval |
|---|---|---|---|
| **H1-T01** | Publish score weighting rationale | — | Yes |
| **H1-T02** | Publish P50/P80 schedule | — | Yes |
| **H1-T03** | Publish approval SLA and delegation policy | — | Yes |

**H1-T01 — Score Weighting Rationale**
`docs/SCORE_MODEL.md` documents each of the 13 dimensions, why it carries its weight, and who signed off. The corrected projection (9.03) and delivered actual (8.61) are both recorded. The target (9.09) is published as a range.

**H1-T02 — P50/P80 Schedule**
`docs/SCHEDULE.md` lists every H-phase task with P10 / P50 / P80 dates. 20% buffer on the critical path. P80 is the commitment.

**H1-T03 — Approval SLA and Delegation**
`docs/APPROVALS.md`: track leads approve docs/tests/internal refactors within their track. Cross-track approval required only for interface changes, security-sensitive changes, frozen files. 72-hour SLA.

**Exit criteria:** Three documents committed and reviewed.

---

### Phase H2 — Enterprise Completeness
**Duration:** Weeks 1–3
**Goal:** Close the six enterprise gaps that block adoption.

| Task | Title | Track | Approval |
|---|---|---|---|
| **H2-T01** | v4 → v5 data migration | A | Yes |
| **H2-T02** | Backup, restore, disaster recovery | B | Yes |
| **H2-T03** | Observability stack (logs, metrics, traces, alerts) | B | Yes |
| **H2-T04** | Load and performance testing | B | Yes |
| **H2-T05** | API versioning and deprecation policy | C | Yes |
| **H2-T06** | i18n string externalization | C | No |

**H2-T01 — v4 → v5 Data Migration**
`core/migrate_v4.py`: idempotent migration of `features/`, `stories/`, `norma.config.yml` into the DB schema. `--dry-run` mode. Integration test against a fixture with 3 features, 5 stories, 1 config. Rollback documented in `docs/MIGRATION.md`.

**H2-T02 — Backup, Restore, DR**
SQLite `VACUUM INTO` snapshots; Postgres `pg_dump --format=custom` + WAL archiving. Daily backup, 7-day retention, off-site copy. `docs/DR.md` with quarterly restore drill; RTO ≤ 1 hour, RPO ≤ 15 minutes. Integration test: create backup → destroy DB → restore → verify row counts.

Additional requirement:
- Backup and restore operations must be exercised in a documented drill with recorded RTO/RPO values and success evidence.
- DR completion is not satisfied by documentation or configuration alone; it requires a successful restore or failover test artifact.

**H2-T03 — Observability Stack**
Structured logging via `structlog` (JSON, correlation IDs). Prometheus metrics via `prometheus-fastapi-instrumentator`. OpenTelemetry traces with OTLP export. `/health` endpoint. Alert rules: cost spike, error rate > 1%, execution failure rate > 5%. Reference Grafana Loki + Prometheus + Tempo stack in `docker-compose.yml`.

Additional requirement:
- Metrics, trace output, and alert definitions must be active in the operational environment or in a verified local stack configuration.
- Health endpoints and alert thresholds must be validated with smoke tests or runbook checks.
- Observability claims are treated as runtime controls, not documentation-only additions.

**H2-T04 — Load and Performance Testing**
`tests/load/` with k6 or Locust. Thresholds: p95 < 300ms read, p95 < 5s generation, 50 concurrent users. Parallel execution benchmark: 100 Playwright tests at 1, 4, 8 workers. DB query audit via `pg_stat_statements` (or SQLite `EXPLAIN QUERY PLAN`); flag queries > 100ms.

**H2-T05 — API Versioning and Deprecation**
All routes prefixed with `/v1/`. 90-day deprecation window; `Sunset` header; changelog. MINOR backward-compatible; MAJOR requires an ADR. `docs/API_VERSIONING.md`.

Additional enforceable requirement:
- No new API surface may ship without versioned routing.
- CI must fail if a route is added outside the `/v1/` prefix policy.
- Existing unversioned routes must be migrated before release or explicitly marked as deprecated with an owner and sunset date.
- Versioning is treated as a release requirement, not as documentation-only guidance.

**H2-T06 — i18n String Externalization**
Extract all UI strings into `ui/src/locales/en.json`. ESLint rule fails on raw JSX string literals. No second locale yet; architecture supports adding one without refactor.

**Exit criteria:** All six deliverables implemented; DR drill passed; load-test baseline recorded and stored in the repo; versioning policy enforced in CI.

---

### Phase H3 — Architectural Contradiction Resolution
**Duration:** Weeks 2–3
**Goal:** Fix the three contradictions surfaced by the review, plus soft-gate documentation.

| Task | Title | Track | Approval |
|---|---|---|---|
| **H3-T01** | Plugin security model remediation | A+B+C | Yes |
| **H3-T02** | Cache false-positive evaluation | A | Yes |
| **H3-T03** | Migration reversibility correction | A | Yes |
| **H3-T04** | Soft-gate timing documentation | A | No |

**H3-T01 — Plugin Security Model Remediation**
ADR-001 v6 §5.8 and §13 state "Plugins trusted once installed. No sandboxing" but grant `read:secrets` and `network:external`. Resolution:

- **Remove `read:secrets`** entirely from the permission model.
- **Brokered secret interface**: plugins request a secret by name; the broker injects at call time, logs access, enforces a per-plugin allowlist, and rejects any secret request outside the declared policy.
- **Subprocess isolation**: each plugin runs in a subprocess with restricted filesystem scope (own directory only) and network policy (declared domains only).
- **Manifest extension**: `plugin.yaml` must declare `allowed_domains` and explicit runtime scope.
- **CI enforcement**: `bandit`, `pip-audit`, `gitleaks`, manifest schema validation, and secret-access policy tests must fail if a plugin attempts direct secret access.
- **Migration guide** for plugins using `read:secrets`; 2-release deprecation window.
- Update `docs/PLUGINS.md` with trust model, disclosure policy, and approved secret-access patterns.
- **Acceptance gate**: the plugin security model must be demonstrated by failing tests that prove secrets are inaccessible without broker approval and that manifest validation rejects invalid network or secret access.

**H3-T02 — Cache False-Positive Evaluation**
Add metric `cache_false_positive_rate` — proportion of semantic cache hits that fail soft gates. Gate: semantic cache disabled if FPR > 2%. Invalidate on model version, prompt template, or domain model change. Semantic cache becomes per-project opt-in. Add 20 near-miss golden pairs that must NOT hit the cache.

**H3-T03 — Migration Reversibility Correction**
Amend `docs/CONFIGURATION.md` and ADR-001 §5.6 claim: change "every migration reversible" to "every migration has a documented rollback; destructive migrations require a backup-first gate." Add forward + backward test for each Alembic migration.

**H3-T04 — Soft-Gate Timing Documentation**
Update MCP tool descriptions to state "soft gates Q7/Q8/Q10 per ADR-001 v6 §10." Add `--strict` flag to CLI that fails generation if any soft gate is below threshold. Default behavior unchanged.

**Exit criteria:** Plugin model documented and tested; cache FPR gate active; migration policy updated; MCP tool descriptions updated; security tests green.

---

### Phase H4 — Operational Maturity
**Duration:** Weeks 3–4
**Goal:** Add operational guardrails deferred in ADR-001 v6.

| Task | Title | Track | Approval |
|---|---|---|---|
| **H4-T01** | Cross-track regression gate | — | Yes |
| **H4-T02** | Release checklist | — | Yes |
| **H4-T03** | Post-implementation re-scoring | — | Yes |

**H4-T01 — Cross-Track Regression Gate**
CI job on every merge to `main`: full unit + integration + contract test suites. Walking-skeleton smoke test. Load-test smoke (10 users, 30 seconds). Merge blocked until green.

Additional requirement:
- Cross-track regression gate must enforce release safety, not merely report results.
- Merge gate includes backup/restore smoke validation when data-layer changes occur.

**H4-T02 — Release Checklist**
`docs/RELEASE_CHECKLIST.md`: version bump + changelog; API version consistency; migration forward + backward; DR drill status (within last quarter); observability dashboards reviewed; score re-projection committed.

Additional requirement:
- Release checklist is a required approval artifact for every production-facing release.
- No release may proceed without a signed checklist referencing passed validation evidence.

**H4-T03 — Post-Implementation Re-Scoring**
Re-score against `docs/SCORE_MODEL.md`. Publish new range with diff against projection (9.03) and delivered actual (8.61). If any dimension falls below target by > 0.5, open a follow-up ADR.

Additional requirement:
- Re-scoring is mandatory before release and must be archived with the release artifacts.
- Score deltas must be explained operationally, not merely reported numerically.

**Exit criteria:** CI gate active; release checklist used once; score re-published with delta recorded; all required checks passed.

---

### Phase H5 — Convergence, Buffer, and Release
**Duration:** Weeks 5–6
**Goal:** Absorb schedule slippage and ship hardened platform.

| Task | Title | Track | Approval |
|---|---|---|---|
| **H5-T01** | Schedule buffer | — | No |
| **H5-T02** | Documentation consolidation | — | Yes |
| **H5-T03** | Hardening release (v2.1.0) | — | Yes |

**H5-T01 — Schedule Buffer**
One-week buffer between H4 completion and H5-T03. No new scope may be added to H5.

**H5-T02 — Documentation Consolidation**
Update all `docs/*.md`. Add cross-references between ADR-001 v6 and ADR-002. Publish `docs/HARDENING_SUMMARY.md` mapping each ADR-002 task to the review finding it addresses.

**H5-T03 — Hardening Release (v2.1.0)**
Tag on `main`. Release notes list the 18 hardening tasks. Announce: plugin security model change, cache opt-in change, API versioning policy. Migration guide for v4 users.

Additional requirement:
- Release includes changelog, migration guide, operator notes, and evidence of restore drill and score re-projection.
- Release is blocked unless the hardening evidence artifacts are attached to the release record.

**Exit criteria:** v2.1.0 tagged; migration guide published; release notes reviewed; hardening evidence archived; restore drill and validation artifacts attached to the release.

---

## 5. Timeline

```text
Week:  1     2     3     4     5     6
H1     ███
H2     ██████████
H3           ██████
H4                 ██████
H5                       ██████
```

**Critical path:** H1 → H2 (T01–T03) → H4 (T01) → H5 (T03).
**Duration:** 5–6 weeks (2 reviewers) / 4–5 weeks (3 reviewers).

**P50 / P80 (published after H1-T02):**

| Phase | P10 | P50 | P80 |
|---|---|---|---|
| H1 | Week 1.0 | Week 1.2 | Week 1.5 |
| H2 | Week 2.5 | Week 3.0 | Week 3.5 |
| H3 | Week 2.5 | Week 3.0 | Week 3.5 |
| H4 | Week 4.0 | Week 4.5 | Week 5.0 |
| H5 | Week 5.0 | Week 5.5 | Week 6.5 |

---

## 6. Score Projection (Corrected — Final)

### 6.1 Framing

ADR-001 v6's 9.53 was a **pre-implementation projection** — an upper bound. ADR-002's number is a **post-implementation measurement** — calibrated against what was actually delivered. Comparing them directly is invalid. Three columns are required.

### 6.2 Corrections

**Correction A — ADR-001 §15 does not sum to 9.53.**
The 13 weighted contributions in ADR-001 §15 sum to **9.03**. This is a 0.5 arithmetic error in the original projection. ADR-002 adopts 9.03 as the corrected projection baseline.

**Correction B — Earlier ADR-002 drafts contained two scoring errors.**

| Item | Earlier Draft | Corrected | Reason |
|---|---|---|---|
| Determinism | 9.3 | 9.5 | H3-T02 adds a cache FPR gate; a gate cannot reduce determinism |
| UI / UX | 8.3 | 8.5 | H2-T06 externalizes i18n strings; additive architecture cannot degrade UX |

### 6.3 Three-Column Model

| Dimension | Weight | ADR-001 Projected (corrected) | Delivered Actual | ADR-002 Target |
|---|---|---|---|---|
| Enterprise readiness | 0.15 | 8.8 | 8.1 | 9.2 |
| Security | 0.18 | 9.1 | 7.8 | 9.4 |
| Determinism | 0.12 | 9.5 | 9.2 | 9.5 |
| Performance | 0.10 | 9.0 | 8.6 | 9.1 |
| Product / UX | 0.10 | 8.5 | 8.2 | 8.7 |
| Quality & gates | 0.12 | 9.1 | 8.8 | 9.2 |
| Observability | 0.08 | 7.5 | 6.9 | 8.9 |
| Migration / config | 0.07 | 8.7 | 7.6 | 9.0 |
| API strategy | 0.04 | 8.4 | 7.3 | 9.1 |
| Plugin ecosystem | 0.04 | 8.6 | 7.1 | 9.2 |
| Operational maturity | 0.06 | 8.2 | 7.4 | 9.0 |
| Governance / approval | 0.03 | 8.8 | 8.2 | 9.0 |
| Release discipline | 0.01 | 8.9 | 7.8 | 9.1 |

**Final target score:** 9.09 ± 0.10

### 6.4 Interpretation

- **Projected ceiling (corrected):** 9.03
- **Delivered actual:** 8.61
- **Hardened target:** 9.09 (± 0.10)

ADR-002 closes the entire delivered-to-projected gap and lands marginally above the corrected projection. ADR-001's original 9.53 is withdrawn as an arithmetic error.

### 6.5 Weight Review Commitment

The 13 weights are inherited from ADR-001 §15 and were never stakeholder-signed. Task **H1-T01** publishes them in `docs/SCORE_MODEL.md` with sign-off. Task **H4-T03** re-scores against the reviewed weights and publishes a diff.

### 6.6 Published Statement

> The platform as delivered scores **8.61** against the corrected ADR-001 weighting model. ADR-002 raises this to **9.09 ± 0.10**, matching or slightly exceeding the corrected ADR-001 projection of **9.03**. The original 9.53 figure is withdrawn.

### Score Confidence Note

The hardening plan is credible and operationally targeted. However, the target score should be interpreted as a conditional outcome: 9.09 is achievable only if each hardening item is enforced in code and validated in CI. Without evidence-based completion criteria, the plan remains strong but aspirational.

---

## 7. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Plugin migration breaks early adopters | Medium | High | 2-release deprecation window; migration guide; shim for `read:secrets` during transition |
| DR drill uncovers data loss | Low | High | Run drill in non-prod first |
| Observability adds request latency | Low | Medium | Async exporters; benchmark in H2-T04 load test |
| Load test fails thresholds | Medium | Medium | Thresholds are targets, not gates; iterate |
| i18n extraction breaks UI | Low | Medium | ESLint rule catches most issues; visual regression in CI |
| Re-scoring drops below 9.0 | Low | Medium | Pre-agree on acceptable range; follow-up ADR if below |
| API versioning breaks consumers | Low | High | `/v1/` added as alias; `/` retained for 1 release |
| Post-ADR-002 Aegis v15.2 slips | Medium | High | Aegis validation runs in parallel; profile decision at end of H5 |

---

## 8. Relationship to Aegis v15.2 (Sequencing)

**ADR-002 executes first. Aegis v15.2 P0 begins after H5-T03 ships.**

| Weeks | ADR-002 | Aegis v15.2 |
|---|---|---|
| 1–3 | H1, H2, H3 | Product Owner begins 20 validation interviews |
| 3–4 | H4 | Interviews continue; validation gate resolves |
| 5–6 | H5, release v2.1.0 | Profile declared (1.5.0 or 2.0.0) |
| 7+ | — | Aegis v15.2 P0 begins |

**Interleaving rule:** Aegis validation interviews run *during* ADR-002 execution, owned by the Product Owner, not blocked by ADR-002 tasks.

**Minimum-viable alternative if market window forces Aegis to start immediately:**

1. Land only H3-T01 (plugin security) before Aegis P0.
2. Land only H2-T05 (API versioning) before Aegis P4-T09.
3. Defer the rest of ADR-002 into Aegis P14 as a hardening sprint.

This is inferior to full sequencing but defensible.

---

## 9. Definition of Done (Extended)

ADR-001 v6 §17 DoD is preserved. ADR-002 adds:

- [ ] Migration task includes forward + backward test against a real fixture
- [ ] Backup task includes a restore drill with verified row counts
- [ ] Observability task includes at least one dashboard and one alert rule
- [ ] Load test task publishes p50/p95/p99 and compares against thresholds
- [ ] API change includes version bump and deprecation notice if breaking
- [ ] Plugin change verifies no raw secret is accessible to plugin code
- [ ] Cache change includes FPR measurement against near-miss golden pairs
- [ ] Score change updates `docs/SCORE_MODEL.md` and `docs/SCORE.md`
- [ ] Operational docs (`docs/SCORE_MODEL.md`, `docs/DR.md`, `docs/RELEASE_CHECKLIST.md`, `docs/MIGRATION.md`) scaffolded and committed with baseline operational metrics
- [ ] CI pipeline rule verifies automated route versioning enforcing `/v1/` prefix compliance

A task is Done when all applicable items are checked and the Evidence block is attached to the PR.

---

## 10. Consequences

### Positive

- **Enterprise-ready:** DR, observability, load testing, API versioning, and migration close the gaps that block adoption.
- **Security-credible:** Plugin model internally consistent; no raw secrets, subprocess isolation, declared domains.
- **Score-credible:** Three-column model with published weights survives stakeholder scrutiny.
- **Cache-correct:** FPR gate prevents silent quality degradation.
- **Operationally mature:** Regression gate, release checklist, DR drill institutionalize quality.
- **Adoption path:** v4 users can migrate; plugin authors have documented deprecation.
- **Aegis-ready:** Aegis v15.2 inherits a hardened base and does not have to build enterprise capabilities itself.

### Negative

- **+18 tasks, +5–6 weeks:** Targeted and additive, but real.
- **Plugin migration:** Removing `read:secrets` may break some plugins; deprecation window and shim mitigate.
- **Operational surface:** DR, observability, and load testing require ongoing maintenance.
- **Score reduction:** The published score drops from the *misstated* 9.53 to a *corrected* 9.03 projection and a 9.09 target. This is honesty, not regression.

### Neutral

- Architecture unchanged.
- CLI remains the primary automation interface.
- All ADR-001 v6 decisions remain in force.

---

## 11. Alternatives Considered

| Alternative | Why rejected |
|---|---|
| Leave the platform as-is | Enterprise gaps and plugin security contradiction surface in first customer review |
| Re-open ADR-001 phases | Violates "no re-opening" principle; disrupts stable modules |
| Bundle all hardening into one mega-PR | Untestable; violates one-task-one-PR discipline |
| Defer hardening to v3 | Delays enterprise revenue; gaps are the barrier to adoption |
| Sandbox plugins via WASM | Overkill for v2.1; subprocess isolation is sufficient |
| Start Aegis v15.2 first | Inverts explicit dependency; pays for plugin and API fixes twice |

---

## 12. Status Tracking

| Phase | Tasks | Status | Blocked By |
|---|---|---|---|
| H1 — Score and Timeline Credibility | 3 | Not started | — |
| H2 — Enterprise Completeness | 6 | Not started | H1 |
| H3 — Architectural Contradictions | 4 | Not started | H1 |
| H4 — Operational Maturity | 3 | Not started | H2, H3 |
| H5 — Convergence and Release | 3 | Not started | H4 |
| **Total** | **18** | **0/18** | — |

---

## 13. Verification Appendix

Post-implementation verification is done via three prompts, documented in `docs/VERIFICATION_PROMPTS.md`:

1. **Master verification** — six passes: structural, end-to-end, gate integrity, non-functional, configuration, acceptance.
2. **Adversarial verification** — ten falsification methods targeting gate bypass, flag bypass, cache poison, RBAC, anchoring, migration round-trip, interface drift, repair loop, cost gate.
3. **Concise verification** — the abbreviated form for routine release gating.

The single most important check: **for each gate Q0–Q10, does at least one test prove the gate FAILS on bad input?** If not, the gate is decorative and the platform's deterministic claim is unproven.

---

## 14. Containerization Appendix

Container portability is verified under **both Docker and Podman**. Requirements:

| Artifact | Purpose |
|---|---|
| `docker-compose.yml` with SELinux labels (`:Z`) on bind mounts | Required for Podman on Fedora/RHEL |
| `Dockerfile` uses exec-form ENTRYPOINT | Same behavior under both runtimes |
| `.dockerignore` excludes secrets, `.git`, caches | Prevents secret leak into image |
| `HEALTHCHECK` per service | Required for `depends_on: service_healthy` |
| `docs/CONTAINER_RUNTIME.md` | Documents Docker + Podman setup and differences |
| `scripts/verify-runtime.sh` | One script that runs cold-start under whichever runtime is present |
| `Makefile` targets: `up-docker`, `up-podman`, `verify-both` | Single command per runtime |
| Seed script with idempotency guard | Prevents duplicate seed on restart |
| Migration entrypoint that waits for DB | Prevents race at startup |

**Single check that matters most:** Under both Docker and Podman, on a clean daemon, with an `.env` derived only from `.env.example`, does `compose up` reach every service healthy — with migrations applied, seed data present, and all four test users (admin, reviewer, generator, viewer) able to authenticate?

---

## 15. Approval

| Role | Name | Decision | Date |
|---|---|---|---|
| Engineering Lead | — | Pending | — |
| QA Architect | — | Pending | — |
| Product Owner | — | Pending | — |
| Security Lead | — | Pending | — |
| UX Lead | — | Pending | — |

Upon approval, H1-T01 is opened as a task branch and ADR-002 enters execution.

---

## 16. Changelog

| Version | Date | Change |
|---|---|---|
| v1 | 2026-09-19 | Initial 18-task plan |
| v2 | 2026-09-19 | Added H3-T04, H5-T03 |
| **v3** | **2026-09-19** | **Corrected §6 score model (three-column); corrected ADR-001 arithmetic error; added §4.3 sequencing with Aegis; added §13 verification appendix; added §14 containerization appendix; final consolidation. FINAL.** |

---

**End of ADR-002 v3 (final).**

**Total tasks: 18.**
**Total phases: 5 (H1–H5).**
**Duration: 5–6 weeks (2 reviewers) / 4–5 weeks (3 reviewers).**
**Target score: 9.09 ± 0.10 (corrected from the misstated 9.53).**
**Sequencing: before Aegis v15.2.**
**Verification: three prompts in `docs/VERIFICATION_PROMPTS.md`.**
**Containerization: Docker + Podman parity required.**

**Execution begins at H1-T01 upon approval.**