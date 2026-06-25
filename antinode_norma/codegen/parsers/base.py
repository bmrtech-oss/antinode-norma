"""Abstract parser interface."""

from abc import ABC, abstractmethod
from pathlib import Path
from ..models.test_model import TestSuite


class Parser(ABC):
    @abstractmethod
    def parse(self, source: Path) -> TestSuite:
        """Parse a source file into a TestSuite."""
        pass
