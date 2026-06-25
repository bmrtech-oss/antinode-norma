"""
File and directory utilities.
"""

from pathlib import Path
import os


def ensure_directory(path: Path) -> None:
    """Create the directory if it doesn't exist."""
    path.mkdir(parents=True, exist_ok=True)


def write_file(path: Path, content: str) -> None:
    """Write content to a file, creating parent directories if needed."""
    ensure_directory(path.parent)
    path.write_text(content, encoding="utf-8")