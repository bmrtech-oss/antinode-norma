"""Apply code formatting (e.g., Prettier, Black) to generated files."""

import subprocess
from pathlib import Path
from typing import List, Optional


class CodeFormatter:
    def __init__(self, tool: Optional[str] = None):
        self.tool = tool

    def format_files(
            self,
            file_paths: List[Path],
            verbose: bool = False) -> bool:
        """Run the formatter on the given files. Returns True on success."""
        if not file_paths:
            return True

        # Detect the tool if not set
        tool = self.tool or self._detect_tool(file_paths[0])
        if not tool:
            return True  # no tool found, skip

        cmd = self._build_command(tool, file_paths)
        if not cmd:
            return True

        if verbose:
            print(f"Running formatter: {' '.join(cmd)}")

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            return True
        except subprocess.CalledProcessError as e:
            if verbose:
                print(f"Formatter error: {e.stderr}")
            return False

    def _detect_tool(self, sample_file: Path) -> Optional[str]:
        """Detect which formatter to use based on file extension."""
        ext = sample_file.suffix
        if ext in [".js", ".ts", ".tsx", ".jsx"]:
            # Check if prettier is available
            try:
                subprocess.run(["prettier", "--version"],
                               check=True, capture_output=True)
                return "prettier"
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass
        elif ext == ".py":
            try:
                subprocess.run(["black", "--version"],
                               check=True, capture_output=True)
                return "black"
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass
        return None

    def _build_command(self, tool: str, files: List[Path]) -> List[str]:
        """Build the command line for the formatter."""
        if tool == "prettier":
            return ["prettier", "--write"] + [str(f) for f in files]
        elif tool == "black":
            return ["black"] + [str(f) for f in files]
        return []
