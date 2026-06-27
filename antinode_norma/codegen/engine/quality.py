"""Quality configuration and helper functions."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class QualityConfig:
    """Settings for improving test code quality."""

    use_page_objects: bool = False
    generate_step_defs: bool = False
    selector_strategy: str = "data-testid"  # "data-testid", "id", "css", "auto"
    add_explicit_waits: bool = True
    enable_scenario_outlines: bool = True
    run_formatter: bool = True
    formatter_tool: Optional[str] = None  # if None, auto‑detect
    run_linter: bool = False
    linter_tool: Optional[str] = None
    page_object_dir: str = "pages"
    step_def_dir: str = "steps"
    output_templates: bool = False  # use Jinja templates if True
    use_llm_mapping: bool = True
    llm_mapping_cache_size: int = 1000
    llm_mapping_timeout: int = 5
    enable_self_healing: bool = False
    enable_visual_testing: bool = False
    enable_failure_learning: bool = True
    failure_learning_max_examples: int = 2
    visual_snapshot_dir: str = "visual-snapshots"
    selector_healing_cache_size: int = 1000
    # Additional options
    wait_timeout: int = 10000  # milliseconds
    retry_count: int = 2

    def __post_init__(self):
        if self.formatter_tool is None:
            # auto‑detect based on framework
            self.formatter_tool = "prettier"  # default; can be overridden

        if isinstance(self.use_llm_mapping, str):
            self.use_llm_mapping = self.use_llm_mapping.strip().lower() in {
                "true",
                "1",
                "yes",
                "on",
            }

        if isinstance(self.enable_self_healing, str):
            self.enable_self_healing = self.enable_self_healing.strip().lower() in {
                "true",
                "1",
                "yes",
                "on",
            }

        if isinstance(self.enable_visual_testing, str):
            self.enable_visual_testing = self.enable_visual_testing.strip().lower() in {
                "true",
                "1",
                "yes",
                "on",
            }

        if isinstance(self.enable_failure_learning, str):
            self.enable_failure_learning = self.enable_failure_learning.strip().lower() in {
                "true",
                "1",
                "yes",
                "on",
            }

        if isinstance(self.failure_learning_max_examples, str):
            try:
                self.failure_learning_max_examples = int(
                    self.failure_learning_max_examples)
            except ValueError:
                self.failure_learning_max_examples = 2

        if isinstance(self.visual_snapshot_dir, str):
            self.visual_snapshot_dir = self.visual_snapshot_dir.strip() or "visual-snapshots"
            self.visual_snapshot_dir = self.visual_snapshot_dir.replace(
                "\\", "/")

        if isinstance(self.llm_mapping_cache_size, str):
            try:
                self.llm_mapping_cache_size = int(self.llm_mapping_cache_size)
            except ValueError:
                self.llm_mapping_cache_size = 1000

        if isinstance(self.selector_healing_cache_size, str):
            try:
                self.selector_healing_cache_size = int(
                    self.selector_healing_cache_size)
            except ValueError:
                self.selector_healing_cache_size = 1000

        if isinstance(self.llm_mapping_timeout, str):
            try:
                self.llm_mapping_timeout = int(self.llm_mapping_timeout)
            except ValueError:
                self.llm_mapping_timeout = 5

        if self.llm_mapping_cache_size < 1:
            self.llm_mapping_cache_size = 1000

        if self.selector_healing_cache_size < 1:
            self.selector_healing_cache_size = 1000

        if self.llm_mapping_timeout < 1:
            self.llm_mapping_timeout = 5
