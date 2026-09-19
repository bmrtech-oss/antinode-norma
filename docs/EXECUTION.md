# Execution Maturity & Test Runners — Antinode Norma

This document outlines the parallel execution engine, retry mechanisms, test artifact capture, reporting frameworks, cloud grid integration, and flake detection.

---

## 1. Execution Architecture

Antinode Norma provides an enterprise execution engine for running Gherkin scenario suites at scale.

```text
[Gherkin Feature Suite]
          │
          ▼
 [ParallelExecutor] ──► (Multithread / Multiprocess Worker Pool)
          │
          ▼
   [RetryEngine] ─────► (Exponential Backoff Retries)
          │
          ▼
 [ArtifactManager] ──► (Screenshots, Video Recordings, Playwright Traces)
          │
          ▼
  [Reporters & DB] ──► (JUnit XML, Allure v2 JSON, HTML, Execution History)
```

---

## 2. Parallel Execution & Retries (`antinode_norma/execution/`)

- **`ParallelExecutor`**: Executes test scenarios in parallel across configurable worker processes (`max_workers`).
- **`RetryEngine`**: Retries failing test scenarios with exponential backoff (`retries`, `retry_delay`).
- **`FlakeDetector`**: Calculates scenario flakiness scores based on pass/fail history across runs.
- **`ExecutionHistoryStore`**: Persists scenario run history and flakiness metrics.

---

## 3. Test Artifacts & Reporters

- **`ArtifactManager`**: Captures screenshots, video recordings, and Playwright trace archives on test step failure.
- **Reporters**:
  - **JUnit XML**: Standard CI/CD test results format (`build/reports/junit.xml`).
  - **Allure v2**: Rich visual test reporting (`build/reports/allure-results/`).
  - **HTML Reporter**: Standalone interactive HTML report.

---

## 4. Cloud Grid Driver Support

Supported cloud execution providers configured via `execution.cloud_provider` in `norma.config.yml`:
- **BrowserStack**
- **Sauce Labs**
- **LambdaTest**
