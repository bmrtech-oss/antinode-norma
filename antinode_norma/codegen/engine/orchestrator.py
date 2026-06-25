"""
Orchestrator that runs the transformation pipeline.
"""

from pathlib import Path
from typing import Optional, List
from ..parsers.gherkin_parser import GherkinParser
from ..emitters.factory import get_emitter
from ..emitters.base import Emitter
from ..models.test_model import TestSuite
from ..config import get_config
from ..post_processors.formatter import CodeFormatter
from ..post_processors.linter import CodeLinter

class Orchestrator:
    def __init__(self, parser: Optional[GherkinParser] = None,
                 emitter: Optional[Emitter] = None):
        self.parser = parser or GherkinParser()
        self.emitter = emitter

    def parse(self, feature_path: Path) -> TestSuite:
        return self.parser.parse(feature_path)

    def emit(self, suite: TestSuite, output_dir: Path, framework: str) -> List[Path]:
        """Emit tests and return list of generated file paths."""
        emitter = self.emitter or get_emitter(framework)
        emitter.emit(suite, output_dir)
        # Gather all generated files (we can simply glob *.spec.ts, etc.)
        generated_files = list(output_dir.glob("*.spec.ts")) + list(output_dir.glob("*.ts"))
        return generated_files

    def generate(self, feature_path: Path, output_dir: Optional[Path] = None,
                 framework: Optional[str] = None) -> None:
        config = get_config()
        fw = framework or config.default_framework
        out_dir = output_dir or config.get_output_dir(fw)

        suite = self.parse(feature_path)
        files = self.emit(suite, out_dir, fw)

        # Post‑processing
        if config.quality.run_formatter:
            formatter = CodeFormatter(tool=config.quality.formatter_tool)
            formatter.format_files(files, verbose=config.verbose)

        if config.quality.run_linter:
            linter = CodeLinter(tool=config.quality.linter_tool)
            linter.lint_files(files, fix=True, verbose=config.verbose)