"""
Abstract emitter interface.

All framework emitters must inherit from this base class and implement
the `emit()` method.
"""

from abc import ABC, abstractmethod
from pathlib import Path

from ..models.test_model import TestSuite


class Emitter(ABC):
    """
    Abstract base class for all framework emitters.

    An emitter takes a TestSuite (intermediate representation) and
    generates framework-specific test code files.
    """

    @abstractmethod
    def emit(self, suite: TestSuite, output_dir: Path) -> None:
        """
        Generate framework-specific test files.

        Args:
            suite: The TestSuite (IR) to generate tests from.
            output_dir: The directory where files should be written.
        """

    def _ensure_output_dir(self, output_dir: Path) -> None:
        """Ensure the output directory exists."""
        output_dir.mkdir(parents=True, exist_ok=True)

    def _write_file(self, path: Path, content: str) -> None:
        """Write content to a file, creating parent directories if needed."""
        self._ensure_output_dir(path.parent)
        path.write_text(content, encoding="utf-8")
