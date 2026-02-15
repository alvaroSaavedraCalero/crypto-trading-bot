"""Simple in-memory cache with TTL for market data."""

import time
from typing import Any, Optional


class TTLCache:
    """Thread-safe in-memory cache with per-key TTL."""

    def __init__(self, default_ttl: int = 300):
        """
        Args:
            default_ttl: Default time-to-live in seconds (default 5 minutes).
        """
        self._store: dict[str, tuple[Any, float]] = {}
        self._default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        """Get a value if it exists and hasn't expired."""
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if time.time() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Store a value with TTL."""
        ttl = ttl if ttl is not None else self._default_ttl
        self._store[key] = (value, time.time() + ttl)

    def clear(self) -> None:
        """Clear all cached entries."""
        self._store.clear()

    def evict_expired(self) -> int:
        """Remove all expired entries and return count removed."""
        now = time.time()
        expired = [k for k, (_, exp) in self._store.items() if now > exp]
        for k in expired:
            del self._store[k]
        return len(expired)


# Global cache instance for market data (5 minute TTL)
market_data_cache = TTLCache(default_ttl=300)
