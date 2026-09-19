# Quality Gates & Evaluation Framework — Antinode Norma

This document defines the Quality Gate architecture (Q0–Q10), aggregate criteria, and evaluation metrics implemented in Antinode Norma.

---

## 1. Overview

Quality gates evaluate generated Gherkin feature files before they are accepted or committed. Quality gates are divided into **Hard Gates (Q0–Q5)** and **Soft Gates (Q6–Q10)**.

---

## 2. Quality Gate Reference

### 2.1 Hard Gates (Q0–Q5)
Hard gates are binary checks. Every hard gate must pass (`hard_pass: true`). Any hard gate failure triggers the `NormaAgent` repair loop.

| Gate | Name | Description | Failure Condition |
|---|---|---|---|
| **Q0** | Norma Validator | Structural & INVEST validation check | Malformed story structure or failed INVEST criteria |
| **Q1** | Syntax Gate | Gherkin syntax parsing using `gherkin-official` parser | Invalid Gherkin keywords or parse error |
| **Q2** | No-RSpec Guard | Disallows RSpec/unit-test tokens in Gherkin | Presence of `describe`, `context`, `expect`, `should`, `let`, `before`, `after` |
| **Q3** | Traceability Tag Gate | Validates `@TestCase.id` tags match story input | Missing requirement ID tag on Scenario |
| **Q4** | Orphan Tag Guard | Ensures no undefined tags exist | Tag does not match configured or story tag schema |
| **Q5** | Duplicate Guard | Checks for duplicate scenario names in feature | Two scenarios share identical names |

---

### 2.2 Soft Gates (Q6–Q10)
Soft gates compute numerical scores between 0.0 and 1.0. The aggregate soft score must meet threshold `soft_score >= 0.85`.

| Gate | Name | Metric / Threshold | Description |
|---|---|---|---|
| **Q6** | Declarative Style | Score ≥ 0.90 | Penalizes imperative UI actions (e.g. "I click button #submit-id") in favor of declarative business intent |
| **Q7** | Vocabulary Reuse | Score ≥ 0.90 | Measures reuse of existing step definitions across feature files |
| **Q8** | Outline Usage | Score = 1.00 | Enforces `Scenario Outline` with `Examples:` for tabular / combinatorial test cases |
| **Q9** | State Model | Score = 1.00 | Verifies proper Given (state) -> When (action) -> Then (outcome) state transitions |
| **Q10** | Semantic Judge | Score ≥ 0.85 | LLM-based evaluation measuring domain accuracy and specification quality |

---

## 3. Aggregate Verdict Thresholds

A feature file is declared `VERDICT_PASS` if:
1. `hard_pass == True` (Q0 through Q5 pass 100%)
2. `soft_score >= 0.85` (Average of Q6–Q9)
3. `sem_score >= 0.85` (Q10 Semantic Judge score)

---

## 4. Evaluation Harness Thresholds

When running the Evaluation Harness (`python -m antinode_norma.evaluate.harness`), platform performance across test datasets is measured against the following SLA gates:

| Metric | SLA Threshold | Description |
|---|---|---|
| `pass_rate` | ≥ 0.95 | Overall pass rate of generated feature specs |
| `first_attempt_syntax_rate` | ≥ 0.90 | Pass rate on attempt 1 without repair loop |
| `avg_attempts` | ≤ 1.50 | Average generation attempts per feature |
| `determinism_score` | ≥ 0.80 | Reproducibility score with exact/semantic cache |
| `avg_sem_score` | ≥ 0.85 | Mean Q10 semantic score |
| `cost_per_run` | ≤ $0.02 | Maximum allowable average LLM cost per run |
