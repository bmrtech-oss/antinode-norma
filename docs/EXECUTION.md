# Execution Maturity Guide (Phase 8)

This document describes the execution maturity capabilities of the Antinode Norma BDD platform (Phase 8, Track B).

---

## 1. Overview

Norma BDD supports enterprise-grade scenario execution capabilities matching dedicated test runners:

- **Parallel Execution (`P8-T01`):** Multi-threaded scenario execution with configurable worker pools.
- **Retry with Exponential Backoff (`P8-T02`):** Automatic retries for transient failures with configurable backoff multipliers.
- **Artifact Capture (`P8-T03`):** Automatic attachment of screenshots, video recordings, trace files, and logs per scenario run.
- **Standardized Reporters (`P8-T04`):** Output formatting for JUnit XML, Allure v2 JSON, and standalone HTML reports.
- **Cloud Grid Integration (`P8-T05`):** Native dispatch to cloud test grids (BrowserStack, Sauce Labs, LambdaTest), controlled by feature flag `execution_cloud`.
- **Flake Detection (`P8-T06`):** Historical tracking of scenario pass/fail results to flag flaky tests and compute flake rates.
- **Execution History Tracking (`P8-T07`):** Persistent JSON storage (`build/execution_history.json`) for historical run analysis.

---

## 2. Component Usage

### 2.1 Parallel Execution

```python
from antinode_norma.execution import ParallelExecutor

executor = ParallelExecutor(max_workers=4)
tasks = [
    lambda: run_scenario("Scenario 1"),
    lambda: run_scenario("Scenario 2"),
]
result = executor.execute_tasks(tasks)
print(f"Executed {result.total_tasks} tasks in {result.duration_seconds:.2f}s")
```

### 2.2 Retry with Backoff

```python
from antinode_norma.execution import retry_with_backoff

def flaky_network_call():
    # Attempt operation
    ...

result = retry_with_backoff(
    flaky_network_call,
    max_retries=3,
    initial_delay=0.5,
    backoff_factor=2.0
)
if result.success:
    print(f"Succeeded after {result.attempts} attempt(s)")
```

### 2.3 Artifact Capture

```python
from antinode_norma.execution import ArtifactManager, ArtifactType

manager = ArtifactManager(artifact_dir="build/artifacts")
screenshot = manager.capture_screenshot("scenario_101", b"PNG_DATA...")
print(f"Saved artifact to {screenshot.file_path}")
```

### 2.4 Reporting (JUnit, Allure, HTML)

```python
from antinode_norma.execution import ExecutionReporter

reporter = ExecutionReporter(output_dir="build/reports")
reporter.generate_junit_xml(execution_results)
reporter.generate_allure_json(execution_results)
reporter.generate_html_report(execution_results)
```

### 2.5 Cloud Grid Runners

Gated by `features.execution_cloud` in `norma.config.yml`:

```yaml
features:
  execution_cloud: true
```

```python
from antinode_norma.execution import CloudRunner, CloudConfig, CloudProvider

config = CloudConfig(
    provider=CloudProvider.BROWSERSTACK,
    username="user",
    access_key="key",
    browser="chrome",
    os="OS X",
    os_version="Sonoma"
)
runner = CloudRunner(config)
remote_url = runner.get_remote_url()
```

### 2.6 Flake Detection

```python
from antinode_norma.execution import FlakeDetector

detector = FlakeDetector(history_file="build/flake_history.json")
detector.record_result("Scenario: User login", passed=True)
flake_rate = detector.get_flake_rate("Scenario: User login")
print(f"Flake rate: {flake_rate:.2%}")
```

### 2.7 Execution History Persistence

```python
from antinode_norma.execution import ExecutionHistoryStore, ExecutionHistoryRecord

store = ExecutionHistoryStore(history_file="build/execution_history.json")
record = ExecutionHistoryRecord(
    id="run-101",
    status="PASSED",
    total_scenarios=10,
    passed_scenarios=10,
    failed_scenarios=0
)
store.save_run(record)
recent_runs = store.get_history(limit=10)
```

---

## 3. Configuration & Feature Flags

Cloud grid execution requires setting `execution_cloud: true` under `features` in `norma.config.yml` or using the `NORMA_FEATURE_EXECUTION_CLOUD=true` environment variable.
