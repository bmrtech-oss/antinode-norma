"""Generate Page Object classes from the test suite."""
from pathlib import Path
from .base import Emitter
from ..models.test_model import TestSuite

class PageObjectEmitter(Emitter):
    def emit(self, suite: TestSuite, output_dir: Path) -> None:
        # TODO: Generate page object files
        pass
