"""Run linters on generated code (e.g., ESLint, flake8)."""

import subprocess
from pathlib import Path
from typing import List, Optional


class CodeLinter:
    def __init__(self, tool: Optional[str] = None):
        self.tool = tool

    def lint_files(
            self,
            file_paths: List[Path],
            fix: bool = False,
            verbose: bool = False) -> bool:
        """Run linter on the given files. Returns True if no issues found."""
        if not file_paths:
            return True

        tool = self.tool or self._detect_tool(file_paths[0])
        if not tool:
            return True

        cmd = self._build_command(tool, file_paths, fix)
        if not cmd:
            return True

        if verbose:
            print(f"Running linter: {' '.join(cmd)}")

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            return True
        except subprocess.CalledProcessError as e:
            if verbose:
                print(f"Linter issues found:\n{e.stdout}")
            return False

    def _detect_tool(self, sample_file: Path) -> Optional[str]:
        ext = sample_file.suffix
        if ext in [".js", ".ts", ".tsx", ".jsx"]:
            # ESLint
            try:
                subprocess.run(["eslint", "--version"],
                               check=True, capture_output=True)
                return "eslint"
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass
        elif ext == ".py":
            try:
                subprocess.run(["flake8", "--version"],
                               check=True, capture_output=True)
                return "flake8"
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass
        return None

    def _build_command(
            self,
            tool: str,
            files: List[Path],
            fix: bool) -> List[str]:
        if tool == "eslint":
            cmd = ["eslint"]
            if fix:
                cmd.append("--fix")
            cmd.extend([str(f) for f in files])
            return cmd
        elif tool == "flake8":
            return ["flake8"] + [str(f) for f in files]
        return []
