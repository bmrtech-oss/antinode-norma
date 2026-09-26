# AEGIS-P3a-T04 Q5 Duplicate Scenario Evidence

- **Requirement:** `AEGIS-P3A-T04`
- **Release profile:** `aegis-foundation`
- **Phase:** P3a
- **Task:** `P3a-T04`
- **Status:** Implemented
- **Verified:** 2026-09-25

## Scope

- Q5 identifies duplicate `Scenario` and `Scenario Outline` titles.
- Comparison normalizes whitespace and case so equivalent titles are detected.
- Unique scenarios and outlines pass the hard gate.
- The gate returns a typed `GateResult` with the duplicate titles and a repair
  suggestion when validation fails.

## Evidence

- Implementation: `antinode_norma/gates/duplicates.py`
- Gate registration: `antinode_norma/gates/runner.py`
- Focused tests: `tests/unit/test_gates_p3a_t04.py`

## Verification command

```text
.\venv\Scripts\python.exe -m pytest tests/unit/test_gates_p3a_t04.py -q --no-cov
```

**Expected result:** `2 passed`

The full regression suite remains the release-candidate verification command
and must be rerun before a release profile is declared.
