#!/usr/bin/env python3
"""
Standalone test for OpenRouter integration using Norma's LLM factory.
"""

import os
import sys
from dotenv import load_dotenv
from antinode_norma.utils.llm_factory import create_llm_callable

load_dotenv()

def test_openrouter():
    config = {
        "provider": "openrouter",
        "api_key": os.getenv("OPENROUTER_API_KEY"),
        "model": os.getenv("LLM_MODEL", "openai/gpt-oss-120b:free"),
        "base_url": os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1"),
        "temperature": float(os.getenv("LLM_TEMPERATURE", "0.2")),
        "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "1024")),
        "extra_body": {"provider": {"require_parameters": True}}
    }
    
    try:
        llm = create_llm_callable(config)
        response = llm("What is the capital of France?")
        print("=== OpenRouter Test ===")
        print(f"Response: {response}")
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    test_openrouter()