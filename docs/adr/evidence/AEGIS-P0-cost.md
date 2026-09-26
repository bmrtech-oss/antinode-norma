# AEGIS-P0 Cost Model Evidence

- **Requirement:** `AEGIS-P0-COST`
- **Release profile:** `aegis-foundation`
- **Phase:** P0
- **Task:** `P0-T02`
- **Verified:** 2026-09-23
- **Implementation:** `docs/COST.md`, `antinode_norma/evaluate/cost.py`

## Commands

```text
python -m pytest tests/unit/test_aegis_p0_cost.py tests/unit/test_cost_tracker_p5_t05.py --no-cov -q
```

## Result

- Input/output token pricing is documented and matches the implemented
  `CostTracker` formula.
- Cost records are written to `build/llm_cost.jsonl` and can be aggregated.
- Exact or semantic cache hits are documented as zero-provider-cost paths.
- The evaluation cost gate passes at `$0.02` and fails above the threshold.
- The cost model is an estimate; provider pricing must be revalidated before a
  release profile is approved.
