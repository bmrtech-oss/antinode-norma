# AEGIS-P2 Unified Normalize Evidence

- **Requirement:** `AEGIS-P2-NORMALIZE`
- **Release profile:** `aegis-foundation`
- **Task:** `P2-T04`
- **Verified:** 2026-09-23
- **Implementation:** `antinode_aegis/shared_ir.py`

## Commands

```text
python -m pytest tests/unit/test_aegis_shared_ir.py tests/unit/test_aegis_csv.py tests/unit/test_aegis_xlsx.py tests/unit/test_aegis_story.py --no-cov -q
```

## Result

- CSV, XLSX/Excel, and story/dict inputs dispatch through their Aegis adapters.
- All supported input types return the same versioned `RequirementIR` contract.
- Worksheet and story references remain part of provenance.
- Unsupported kinds fail explicitly.
