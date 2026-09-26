# AEGIS-P1 Contract Evidence

- **Requirement:** `AEGIS-P1-CONTRACTS`
- **Release profile:** `aegis-foundation`
- **Verified:** 2026-09-23
- **Implementation:** `antinode_aegis/contracts.py`, `antinode_aegis/config.py`
- **Phase status:** Implemented; this record covers the versioned public API
  contract slice of P1.

## Commands

```text
python -m pytest tests/unit/test_aegis_contracts.py tests/unit/test_aegis_api_contract.py --no-cov -q
```

## Result

- Shared requirement IR round-trip tests pass.
- Unknown contract fields are rejected.
- Aegis configuration is disabled by default and bounds repair attempts.
- Canonical `/v1` import and generation paths expose the expected methods and
  typed OpenAPI response schemas.
- Legacy `/v1/api` aliases remain method-compatible with canonical operations.
