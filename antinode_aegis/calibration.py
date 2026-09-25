"""Deterministic calibration dataset and reliability metrics."""

from __future__ import annotations

from pathlib import Path
from typing import List

import json
from pydantic import BaseModel


class CalibrationExample(BaseModel):
    id: str
    predicted_probability: float
    observed_success: bool


class CalibrationDataset(BaseModel):
    version: str
    examples: List[CalibrationExample]

    @classmethod
    def from_json(cls, path: Path) -> "CalibrationDataset":
        return cls.model_validate(json.loads(path.read_text(encoding="utf-8")))


def calibration_metrics(dataset: CalibrationDataset, bins: int = 10) -> dict[str, float]:
    if not dataset.examples:
        return {"ece": 0.0, "mce": 0.0, "brier": 0.0}

    buckets: list[list[CalibrationExample]] = [[] for _ in range(bins)]
    for example in dataset.examples:
        probability = min(1.0, max(0.0, example.predicted_probability))
        index = min(bins - 1, int(probability * bins))
        buckets[index].append(example)

    ece = 0.0
    mce = 0.0
    total = len(dataset.examples)
    for bucket in buckets:
        if not bucket:
            continue
        confidence = sum(item.predicted_probability for item in bucket) / len(bucket)
        accuracy = sum(item.observed_success for item in bucket) / len(bucket)
        gap = abs(confidence - accuracy)
        ece += len(bucket) / total * gap
        mce = max(mce, gap)

    brier = sum(
        (item.predicted_probability - int(item.observed_success)) ** 2
        for item in dataset.examples
    ) / total
    return {"ece": round(ece, 6), "mce": round(mce, 6), "brier": round(brier, 6)}
