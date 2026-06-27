# Testing Guide for Antinode Norma

This document provides step‑by‑step instructions for setting up, running, and extending the test suite for **Antinode Norma**.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Installing Development Dependencies](#2-installing-development-dependencies)
3. [Configuring Test Environment Variables](#3-configuring-test-environment-variables)
4. [Understanding the Test Structure](#4-understanding-the-test-structure)
5. [Running the Tests](#5-running-the-tests)
6. [Interpreting Test Output](#6-interpreting-test-output)
7. [Writing New Tests](#7-writing-new-tests)
8. [Continuous Integration (CI)](#8-continuous-integration-ci)
9. [Testing the Code Generation Module](#9-testing-the-code-generation-module)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. Prerequisites

Before running the tests, ensure you have:

- **Python 3.9+** installed on your system.
- **Git** (to clone the repository).
- A **virtual environment** (recommended) to isolate dependencies.

---

## 2. Installing Development Dependencies

If you haven't already, clone the repository and install the package:

```bash
git clone https://github.com/antinodelabs/antinode-norma.git
cd antinode-norma
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -e .
```

Now install the **development dependencies** from `requirements-dev.txt`:

```bash
pip install -r requirements-dev.txt
```

This installs:

- `pytest` – the test runner.
- `pytest-cov` – for code coverage reporting.
- `pytest-asyncio` – for testing asynchronous code.
- `pytest-mock` – for mocking in tests.

---

## 3. Configuring Test Environment Variables

Certain tests (integration) require API keys to call external services.

1. Copy the example environment file and fill in your credentials:

   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and set **at least**:

   ```ini
   # Required for integration tests
   OPENROUTER_API_KEY=sk-or-...
   ```

   Optional (for JIRA connector tests):

   ```ini
   JIRA_SERVER=https://your-company.atlassian.net
   JIRA_TOKEN=your_api_token
   ```

> **Note:** Unit tests do **not** require any external credentials and will run without these variables.

---

## 4. Understanding the Test Structure

The tests are organised into three main directories:

```
tests/
├── unit/                 # Pure logic, fast, no external calls
│   ├── test_quality.py
│   ├── test_schemas.py
│   ├── test_parser.py
│   ├── test_validator.py
│   ├── test_gherkin_generator.py
│   ├── test_runner.py
│   └── test_config.py
├── integration/          # Real LLM / file system calls
│   ├── test_cli.py
│   ├── test_llm_factory.py
│   └── test_runner.py
└── connectors/           # Tests for external integrations (mocked)
    └── test_jira_connector.py
```

- **Unit tests** (`unit/`): Test individual functions in isolation. Mocks are used to replace external dependencies (LLM, file system).
- **Integration tests** (`integration/`): Exercise the system end‑to‑end using real LLM calls and file I/O. These are slower and require API keys.
- **Connector tests** (`connectors/`): Test adapters to external systems (JIRA, etc.). They can be unit‑tested with mocks or run as integration tests.

---

## 5. Running the Tests

### 5.1 Run All Tests (Unit + Integration)

```bash
pytest
```

This will execute **all** tests. If you do not have `OPENROUTER_API_KEY` set, integration tests will be skipped automatically with a message.

### 5.1a Run Tests Inside Docker/Podman

If you prefer to run tests in the local containerized environment, build the image and run:

```bash
docker compose build

docker compose run --rm app pytest
```

For Podman:

```bash
podman compose build

podman compose run --rm app pytest
```

This uses the same development image and dependencies as the local Docker workflow.

### 5.2 Run Only Unit Tests (Fast)

```bash
pytest -m "not integration"
```

This runs only the `unit/` tests and skips any test marked with the `integration` marker.

### 5.3 Run Only Integration Tests

```bash
pytest -m integration
```

This runs only tests that call real LLMs or external services. **Ensure your `.env` is correctly configured** before running these.

### 5.4 Run a Specific Test File

```bash
pytest tests/unit/test_quality.py
```

### 5.5 Run a Specific Test Function

```bash
pytest tests/unit/test_quality.py::test_is_independent
```

### 5.6 Generate a Coverage Report

```bash
pytest --cov=antinode_norma --cov-report=term-missing
```

To create an HTML report for easier browsing:

```bash
pytest --cov=antinode_norma --cov-report=html
```

Open `htmlcov/index.html` in your browser to explore the coverage details.

---

## 6. Interpreting Test Output

A successful test run looks like:

```
============================= test session starts ==============================
platform win32 -- Python 3.9.7, pytest-7.4.0, pluggy-1.0.0
rootdir: D:\incubator\antinode-norma
plugins: asyncio-0.21.0, cov-4.0.0, mock-3.10.0
collected 24 items

tests/unit/test_quality.py ............                                 [ 50%]
tests/unit/test_schemas.py ....                                          [ 66%]
tests/unit/test_parser.py .                                              [ 70%]
tests/unit/test_validator.py ...                                         [ 83%]
tests/unit/test_gherkin_generator.py ..                                  [ 91%]
tests/unit/test_runner.py ....                                           [100%]

=============================== warnings summary ===============================
... (optional warnings)

----------- coverage: platform win32, python 3.9.7 -----------
Name                                          Stmts   Miss  Cover
-----------------------------------------------------------------
antinode_norma/cli.py                            26     16    38%
antinode_norma/core/gherkin_generator.py          6      0   100%
antinode_norma/core/parser.py                     9      0   100%
antinode_norma/core/quality.py                   50      0   100%
antinode_norma/core/schemas.py                   13      0   100%
antinode_norma/core/validator.py                 13      1    92%
antinode_norma/runner.py                         48     10    79%
antinode_norma/utils/file_writer.py              6      0   100%
antinode_norma/utils/llm_factory.py             60     18    70%
-----------------------------------------------------------------
TOTAL                                           231     45    81%

========================= 24 passed, 5 skipped in 12.34s =========================
```

- **`.`, `F`, `E`**: Each dot means a test passed; `F` means failure; `E` means error.
- **Skipped tests**: These are integration tests that were skipped because credentials were missing. They are counted as "skipped".
- **Coverage report**: Shows which lines of code are not exercised by tests. Aim for higher coverage over time.

---

## 7. Writing New Tests

### 7.1 Unit Tests

- Place your test file in `tests/unit/`.
- Name it `test_*.py`.
- Use `pytest` fixtures from `conftest.py` where possible.
- Mock external dependencies using `pytest-mock` or `unittest.mock`.

**Example: Testing a pure function**

```python
# tests/unit/test_my_module.py
from antinode_norma.my_module import my_function

def test_my_function():
    assert my_function(2, 3) == 5
```

### 7.2 Integration Tests

- Place in `tests/integration/`.
- Mark the test with `@pytest.mark.integration` so it can be skipped when credentials are missing.
- Use `pytest.skipif` to skip when environment variables are not set.

**Example:**

```python
import pytest
import os

@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("OPENROUTER_API_KEY"), reason="API key missing")
def test_real_llm():
    # Your test using real LLM
    pass
```

### 7.3 Adding a New Fixture

If you need a shared fixture, define it in `tests/conftest.py` and decorate with `@pytest.fixture`. Then use it in any test file by referencing its name.

---

## 8. Continuous Integration (CI)

To automatically run tests on every commit, set up GitHub Actions with a workflow like `.github/workflows/tests.yml`:

```yaml
name: Test Suite

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.9", "3.10", "3.11"]

    steps:
      - uses: actions/checkout@v4
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e .
          pip install -r requirements-dev.txt
      - name: Run unit tests (no credentials)
        run: pytest -m "not integration" --cov=antinode_norma
      - name: Upload coverage report
        uses: codecov/codecov-action@v4
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
```

This workflow:

- Runs on every push and pull request.
- Tests against Python 3.9, 3.10, and 3.11.
- Runs only **unit tests** (integration tests would require secrets).
- Uploads coverage to Codecov (optional).

If you want to run integration tests in CI, store your `OPENROUTER_API_KEY` as a GitHub secret and expose it in the environment.

---

## 9. Testing the Code Generation Module

The code generation module (`antinode_norma.codegen`) has its own test suite. Below is guidance on testing the various components.

### 9.1 Test Structure for Codegen

The codegen tests should be organised as follows:

```text
tests/
├── unit/
│   └── codegen/
│       ├── test_models.py          # Test dataclasses (TestSuite, TestCase, etc.)
│       ├── test_rules.py           # Test RuleEngine step mapping
│       ├── test_parsers.py         # Test GherkinParser (with mock files)
│       └── test_emitters.py        # Test emitters with mock TestSuite
├── integration/
│   └── codegen/
│       ├── test_gherkin_parser.py  # Test with real .feature files
│       ├── test_orchestrator.py    # Test end‑to‑end generation
│       └── test_emitters_real.py   # Test emitters with real output
└── fixtures/
    └── codegen/
        ├── login.feature           # Sample feature file
        └── expected/               # Expected output files
```

### 9.2 Running Codegen Tests

```bash
# Run all codegen tests
pytest tests/unit/codegen/ tests/integration/codegen/

# Run only unit tests (fast)
pytest tests/unit/codegen/ -m "not integration"

# Run only integration tests (requires real LLM or file system)
pytest tests/integration/codegen/ -m integration
```

### 9.3 Sample Unit Test: RuleEngine

```python
# tests/unit/codegen/test_rules.py
import pytest
from antinode_norma.codegen.engine.rules import RuleEngine
from antinode_norma.codegen.models.test_model import ActionType

def test_navigate_rule():
    engine = RuleEngine()
    action, target, value, options = engine.map_step("Given I navigate to \"https://example.com\"")
    assert action == ActionType.NAVIGATE
    assert value == "https://example.com"

def test_click_rule():
    engine = RuleEngine()
    action, target, value, options = engine.map_step("When I click on \"#login-button\"")
    assert action == ActionType.CLICK
    assert target == "#login-button"

def test_fill_rule():
    engine = RuleEngine()
    action, target, value, options = engine.map_step("And I fill \"test@example.com\" into \"#email\"")
    assert action == ActionType.FILL
    assert target == "#email"
    assert value == "test@example.com"
```

### 9.4 Sample Integration Test: Orchestrator

```python
# tests/integration/codegen/test_orchestrator.py
import pytest
from pathlib import Path
from antinode_norma.codegen import Orchestrator

@pytest.mark.integration
def test_orchestrator_generate_playwright(tmp_path):
    # Create a temporary feature file
    feature_path = tmp_path / "test.feature"
    feature_path.write_text("""
        Feature: Test Feature
          Scenario: Test Scenario
            Given I navigate to "https://example.com"
            When I click on "#button"
    """)

    orchestrator = Orchestrator()
    orchestrator.generate(
        feature_path=feature_path,
        output_dir=tmp_path / "output",
        framework="playwright"
    )

    # Check that the file was created
    output_file = tmp_path / "output" / "test_feature.spec.ts"
    assert output_file.exists()
    content = output_file.read_text()
    assert "await page.goto('https://example.com')" in content
    assert "await page.locator('#button').click()" in content
```

### 9.5 Testing Emitters with Quality Enhancements

```python
# tests/unit/codegen/test_emitters.py
from antinode_norma.codegen.emitters.playwright_emitter import PlaywrightEmitter
from antinode_norma.codegen.models.test_model import TestSuite, TestCase, TestStep, ActionType

def test_playwright_emitter_with_page_objects(tmp_path):
    # Create a test suite
    suite = TestSuite(
        name="Login",
        cases=[
            TestCase(
                name="Successful Login",
                steps=[
                    TestStep(action=ActionType.NAVIGATE, value="https://example.com/login"),
                    TestStep(action=ActionType.FILL, target="#email", value="test@example.com"),
                    TestStep(action=ActionType.CLICK, target="#login-button"),
                ]
            )
        ]
    )

    # Configure emitter with quality settings
    emitter = PlaywrightEmitter()
    # Set quality config (simplified for test)
    emitter.quality.use_page_objects = True

    emitter.emit(suite, tmp_path)

    # Check main test file
    assert (tmp_path / "login.spec.ts").exists()
    # Check page objects
    assert (tmp_path / "pages" / "loginpage.page.ts").exists()
```

### 9.6 Test Fixtures

Create sample feature files in `tests/fixtures/codegen/`:

**`login.feature`**:
```gherkin
Feature: Login
  Scenario: Successful login
    Given I navigate to "https://example.com/login"
    When I fill "test@example.com" into "#email"
    And I fill "SecurePass123" into "#password"
    And I click on "#login-button"
    Then I should see "Welcome"
```

### 9.7 Mocking External Dependencies

For unit tests, mock the file system and LLM calls:

```python
# tests/unit/codegen/test_parsers.py
from unittest.mock import mock_open, patch
from antinode_norma.codegen.parsers.gherkin_parser import GherkinParser

def test_parser_with_mock_file():
    mock_content = """
        Feature: Test
          Scenario: Test
            Given I navigate to "https://example.com"
    """
    with patch("builtins.open", mock_open(read_data=mock_content)):
        parser = GherkinParser()
        # The parser reads from a Path, so we need to mock Path.read_text
        # or pass a string directly. Adjust as needed.
        # For this example, we'd use a real file or a StringIO.
        pass
```

### 9.8 Coverage

To generate coverage specifically for the codegen module:

```bash
pytest --cov=antinode_norma.codegen --cov-report=html tests/unit/codegen/ tests/integration/codegen/
```

### 9.9 Continuous Integration

Ensure the codegen tests are included in your CI pipeline (`.github/workflows/ci.yml`):

```yaml
- name: Run codegen tests
  run: |
    pytest tests/unit/codegen/ -m "not integration"
    # Integration tests require API keys – run conditionally
```

---

## 10. Troubleshooting

| Problem | Solution |
| :--- | :--- |
| `ModuleNotFoundError: No module named 'antinode_norma'` | Run `pip install -e .` to install the package in editable mode. |
| `OPENROUTER_API_KEY not set` in integration tests | Create a `.env` file or set the variable in your shell: `export OPENROUTER_API_KEY=...` |
| Tests are very slow | Run only unit tests: `pytest -m "not integration"` |
| `pytest` not found | Activate your virtual environment (`source venv/bin/activate`) or install `pytest` globally (`pip install pytest`) |
| Coverage report shows missing lines | Add more tests to cover untested code paths. |
| `Error: asyncio.run() cannot be called from a running event loop` | Ensure your test function is marked with `@pytest.mark.asyncio`. |

---

*Last updated: 2026-06-25*
