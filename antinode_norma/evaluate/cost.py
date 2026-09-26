import json
import time
import uuid
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# Token pricing for gpt-4o-mini per 1M tokens ($)
INPUT_PRICE_PER_1M = 0.15
OUTPUT_PRICE_PER_1M = 0.60


class CostTracker:
    """
    LLM Cost Tracker.
    Calculates prompt/completion costs, logs usage to build/llm_cost.jsonl,
    and enforces cost gates ($0.02 per run threshold).
    """

    def __init__(
        self,
        log_path: Optional[Path] = None,
        model: str = "gpt-4o-mini",
        database_url: Optional[str] = None,
    ):
        self.log_path = log_path or Path("build/llm_cost.jsonl")
        self.model = model
        self.database_url = database_url or os.getenv("DATABASE_URL")

    @staticmethod
    def calculate_cost(input_tokens: int, output_tokens: int) -> float:
        """Calculate LLM call cost in USD."""
        input_cost = (input_tokens / 1_000_000) * INPUT_PRICE_PER_1M
        output_cost = (output_tokens / 1_000_000) * OUTPUT_PRICE_PER_1M
        return input_cost + output_cost

    def log_call(
        self,
        prompt: str,
        completion: str,
        input_tokens: int,
        output_tokens: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> float:
        """Log an LLM call to the JSONL log file and return calculated cost."""
        cost = self.calculate_cost(input_tokens, output_tokens)
        record = {
            "id": str(uuid.uuid4()),
            "timestamp": time.time(),
            "model": self.model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": cost,
            "prompt_length": len(prompt),
            "completion_length": len(completion),
            "metadata": metadata or {},
        }

        if self.database_url:
            from antinode_norma.database import save_cost_event

            save_cost_event(self.database_url, record)
            return cost

        try:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception:
            pass

        return cost

    def get_total_cost(self) -> float:
        """Calculate total USD cost recorded in the log file."""
        if self.database_url:
            from antinode_norma.database import total_cost

            return total_cost(self.database_url)
        if not self.log_path.exists():
            return 0.0

        total = 0.0
        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        total += data.get("cost_usd", 0.0)
        except Exception:
            pass

        return total

    def check_cost_gate(self, cost_per_run: float, threshold: float = 0.02) -> Tuple[bool, str]:
        """Verify cost_per_run against cost gate threshold ($0.02)."""
        if cost_per_run <= threshold:
            return True, f"Cost ${cost_per_run:.5f} is within limit (${threshold:.2f})."
        return False, f"Cost ${cost_per_run:.5f} exceeds maximum threshold of ${threshold:.2f}."
