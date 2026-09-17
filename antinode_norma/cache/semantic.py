import json
import re
import time
from pathlib import Path
from typing import Dict, Any, Optional, Set, Tuple


def _tokenize(text: str) -> Set[str]:
    """Tokenize and normalize text into a set of lower-case alphanumeric words."""
    words = re.findall(r"\w+", text.lower())
    return set(words)


def _jaccard_similarity(set1: Set[str], set2: Set[str]) -> float:
    """Calculate Jaccard similarity index between two token sets."""
    if not set1 and not set2:
        return 1.0
    if not set1 or not set2:
        return 0.0
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / union


class SemanticPromptCache:
    """
    Semantic Prompt Cache.
    Matches incoming prompts against cached prompts using token similarity (Jaccard similarity).
    Supports similarity threshold, TTL expiration, and JSON file persistence.
    """

    def __init__(
        self,
        cache_path: Optional[Path] = None,
        similarity_threshold: float = 0.85,
        ttl_seconds: int = 86400,
    ):
        self.cache_path = cache_path or Path("build/llm_semantic_cache.json")
        self.similarity_threshold = similarity_threshold
        self.ttl_seconds = ttl_seconds
        self._entries: list[Dict[str, Any]] = self._load()

    def _load(self) -> list[Dict[str, Any]]:
        if not self.cache_path.exists():
            return []
        try:
            with open(self.cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save(self) -> None:
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(self._entries, f, indent=2)
        except Exception:
            pass

    def get(self, prompt: str) -> Optional[Tuple[str, float]]:
        """
        Search for semantically similar cached prompt.

        Returns:
            Tuple of (cached_response, similarity_score) if match >= similarity_threshold and not expired.
            None otherwise.
        """
        prompt_tokens = _tokenize(prompt)
        now = time.time()
        best_match: Optional[Dict[str, Any]] = None
        best_score = 0.0

        valid_entries = []
        for entry in self._entries:
            timestamp = entry.get("timestamp", 0)
            if now - timestamp > self.ttl_seconds:
                continue

            valid_entries.append(entry)
            cached_tokens = set(entry.get("tokens", []))
            score = _jaccard_similarity(prompt_tokens, cached_tokens)

            if score >= self.similarity_threshold and score > best_score:
                best_score = score
                best_match = entry

        if len(valid_entries) != len(self._entries):
            self._entries = valid_entries
            self._save()

        if best_match:
            return best_match.get("response", ""), best_score

        return None

    def set(self, prompt: str, response: str) -> None:
        """
        Store prompt, tokenized words, response, and timestamp in cache.
        """
        tokens = list(_tokenize(prompt))
        self._entries.append(
            {
                "prompt": prompt,
                "tokens": tokens,
                "response": response,
                "timestamp": time.time(),
            }
        )
        self._save()

    def clear(self) -> None:
        """
        Clear all semantic cache entries.
        """
        self._entries = []
        if self.cache_path.exists():
            try:
                self.cache_path.unlink()
            except Exception:
                pass
