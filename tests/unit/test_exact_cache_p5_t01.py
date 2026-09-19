import time
from antinode_norma.cache.exact import ExactPromptCache


def test_exact_cache_hit_and_miss(tmp_path):
    cache_file = tmp_path / "cache.json"
    cache = ExactPromptCache(cache_path=cache_file, ttl_seconds=3600)

    prompt = "Generate a feature for password reset"
    response = "Feature: Password reset\n  Scenario: Reset link"

    # Initial miss
    assert cache.get(prompt) is None

    # Set response
    cache.set(prompt, response)

    # Hit
    assert cache.get(prompt) == response

    # Miss on different prompt
    assert cache.get("Different prompt") is None


def test_exact_cache_persistence(tmp_path):
    cache_file = tmp_path / "cache.json"
    cache1 = ExactPromptCache(cache_path=cache_file, ttl_seconds=3600)

    prompt = "Persistent prompt"
    response = "Feature: Persistent"

    cache1.set(prompt, response)

    # Re-instantiate from file
    cache2 = ExactPromptCache(cache_path=cache_file, ttl_seconds=3600)
    assert cache2.get(prompt) == response


def test_exact_cache_ttl_expiry(tmp_path):
    cache_file = tmp_path / "cache.json"
    # TTL of 1 second
    cache = ExactPromptCache(cache_path=cache_file, ttl_seconds=1)

    prompt = "Expiring prompt"
    response = "Feature: Expiring"

    cache.set(prompt, response)
    assert cache.get(prompt) == response

    # Wait for TTL to expire
    time.sleep(1.1)

    assert cache.get(prompt) is None
