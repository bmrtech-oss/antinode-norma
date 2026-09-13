# Cost Model & Token Governance (ADR-001 §5.2)

This document specifies the LLM cost model, token consumption baselines, cost gate thresholds, prompt caching ROI, and execution cost logging format for Antinode Norma.

---

## 1. LLM Token Usage Baseline

All cost calculations are baselined against `gpt-4o-mini` (or equivalent lightweight model tier) with standard pricing assumptions:

| Operation | Input Tokens | Output Tokens | Est. Cost / Call |
|---|---|---|---|
| **Avg Generation Prompt** | 2,000 in | 1,500 out | ~$0.00105 |
| **Avg Judge Prompt** | 3,000 in | 500 out | ~$0.00090 |

---

## 2. Cost Projections per Workflow

- **Standard Run (2 attempts + 1 judge pass):** ~$0.003 / run
- **Evaluation Cycle (N=10 golden dataset run):** ~$0.03 / cycle
- **Cached Run (70% prompt cache hit rate):** ~$0.001 / run

---

## 3. Cost Gate & Evaluation Rules

To prevent unexpected token burn or prompt explosion in automated evaluation cycles and CI pipelines, a strict **Cost Gate** is enforced:

```text
Cost Gate Rule:
cost_per_run <= $0.02
```

### Gate Behavior
- If `cost_per_run > $0.02`, the evaluation/CI pipeline **fails immediately**.
- Cost gate failure requires prompt review, token budget optimization, or cache warm-up before re-running.

---

## 4. Prompt Caching & ROI

Prompt caching drastically reduces cost and speeds up evaluation runs:
- **Cache Target**: ≥ 70% cache hit rate for prompt prefixes and system instructions.
- **Cost Reduction**: Cuts average per-run cost from ~$0.003 down to ~$0.001 (~66% savings).
- **At Scale**: For 10,000 feature generation runs, caching reduces total LLM spend from $30.00 to $10.00.

---

## 5. Cost Logging Specification

Every LLM call executed by the platform logs structured JSON metrics to `build/llm_cost.jsonl`.

### Log Record Schema (`build/llm_cost.jsonl`)

```json
{
  "timestamp": "2026-09-12T18:00:00Z",
  "provider": "openai",
  "model": "gpt-4o-mini",
  "operation": "generate_gherkin",
  "prompt_tokens": 2045,
  "completion_tokens": 1480,
  "total_tokens": 3525,
  "estimated_cost_usd": 0.00108,
  "cache_hit": false,
  "run_id": "run-xyz-123"
}
```
