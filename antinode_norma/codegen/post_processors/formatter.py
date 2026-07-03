"""Apply code formatting (e.g., Prettier, Ruff) to generated files."""

import subprocess
from pathlib import Path
from typing import List, Optional


class CodeFormatter:
    def __init__(self, tool: Optional[str] = None):
        self.tool = tool

    def format_files(self, file_paths: List[Path], verbose: bool = False) -> bool:
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
        except FileNotFoundError as e:
            if verbose:
                print(f"Formatter not found: {e}")
            return False

    def _detect_tool(self, sample_file: Path) -> Optional[str]:
        """Detect which formatter to use based on file extension."""
        ext = sample_file.suffix
        if ext in [".js", ".ts", ".tsx", ".jsx"]:
            # Check if prettier is available
            try:
                subprocess.run(
                    ["prettier", "--version"], check=True, capture_output=True
                )
                return "prettier"
            except (subprocess.CalledProcessError, FileNotFoundError):
                # fallback to local node_modules binary (works in CI after `npm ci`)
                local_prettier = Path("node_modules") / ".bin" / "prettier"
                if local_prettier.exists():
                    return str(local_prettier)
                # as a last resort, try `npx prettier`
                try:
                    subprocess.run(["npx", "prettier", "--version"], check=True, capture_output=True)
                    return "npx prettier"
                except (subprocess.CalledProcessError, FileNotFoundError):
                    return None
        elif ext == ".py":
            try:
                subprocess.run(["ruff", "--version"], check=True, capture_output=True)
                return "ruff"
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass
        return None

    def _build_command(
        self, tool: str, files: List[Path], check: bool = False
    ) -> List[str]:
        """Build the command line for the formatter."""
        if tool.endswith("prettier") or tool == "prettier":
            # tool may be a path to the prettier binary (node_modules/.bin/prettier)
            exe = tool if tool != "prettier" and " " not in tool else "prettier"
            if tool == "prettier":
                exe = "prettier"
            cmd = [exe, "--write"]
            if check:
                cmd = [exe, "--check"]
            cmd.extend([str(f) for f in files])
            return cmd
        if tool == "npx prettier":
            cmd = ["npx", "prettier", "--write"]
            if check:
                cmd = ["npx", "prettier", "--check"]
            cmd.extend([str(f) for f in files])
            return cmd
        elif tool == "ruff":
            cmd = ["ruff", "format"]
            if check:
                cmd = ["ruff", "check"]
            cmd.extend([str(f) for f in files])
            return cmd
        return []
