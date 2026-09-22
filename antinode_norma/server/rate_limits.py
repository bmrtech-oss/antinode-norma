"""Small process-local sliding-window limiters for the local API service."""

import os
import threading
import time
from collections import defaultdict, deque

_lock = threading.Lock()
_events: dict[tuple[str, str], deque[float]] = defaultdict(deque)


def _int_setting(name: str, default: int) -> int:
    try:
        return max(0, int(os.getenv(name, str(default))))
    except (TypeError, ValueError):
        return default


def allow(scope: str, user_key: str, limit_env: str, default_limit: int,
          window_env: str = "NORMA_RATE_LIMIT_WINDOW_SECONDS",
          default_window: int = 60) -> bool:
    """Consume one request if under the configured per-user sliding-window limit.

    A limit of zero disables the limiter, which is useful for local development.
    """
    limit = _int_setting(limit_env, default_limit)
    if limit == 0:
        return True
    window = max(1, _int_setting(window_env, default_window))
    now = time.monotonic()
    key = (scope, user_key)
    with _lock:
        timestamps = _events[key]
        while timestamps and timestamps[0] <= now - window:
            timestamps.popleft()
        if len(timestamps) >= limit:
            return False
        timestamps.append(now)
        return True


def user_key(user) -> str:
    return f"{user.tenant_id or 'default'}:{user.id}"
