"""
Logging setup and helpers.
"""

import logging
import sys


def setup_logging(level=logging.INFO, format_string=None):
    """Configure logging with a standard format."""
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        level=level,
        format=format_string,
        stream=sys.stdout
    )
    return logging.getLogger("antinode_norma.codegen")