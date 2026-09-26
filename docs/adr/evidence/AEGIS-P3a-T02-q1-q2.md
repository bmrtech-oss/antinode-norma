# AEGIS-P3a-T02 Q1 Syntax and Q2 No-RSpec Evidence

- **Requirement:** `AEGIS-P3A-T02`
- **Release profile:** `aegis-foundation`
- **Phase:** P3a
- **Task:** `P3a-T02`
- **Status:** Implemented
- **Verified:** 2026-09-25

## Scope

- Q1 uses `gherkin-official` through the shared Gherkin validator.
- The validator retains explicit checks for the required Feature and Scenario
  structure and incomplete step keywords.
- Q2 rejects standalone RSpec/unit-test vocabulary with word-boundary matching,
  avoiding false positives in ordinary words such as `beforehand`.
- Both gates are hard gates and return typed `GateResult` values.

## Evidence

- Q1 implementation: `antinode_norma/gates/syntax.py`
- Q2 implementation: `antinode_norma/gates/rspec_guard.py`
- Shared parser validation: `antinode_norma/core/validator.py`
- Focused tests: `tests/unit/test_gates_p3a_t02.py`

## Verification command

```text
.\venv\Scripts\python.exe -m pytest tests/unit/test_gates_p3a_t02.py -q --no-cov
```

**Expected result:** `6 passed`

The full regression suite remains the release-candidate verification command
and must be rerun before a release profile is declared.
