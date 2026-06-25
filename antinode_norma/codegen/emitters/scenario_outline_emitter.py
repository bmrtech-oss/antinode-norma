"""Specialised emitter for Scenario Outline data‑driven tests."""
from pathlib import Path
from .base import Emitter
from ..models.test_model import TestSuite

class ScenarioOutlineEmitter(Emitter):
    def emit(self, suite: TestSuite, output_dir: Path) -> None:
        # TODO: Generate parameterised test code
        pass
