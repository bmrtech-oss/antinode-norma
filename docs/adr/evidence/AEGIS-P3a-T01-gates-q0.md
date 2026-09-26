# AEGIS-P3a-T01 Gate Types, Aggregator, and Q0 Evidence

- **Requirement:** `AEGIS-P3A-T01`
- **Release profile:** `aegis-foundation`
- **Phase:** P3a
- **Task:** `P3a-T01`
- **Verified:** 2026-09-24
- **Implementation:** `antinode_norma/gates/types.py`,
  `antinode_norma/gates/aggregate.py`,
  `antinode_norma/gates/norma_validator.py`,
  `antinode_norma/gates/runner.py`

## Commands

```text
python -m pytest tests/unit/test_aegis_p3a_t01.py tests/unit/test_gates_p3a_t01.py --no-cov -q
```

## Result

- `GateContext` and `BaseGate` provide the typed gate contract.
- Q0 rejects empty input, delegates valid Gherkin to the Norma validator, and
  emits a hard-gate `GateResult`.
- The aggregator requires all hard gates to pass and applies the documented
  `0.85` soft and semantic thresholds.
- `GateRunner` registers Q0 first, followed by Q1-Q10 in the declared order.
