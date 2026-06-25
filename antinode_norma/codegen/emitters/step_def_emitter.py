"""Generate reusable step definition functions."""

from pathlib import Path
from .base import Emitter
from ..models.test_model import TestSuite


class StepDefEmitter(Emitter):
    def emit(self, suite: TestSuite, output_dir: Path) -> None:
        # TODO: Generate step definition files
        pass
