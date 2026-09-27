# ADR-005: Context Contract and Context Linter as Norma's Input Harness

**Status:** FROZEN
**Date:** 2026-09-27
**Deciders:** Owner (bmrtech), Engineering Lead, QA Architect
**Version:** 1.0
**Extends:** ADR-001 (Norma BDD Platform), ADR-002 (Platform Hardening), ADR-004 (Closed-Loop Verification)
**Supersedes:** None

---

## Metadata

| Field | Value |
|---|---|
| **ADR ID** | ADR-005 |
| **Version** | v1.0 |
| **Title** | Context Contract and Context Linter as Norma's Input Harness |
| **Status** | **FROZEN** |
| **Date** | 2026-09-27 |
| **Deciders** | Owner, Engineering Lead, QA Architect |
| **Extends** | ADR-001, ADR-002, ADR-004 |
| **Target Duration** | 1.5 weeks (v1.0), 3 days (v1.1) |
| **Total new tasks** | **10** (v1.0: 7, v1.1: 3) |
| **Total new phases** | **2** (v1.0, v1.1) |
| **Deferred items** | 6 (documented in §12 with revisit triggers) |

---

## 1. Context

Norma has three ingestion adapters (CSV, XLSX, Jira) and a generation pipeline (`NormaAgent`) followed by quality gates Q0–Q10. The gates check the **output** of generation. They do not check the **input**.

Consequences of having only output gates:

1. **Late failure.** A story with no acceptance criteria reaches `NormaAgent`, which burns tokens to generate Gherkin, then Q-gates fail on the output. The real problem was the input.
2. **Inconsistent inputs.** CSV, XLSX, and Jira adapters produce slightly different shapes. Downstream code compensates in ways that are invisible.
3. **No traceability anchor.** Q0–Q10 check that scenarios "map to an AC," but the AC list is implicit and unversioned. Traceability is aspirational, not enforceable.
4. **No trust model.** A story from Jira, a design doc from Confluence, and a snippet from a public blog all reach the LLM identically. Prompt injection is unguarded.
5. **No cost pre-flight.** Token budget is discovered after the LLM call, not before.
6. **Review is late.** Humans review generated output rather than the input they care about.

In short: **Norma has sensors, but no guides.** This ADR adds the guide.

The design is deliberately minimal: one file format and one function. No orchestrator, no agent framework, no queue, no state machine. The smallest useful component is not an agent. It is a contract.

---

## 2. Four-Lens Review Summary

This ADR was shaped by four lenses: Hickey (shape), Fowler (evolution), the Enumerator (completeness), and Antinode Labs (signal over noise). The review is documented because it explains why the scope is what it is.

### 2.1 The Core User Problem

**A QA engineer cannot tell whether a story has enough context to generate trustworthy tests, until after generation has already run.**

The Context Contract makes this verifiable before the LLM is invoked.

### 2.2 Where All Four Lenses Agree

- **The contract is data, not code.** Hickey: a versioned value you can hash, diff, and reason about. Fowler: the ubiquitous-language artifact.
- **The linter is a pure function.** Hickey: reads a file, writes a sidecar, no side effects. Fowler: it's a guide (feedforward), complementing the sensors (Q0–Q10).
- **The contract is not owned by Norma.** Antinode: Norma reads it; the team owns it. This keeps Norma narrow.
- **The schema is 20 fields, not 40.** Enumerator wanted more; Hickey and Fowler cut it. Add fields when a real user is blocked.

### 2.3 Scope Cut Rationale

| Cut | Reason |
|---|---|
| `readiness` in contract → sidecar file | Linter must not mutate the contract (§6.3) |
| 40 fields → 20 fields | Bet on 20 real needs, not 40 imagined ones |
| `constraints` field | Overlaps with `definition_of_done` |
| `budget.relevant_files` | No cost pain yet |
| `readiness.expiry` | No stale-contract case yet |
| `domain_terms` uniqueness rule | Downgraded to soft warning |
| LLM-based linter checks | Opt-in only; deterministic first |
| Plugin registry / marketplace | Audience of one |

---

## 3. Decision

Introduce two artifacts into Norma:

1. **Context Contract** — a frozen YAML file (v1.0, 20 fields) that carries intent, scope, acceptance criteria, sources, trust, and budget for one user story. The canonical input to any Norma generation stage.
2. **Context Linter** — a pure function, shipped as a Norma plugin, that validates a Context Contract against CAFE(S) and returns a readiness decision with evidence. Writes its findings to a sidecar file. Never mutates the contract.

The Context Contract sits **in front of** Norma. The linter runs **before** `NormaAgent`. The existing pipeline — `Adapter → NormaAgent → Q0–Q10 → Output` — remains unchanged except that the adapter's output type becomes `Contract`, and the linter is inserted between adapter and agent.

The contract is a **file**. Norma reads it. Norma does not own it, store it, version it, or enforce its schema at runtime. If the contract cannot be created, edited, and version-controlled in the repository (or attached to the work item), it does not belong in Norma.

---

## 4. Design Principles

These principles are binding. Any future extension must honor them.

1. **Data over code.** The contract is data. The linter is a pure function over data. Rules are a data catalog (YAML list of checks).
2. **Guides before sensors.** The linter (guide) prevents bad input from reaching the LLM. Q0–Q10 (sensors) catch bad output.
3. **Contract is not owned by Norma.** Ownership stays with the team that writes the story.
4. **Contract is immutable during lint.** The linter writes to a sidecar. The contract file is never modified.
5. **Trust is enforced, not labeled.** `trust.level` has consequences.
6. **Evidence for every finding.** Findings without evidence cause the entire run to return `blocked`.
7. **Readiness, not scores.** `ready`, `conditional`, or `blocked`. No numeric scores.
8. **Transformers are narrow.** One input, one output, no knowledge of siblings.
9. **Contract content is data, not instructions.** Never executed, never `eval`'d, never obeyed.
10. **Smallest useful thing.** 20 fields, not 40.

---

## 5. The Context Contract (v1.0, Frozen)

Schema frozen at v1.0 with 20 fields.

### 5.1 Schema

```yaml
version: "1.0"                        # required, frozen

id: <string>                          # required, e.g. QA-1234
title: <string>                       # required
stage: <enum>                         # required: story-to-feature | feature-to-code | code-to-review

intent:                               # required
  goal: <string>                      # required
  actor: <string>                     # required
  outcome: <string>                   # required

scope:                                # required
  in: [<string>, ...]                 # required, min 1
  out: [<string>, ...]                # required, min 1 (non-empty)

acceptance_criteria:                  # required, min 1
  - id: <string>                      # required, e.g. AC-1
    given: <string>                   # required
    when: <string>                    # required
    then: <string>                    # required

domain_terms:                         # required, min 1
  - term: <string>
    meaning: <string>

definition_of_done: [<string>, ...]   # required, min 1

sources:                              # required, min 1
  - type: <enum>                      # required: story | design | code | external
    ref: <string>                     # required
    version: <string>                 # required
    freshness: <date|null>            # required for type=design only
    owner: <string>                   # required for type in [story, design]

trust:                                # required
  level: <enum>                       # required: untrusted | low | trusted
  pii: <bool>                         # required
  secrets: <bool>                     # required
  allowed_sources: [<string>, ...]    # required, min 1

budget:
  max_tokens: <int>                   # required
```

**20 fields total.** Additions require a version bump and a real user case.

### 5.2 CAFE(S) Mapping

| CAFE(S) | Contract field |
|---|---|
| Clarity | `domain_terms`, unambiguous actor/system names |
| Actionability | `acceptance_criteria`, `definition_of_done`, `scope` |
| Fidelity | `sources`, `version`, `freshness`, `owner` |
| Efficiency | `budget.max_tokens`, `scope.out` |
| Security | `trust`, `pii`, `secrets`, `allowed_sources` |

### 5.3 Complete Example

```yaml
version: "1.0"
id: QA-1234
title: Password reset via email
stage: story-to-feature

intent:
  goal: Allow a registered user to reset a forgotten password.
  actor: Registered user
  outcome: User can set a new password and log in.

scope:
  in:
    - Request reset link
    - Email delivery
    - Token expiry
    - Password rules
  out:
    - Admin-initiated reset
    - SSO users

acceptance_criteria:
  - id: AC-1
    given: a registered user with a verified email
    when: they request a password reset
    then: they receive a reset link valid for 30 minutes
  - id: AC-2
    given: an expired reset token
    when: the user opens the link
    then: they see the error "Link expired. Request a new one." and a request link

domain_terms:
  - term: reset token
    meaning: single-use URL parameter, expires after 30 minutes
  - term: verified email
    meaning: email address confirmed by the user

definition_of_done:
  - Feature file has one scenario per acceptance criterion.
  - Each scenario maps to an AC id.
  - Test code covers happy path and expired-token path.
  - No hardcoded secrets or environment URLs.

sources:
  - type: story
    ref: JIRA-QA-1234
    version: "3"
    freshness: null
    owner: product-team
  - type: design
    ref: docs/auth/password-reset.md
    version: commit-abc123
    freshness: 2026-09-20
    owner: design-team
  - type: code
    ref: src/auth/reset-service.ts
    version: commit-abc123
    freshness: null

trust:
  level: trusted
  pii: true
  secrets: false
  allowed_sources:
    - internal-repo
    - jira

budget:
  max_tokens: 4000
```

### 5.4 Sidecar File (`<id>.lint.yaml`)

Written by the linter. Read by downstream transformers. Never edited by humans.

```yaml
contract_id: QA-1234
contract_hash: sha256:4a3f8e2b...
linted_at: 2026-09-27T10:00:00Z
linted_by: linter@1.0.0
stage: story-to-feature

readiness:
  status: conditional
  reason: "One soft finding remains."

findings:
  - id: C-07
    check: freshness_missing
    severity: soft
    field: sources[2].freshness
    issue: "Code source has no freshness date."
    evidence:
      - ref: contract.sources[2]
        quote: "type: code, ref: src/auth/reset-service.ts"
    fix: "Add freshness: <date>."
    blocked: false

summary:
  hard_findings: 0
  soft_findings: 1
  blocked: false
```

### 5.5 Contract Identity

The linter computes `contract_hash` as SHA-256 of the canonical contract file and writes it to the sidecar. Every downstream artifact records `(contract_hash, artifact_hash)` in the audit trail.

If a sidecar's `contract_hash` doesn't match the current contract, the sidecar is **stale**. Downstream transformers treat a stale sidecar as `blocked` until the contract is re-linted.

---

## 6. The Context Linter

A pure function. Input: a contract file. Output: a sidecar file. The contract file is never mutated.

### 6.1 Interface

```python
def lint(contract_path: Path, *, cfg: LinterConfig) -> LintReport:
    ...
```

- Pure function. No network calls except when `--llm` is passed.
- Deterministic checks run first. LLM checks run only when the deterministic pass has no hard findings.
- Every finding carries `evidence`. Empty evidence → run returns `blocked`.

### 6.2 Deterministic Checks (v1.0)

| ID | Check | Severity |
|---|---|---|
| C-01 | Required fields present | hard |
| C-02 | Every AC has an id | hard |
| C-03 | Every AC has given/when/then | hard |
| C-04 | `scope.out` non-empty | soft |
| C-05 | Domain terms unique | soft |
| C-06 | Sources have version | hard |
| C-07 | Design sources have freshness | soft |
| C-08 | Every source is in `allowed_sources` | hard |
| C-09 | Token count ≤ `budget.max_tokens` | hard |
| C-10 | No secret patterns (API keys, tokens, passwords) | hard |
| C-11 | No PII patterns when `trust.pii=false` | hard |
| C-12 | `definition_of_done` non-empty | soft |
| C-13 | Constraints do not contradict `scope.out` | soft |
| C-14 | `version` field is exactly `"1.0"` | hard |
| C-15 | Referenced files in `sources[].ref` exist | soft |
| C-16 | `trust.pii=true` implies owner on every story/design source | hard |

### 6.3 LLM Checks (Opt-In, v1.0)

| ID | Check | Severity |
|---|---|---|
| L-01 | Ambiguous terms not in `domain_terms` | soft |
| L-02 | Contradictions between story and design sources | hard |
| L-03 | Instructions embedded in untrusted sources | hard |
| L-04 | Missing recovery path for error states | soft |
| L-05 | `definition_of_done` unmeasurable | soft |

**LLM check contract:**
- Model: configurable, default `claude-sonnet-4`
- Temperature: 0
- Timeout: 30 seconds per check
- Fallback: on failure or timeout → `unknown`, not `pass`
- Prompt: versioned at `prompts/linter/v1.md`
- Output: structured YAML with `evidence` per finding

### 6.4 Evidence Schema

Every finding must include at least one evidence entry:

```yaml
evidence:
  - ref: <file:line | field.path | source.ref>
    quote: <string, ≤200 chars>
```

Empty evidence → the entire linter run returns `blocked` with finding `E-04`.

### 6.5 Readiness States

| Status | Meaning | Downstream Action |
|---|---|---|
| `ready` | No hard findings, no soft findings | Proceed |
| `conditional` | No hard findings, ≥1 soft finding | Proceed with human acknowledgement |
| `blocked` | ≥1 hard finding, or any error finding | Stop. Fix and re-lint. |

No numeric scores. No grades.

### 6.6 Output Formats

Two formats from one run:

- `<id>.lint.yaml` — structured, machine-readable
- `<id>.lint.md` — human-readable prose

Both written to the sidecar path. Neither modifies the contract.

### 6.7 Plugin SDK Alignment

`ContextLinter` ships as a Norma plugin. Two paths considered:

**Path A — As-is.** If `QualityGatePlugin` operates on arbitrary inputs (not just generated Gherkin), `ContextLinter` implements it directly. No SDK changes.

**Path B — Additive Extension.** If `QualityGatePlugin` is limited to generated output, extend it with an additive `input_schema` field in the plugin manifest. Existing plugins are unaffected.

**Decision:** Determined by a 30-minute spike in step 3 of the build sequence (§10). Whichever applies, the ADR commits to one of the two paths. The plugin SDK alignment is verified before implementation, not assumed.

---

## 7. Trust Enforcement

`trust.level` is not a label. It has consequences enforced by the linter and by every transformer.

| Level | Enforcement |
|---|---|
| `untrusted` | Strip all free-text fields before any LLM call. Only structured fields (ids, given/when/then) may pass downstream. Require human approval at every handoff. |
| `low` | Require human approval before the next transformer runs. Redact free text through the secret scanner. Cap LLM token budget to 50% of declared. |
| `trusted` | Proceed with audit trail. Full budget applies. |

**Downgrade rules:**

1. If any source's `ref` is not in `allowed_sources`, `trust.level` becomes `low`.
2. If `allowed_sources` is empty, the contract is `blocked`.
3. Trust is set by the author. The linter cannot elevate it; only downgrade.
4. Contracts with `trust.pii=true` require an `owner` on every `story` and `design` source. Missing owner is a hard finding (C-16).

---

## 8. Failure Modes

Every failure has a name and a defined behavior. No silent failures. No `pass` by default.

| Failure mode | Behavior | Recovery |
|---|---|---|
| Contract file missing | `blocked` with finding `E-01` | Team writes the contract |
| Contract invalid YAML | `blocked` with finding `E-02` | Team fixes syntax |
| Sidecar hash mismatch | Downstream transformers treat as `blocked` | Re-run linter |
| Deterministic check crashes | `blocked` with finding `E-03`; run halts | Fix linter; re-run |
| LLM check times out | Returns `unknown`, not `pass`; overall `conditional` | Retry with `--llm` or accept conditional |
| LLM check returns no evidence | Rejects LLM output; `E-04`; run returns `blocked` | Investigate prompt; re-run |
| Two contracts share the same `id` | Both flagged `E-05`; newer `linted_at` wins | Team resolves |
| Referenced file does not exist | Soft finding `C-15` | Add file or remove reference |
| Plugin SDK path fails | `E-06`; ADR falls back to Path B | Document in changelog |

Error findings (`E-*`) are always hard and always produce `blocked`.

---

## 9. How It Fits Norma

### 9.1 Pipeline Position

```
CSV / XLSX / Jira / Markdown / Slack
        │
        ▼
 [ Contract Builder ]           ← adapter output (thin)
        │
        ▼
   Context Contract             ← canonical, frozen input (immutable)
        │
        ▼
 [ Context Linter ]             ← plugin, guide
        │
        ├── blocked ──► stop
        │
        ▼
   [ NormaAgent ]               ← unchanged
        │
        ▼
   [ Gates Q0–Q10 ]             ← unchanged, sensors
        │
        ▼
    Feature file
```

### 9.2 What Changes in Norma

| Component | Change |
|---|---|
| `NormaAgent` | None at v1.0. Input type becomes `Contract` at v1.1. |
| Gates Q0–Q10 | None. Still run on generated Gherkin. |
| Adapters (CSV, XLSX, Jira) | Produce a `Contract` instead of a `Story`. |
| Plugin SDK | None (Path A) or additive extension (Path B). |
| MCP tools | One new tool: `norma.lint_contract(contract)`. |
| UI | New tab: **Contract Review**. Added at v1.1. |
| Audit trail | Records `(contract_hash, artifact_hash)` pairs. |

### 9.3 Where the Linter Lives

Shipped as a **Norma plugin**, not a core module.

```
src/norma/plugins/context_linter/
├── manifest.yaml
├── linter.py
├── checks/
│   ├── deterministic.py
│   └── llm_checks.py
└── tests/
```

### 9.4 Where the Contract Lives

The contract is a file. It lives where the story lives:

- **In the repo** for Git-based teams: `.context/<id>.yaml`
- **In Jira** as an attachment for Jira-based teams
- **Wherever the team already works**

Norma does not own, host, version, or edit the contract.

### 9.5 Three-Layer Verification Stack

ADR-005 is the input gate of a three-layer stack:

| Layer | ADR | Artifact | Purpose |
|---|---|---|---|
| **Input gate** | ADR-005 | Context Contract | Validates input before generation |
| **Application-knowledge gate** | ADR-004 | Application Fingerprint | Validates that the application interface is known |
| **Output gate** | ADR-004 | Closed-loop verification + SD gates | Validates that step definitions execute intent |

**Dependency direction:** ADR-005 → ADR-003 → ADR-004. No circular dependencies.

---

## 10. Build Sequence

### v1.0 — ~1.5 weeks

| # | Step | Output | Time |
|---|---|---|---|
| 1 | Write contract schema v1.0 | `docs/context-contract.md` | 1 hour |
| 2 | Write one real contract | `.context/QA-1234.yaml` | 1 hour |
| 3 | Verify plugin SDK path (A or B) | Spike result documented | 30 min |
| 4 | Write deterministic linter (C-01 to C-16) | `src/norma/plugins/context_linter/` | 1.5 days |
| 5 | Add MCP tool `norma.lint_contract` | `src/norma/mcp/tools.py` | 2 hours |
| 6 | Change one adapter (Jira) to emit contracts | `src/norma/adapters/jira.py` | 4 hours |
| 7 | Run end-to-end on one story | — | 1 day |

**Task count:** 7. **Deliverable:** `docs/release-gates/v1.0.0.md`.

### v1.1 — ~3 days

| # | Step | Output | Time |
|---|---|---|---|
| 8 | Change `NormaAgent` input type to `Contract` | `src/norma/agent/` | 3 hours |
| 9 | Add "Contract Review" tab to UI | `web/src/routes/` | 1 day |
| 10 | Write two more adapter changes (CSV, XLSX) | `src/norma/adapters/` | 1 day |

**Task count:** 3. **Deliverable:** `docs/release-gates/v1.1.0.md`.

### Sequencing with ADR-004

```
Week 0     │ Decide
Week 1–2   │ ADR-005 v1.0
Week 3–4   │ Use it. Measure. Decide.
Week 5–9   │ ADR-004 P15–P20
Week 10    │ Use it. Measure. Decide.
Week 11+   │ ADR-006 (if written)
```

ADR-005 ships before ADR-004. The two are not parallel.

### Decision Test at End of Week 2

1. Did the linter catch a real problem in your own stories? If yes → continue.
2. Did you write contracts for two weeks without giving up? If yes → continue.
3. Did the plugin SDK work as expected? If yes → ADR-004's path is de-risked.

If any answer is no, spend two more weeks on ADR-005 before starting ADR-004.

---

## 11. Consequences

### Positive

- **Guides added.** Norma now has pre-flight checks, not just post-flight gates.
- **Traceability becomes enforceable.** Scenarios must reference AC ids that exist in the contract.
- **Trust becomes a first-class input.** Prompt injection has a defensive surface.
- **Cost becomes predictable.** Budget checked before tokens are spent.
- **Human review moves earlier.** Contract review is cheaper than output review.
- **Norma stays narrow.** Contract sits in front, not inside.
- **Contract is immutable.** No concurrent-write races, no git diff noise.
- **Content hash enables exact traceability.** Every artifact resolves to a contract version.
- **Plugin SDK is exercised.** A real use case proves the plugin architecture.
- **No architecture change.** No orchestrator, no queue, no MCP changes beyond one tool.

### Negative

- **One more artifact to maintain.** Teams must write contracts before generating.
- **Schema is frozen at 20 fields.** Early contracts may reveal gaps; changes require version bumps.
- **Deterministic checks are limited.** Some quality issues require LLM checks, which are non-deterministic.
- **Adoption cost.** Teams already working without contracts need to adopt a new practice.

### Neutral

- LLM checks are opt-in.
- Fingerprint (ADR-004) is a sibling layer, not a dependency.

### Mitigations

- Provide contract templates for common story types.
- Ship deterministic checks first; LLM checks are opt-in.
- Start with one team; iterate only if a real case demands it.

---

## 12. Deferred Work

Deferred, not removed. Each item has a named trigger.

| Deferred item | Tasks | Revisit trigger |
|---|---|---|
| Multi-tenant isolation | 4 | 20+ orgs ask for hosted |
| Billing / Metering | 6 | SaaS committed |
| Contract schema v1.1 (add fields) | 3 | A real user cannot express a story in v1.0 |
| Contract repository / registry | 2 | Team #2 needs shared templates |
| LLM check calibration harness | 3 | False-positive rate exceeds 10% |
| Schema migration tooling | 2 | A breaking schema change is required |

**Total deferred: 20 tasks.** Not in scope for v1.0 or v1.1.

---

## 13. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Teams won't write contracts | Medium | High | Templates; two-week probe; if no adoption, kill the ADR |
| Schema gap reveals field 21 | High | Low | Version bump to v1.1 |
| LLM checks non-deterministic | Medium | Medium | Opt-in; structured evidence required |
| Plugin SDK path mismatch | Low | Medium | Verified in step 3 before implementation |
| Contract/story divergence | Medium | Medium | Sidecar `contract_hash` enables detection |
| Sidecar drift | Low | Medium | Stale sidecar treated as `blocked` |
| Secret leakage in contract | Low | High | C-10 scans before LLM |
| Prompt injection via contract text | Medium | High | L-03 detects; untrusted contracts bypass LLM entirely |
| Two contracts share an id | Low | Medium | E-05 flags both |
| Cross-tenant artifact leak | Low | High | Not applicable in v1.0 (no tenancy) |

---

## 14. Definition of Done

Inherits ADR-003's DoD. A task is Done when:

- [ ] Discovery cited at least one file inspected, with paths
- [ ] Tier (1/2/3) declared in the plan
- [ ] For Tier 1/2: reuse candidate verified in `docs/COMPONENT_SOURCING.md`
- [ ] Plan output before any implementation
- [ ] Plan included cost, rollback plan (if high-risk)
- [ ] Prior-review items applied or explicitly rejected
- [ ] If the task introduces a conditional, propagation pass performed
- [ ] Explicit APPROVE received
- [ ] All declared files created/modified
- [ ] All declared tests pass
- [ ] Verification commands run and output shown
- [ ] Regression suite passes
- [ ] Contract tests pass if public interface touched
- [ ] No secret leaks (`gitleaks`)
- [ ] No deviations, or deviations re-approved
- [ ] Docs updated
- [ ] Report output with next task ID and PR link

---

## 15. Rollback Plan

To remove ADR-005's changes:

1. Set `features.context_linter: false` — linter becomes a no-op; adapters still emit `Contract`, but nobody reads it.
2. Revert adapters to emit `Story` instead of `Contract`.
3. Drop the `norma.lint_contract` MCP tool.
4. Revert `NormaAgent` input type at v1.1 if applicable.

Contract files become inert `.context/` files. They cause no harm.

**Rollback cost: ≤1 day.**

**Rollback trigger:** If, after 4 weeks of use, fewer than 3 teams are writing contracts, or the linter catches no real problems, disable and re-evaluate.

---

## 16. Alternatives Considered

| Alternative | Why rejected |
|---|---|
| Continue with output-only gates | Late failure; expensive; hides the real problem |
| God agent that ingests stories and produces tests | Hidden assumptions; unsafe; hard to debug |
| Orchestrator with multiple agents | Unnecessary complexity for the workflow |
| Store contracts in Norma's DB | Makes Norma the owner; reintroduces the god component |
| Mutate the contract with lint results | Concurrent-write races; git diff noise; ownership blur |
| Freeze schema at 40 fields | Bet on 40 guesses; speculative complexity |
| Require OpenAPI specs only | Excludes stories without specs; excludes non-API work |
| Rely on prompt engineering only | Unreliable; no evidence trail; no enforceability |
| Skip the contract; extend ADR-004 to validate input | Couples validation to generation; violates single responsibility |

---

## 17. Status and Next Steps

**Status:** FROZEN.

**Immediate next steps:**
1. Write contract schema v1.0 (`docs/context-contract.md`).
2. Write one real contract for one real story.
3. Run the plugin SDK verification spike.
4. Implement the deterministic linter as a plugin.
5. Run end-to-end on one story.
6. Use it for two weeks. Measure.
7. Decide whether to proceed to v1.1 and ADR-004.

**Review triggers:**
- Any contract that cannot be expressed in v1.0
- Any linter finding that is consistently wrong
- Every 90 days
- On owner request

---

## 18. What This Version Is and Is Not

**Is:**

- The smallest scope that solves the input-validation problem.
- One YAML schema (20 fields). One linter (deterministic + opt-in LLM).
- Contract is immutable; linter writes to a sidecar.
- Content hash enables exact traceability.
- Plugin SDK alignment verified before implementation.
- Failure modes are named and resolved.
- Rollback is a one-day operation.
- Positioned in the three-layer verification stack.
- Internally consistent: task count, dependencies, arithmetic.

**Is not:**

- A platform.
- A multi-tenant SaaS.
- An orchestrator.
- A graph database.
- A pattern library.
- A registry or marketplace.
- A tool that owns the contract.
- A tool that mutates the contract during lint.

---

## 19. Changelog

| Version | Date | Change |
|---|---|---|
| 0.1 | 2026-09-24 | Initial: Context Contract + Context Linter concept |
| 0.2 | 2026-09-25 | Expanded schema (40 fields) |
| 0.9 | 2026-09-26 | Pre-freeze review: 20-field schema; sidecar file |
| **1.0** | **2026-09-27** | **FROZEN. Contract immutable; linter writes sidecar. Schema at 20 fields. C-16 added (PII implies owner). Failure modes enumerated. Rollback plan added. Plugin SDK verification step added. Three-layer stack positioning (§9.5). ADR-004 cross-reference. Score projection removed (would be circular).** |

---

## 20. The One-Paragraph Summary

> Norma has output gates but no input contract. This ADR adds the Context Contract — a frozen 20-field YAML file carrying intent, scope, acceptance criteria, sources, trust, and budget for one story — and the Context Linter — a pure function, shipped as a Norma plugin, that validates the contract against CAFE(S) and writes its findings to a sidecar file. The contract sits in front of Norma, not inside it. The linter runs before `NormaAgent`; gates Q0–Q10 run after. Together they form a complete harness. The contract is a file that lives in the repository; Norma reads it, does not own it, and never mutates it. This is a 1.5-week addition that turns Norma from a generator into a harness. No new releases beyond v1.0 and v1.1. No orchestrator. No queue. No platform. Just the piece that was always missing.

---

## 21. The One-Line Summary

> **The smallest useful component is not an agent. It is a Context Contract. The smallest active component is a Context Linter. Build those two.**

---

## Appendix A — CAFE(S) Checklist for Authors

Before running the linter, authors can self-check:

| CAFE(S) | Self-check question |
|---|---|
| Clarity | Are all domain terms defined? Are actors unambiguous? |
| Actionability | Does every AC have a clear given/when/then? Is DoD measurable? |
| Fidelity | Does every source have a version? Are design sources fresh? |
| Efficiency | Is the token budget realistic? Is `scope.out` non-empty? |
| Security | Is trust set correctly? Are `allowed_sources` correct? Is PII flagged? |

## Appendix B — Linter Check Catalog (v1.0)

Full catalog with severities, evidence requirements, and fix hints available in `docs/context-linter.md` (to be written alongside the linter implementation).

## Appendix C — Versioning Policy

- Schema frozen at v1.0 with 20 fields.
- Fields added only when a real user's case forces it, and only with a version bump to v1.1, v2.0, etc.
- The linter checks the `version` field (C-14) and refuses contracts with unknown versions.
- Migration between versions is the author's responsibility, not Norma's.
- Every schema change is a deliberate PR with a migration script, tested in CI with sample contracts.

## Appendix D — Where This Sits in the Stack

```
ADR-005  →  Context Contract + Linter      (input gate)
ADR-003  →  Norma pipeline + Q0–Q10         (generation)
ADR-004  →  Fingerprint + closed-loop       (output gate)
ADR-006  →  Feature file correctness        (if written)
```

ADR-005 ships first. ADR-004 ships second. ADR-006 ships only if needed.

---

**End of ADR-005 v1.0.**

**Status: FROZEN.**
**Total tasks: 10 (v1.0: 7, v1.1: 3).**
**Total phases: 2.**
**Duration: ~1.5 weeks (v1.0) + 3 days (v1.1).**
**The contract is data. The linter is a pure function. Norma reads; Norma does not own. The sidecar is written; the contract is immutable.**