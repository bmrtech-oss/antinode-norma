# LLM Cost Model & Cost Gate — Antinode Norma

This document specifies the LLM token usage baseline, cost model, caching ROI, and automated cost gate enforced during evaluation.

---

## 1. Token & Cost Baseline

| Operations Item | Average Prompt / Tokens | Estimated Model | Cost Per Operation |
|---|---|---|---|
| **Generation Prompt** | 2,000 input / 1,500 output | `gpt-4o-mini` | ~$0.0015 / attempt |
| **Judge Prompt** | 3,000 input / 500 output | `gpt-4o-mini` | ~$0.0012 / judge |
| **Full Single Run** | 2 attempts + Q10 Judge | `gpt-4o-mini` | ~$0.003 / run |
| **Cache Hit Run** | 100% Exact/Semantic Cache Hit | N/A (Cached) | ~$0.000 / run |
| **Avg Cost (70% Cache)** | Weighted Average | `gpt-4o-mini` | ~$0.001 / run |

---

## 2. Cost Tracker & Logging

- Every LLM completion call records prompt tokens, completion tokens, model name, and calculated USD cost to `build/llm_cost.jsonl`.
- `CostTracker` (`antinode_norma/evaluate/cost.py`) aggregates run costs across evaluation batches.

---

## 3. Cost Gate SLA Threshold

- **Cost Gate**: Evaluation cycles fail if `cost_per_run > $0.02`.
- Any prompt update or feature pipeline change that exceeds $0.02 per run requires explicit architectural prompt review.
