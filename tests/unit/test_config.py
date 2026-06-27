"""Unit tests for configuration loading."""

import os
from dotenv import load_dotenv


def test_env_loading():
    """Test that .env file is loaded (if present)."""
    load_dotenv()
    # This just checks that the function runs; the actual variables depend on
    # .env
    _ = os.getenv("LLM_PROVIDER")
    # If the .env file is present, it might be set; but we don't force it.
    assert True  # no assertion, just ensure no exception
