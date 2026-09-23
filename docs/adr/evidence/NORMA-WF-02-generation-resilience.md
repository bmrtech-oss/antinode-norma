# Norma workflow generation resilience evidence

- **Requirement:** `NORMA-WF-02`
- **Command:** `pytest -q tests/unit/test_import_api.py tests/unit/test_generation_provider_resilience_gen4_t08.py`
- **Evidence:** Existing generation workflow and provider resilience regression
  coverage for progress, retry, cancellation, and failure handling.
