# AEGIS-P3a-T03 Q3/Q4 Traceability Evidence

- **Requirement:** `AEGIS-P3A-T03`
- **Release profile:** `aegis-foundation`
- **Phase:** P3a
- **Task:** `P3a-T03`
- **Status:** Implemented
- **Verified:** 2026-09-25

## Scope

- Q3 verifies that every known `TestCase.id` is represented by a Gherkin tag.
- Q4 rejects unknown non-system tags and permits approved system tags and
  explicit test-case tags.
- IDs and tags are compared case-insensitively with a normalized leading `@`.
- Both gates are hard gates and return typed `GateResult` values.

## Evidence

- Implementation: `antinode_norma/gates/traceability.py`
- Gate registration: `antinode_norma/gates/runner.py`
- Focused tests: `tests/unit/test_gates_p3a_t03.py`

## Verification command

```text
.\venv\Scripts\python.exe -m pytest tests/unit/test_gates_p3a_t03.py -q --no-cov
```

**Expected result:** `4 passed`

The full regression suite remains the release-candidate verification command
and must be rerun before a release profile is declared.
