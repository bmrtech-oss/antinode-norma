import hashlib
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional


class ExactPromptCache:
    """
    Exact Prompt Cache.
    Stores LLM prompt responses keyed by SHA-256 hash of the exact prompt string.
    Supports TTL expiration and JSON file persistence.
    """

    def __init__(
        self,
        cache_path: Optional[Path] = None,
        ttl_seconds: int = 86400,
    ):
        self.cache_path = cache_path or Path("build/llm_cache.json")
        self.ttl_seconds = ttl_seconds
        self._data: Dict[str, Dict[str, Any]] = self._load()

    def _hash_prompt(self, prompt: str) -> str:
        return hashlib.sha256(prompt.encode("utf-8")).hexdigest()

    def _load(self) -> Dict[str, Dict[str, Any]]:
        if not self.cache_path.exists():
            return {}
        try:
            with open(self.cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save(self) -> None:
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)
        except Exception:
            pass

    def get(self, prompt: str) -> Optional[str]:
        """
        Get cached response for exact prompt if key exists and is not expired.
        """
        key = self._hash_prompt(prompt)
        entry = self._data.get(key)
        if not entry:
            return None

        timestamp = entry.get("timestamp", 0)
        now = time.time()
        if now - timestamp > self.ttl_seconds:
            # Expired
            del self._data[key]
            self._save()
            return None

        return entry.get("response")

    def set(self, prompt: str, response: str) -> None:
        """
        Cache response for prompt with current timestamp.
        """
        key = self._hash_prompt(prompt)
        self._data[key] = {
            "response": response,
            "timestamp": time.time(),
        }
        self._save()

    def clear(self) -> None:
        """
        Clear all cached entries.
        """
        self._data = {}
        if self.cache_path.exists():
            try:
                self.cache_path.unlink()
            except Exception:
                pass
