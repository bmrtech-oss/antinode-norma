# AEGIS-P1 Shared IR Evidence

- **Requirement:** `AEGIS-P1-SHARED-IR`
- **Release profile:** `aegis-foundation`
- **Task:** `P1-T03`
- **Verified:** 2026-09-23
- **Implementation:** `antinode_aegis/shared_ir.py`

## Commands

```text
python -m pytest tests/unit/test_aegis_shared_ir.py --no-cov -q
```

## Result

- CSV and story inputs use the existing Norma normalization path.
- Both inputs produce the versioned Aegis `RequirementIR`.
- Source kind and source reference are preserved as provenance.
- The shared IR remains convertible to the existing Norma `TestCase`.
