# AEGIS-P2 XLSX Ingester Evidence

- **Requirement:** `AEGIS-P2-XLSX`
- **Release profile:** `aegis-foundation`
- **Task:** `P2-T02`
- **Verified:** 2026-09-23
- **Implementation:** `antinode_aegis/xlsx.py`

## Commands

```text
python -m pytest tests/unit/test_aegis_xlsx.py tests/unit/test_ingest.py --no-cov -q
```

## Result

- Worksheet selection uses the existing Norma XLSX ingester behavior.
- XLSX rows are returned as versioned Aegis `RequirementIR` values.
- Source kind, path, and selected worksheet are preserved as provenance.
- Missing files continue to raise `FileNotFoundError`.
