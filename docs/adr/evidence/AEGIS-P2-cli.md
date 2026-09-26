# AEGIS-P2 CLI Subcommands Evidence

- **Requirement:** `AEGIS-P2-CLI`
- **Release profile:** `aegis-foundation`
- **Task:** `P2-T05`
- **Verified:** 2026-09-23
- **Implementation:** `antinode_norma/cli.py`

## Commands

```text
python -m pytest tests/unit/test_aegis_cli.py --no-cov -q
```

## Result

- `anorm aegis normalize` exposes CSV, XLSX, and story normalization through
  one CLI contract.
- Output is JSON-serialized versioned `RequirementIR`.
- Story input accepts inline JSON or a JSON file path.
- Invalid input produces a non-zero CLI result with an explicit error.
