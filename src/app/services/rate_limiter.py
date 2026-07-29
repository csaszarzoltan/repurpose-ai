"""Token-bucket rate limiter with per-platform isolation."""
from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock


class RateLimiter:
    """Token-bucket rate limiter with per-platform isolation.

    Tracks call timestamps per platform and prunes expired windows on access.
    Thread-safe via a single Lock.
    """

    def __init__(self, max_calls: int = 100, period: float = 60.0) -> None:
        self._max_calls = max_calls
        self._period = period
        self._buckets: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, platform: str) -> bool:
        """Check if a call is allowed without consuming a token."""
        with self._lock:
            bucket = self._buckets[platform]
            now = time.time()
            while bucket and now - bucket[0] > self._period:
                bucket.popleft()
            return len(bucket) < self._max_calls

    def consume(self, platform: str) -> bool:
        """Try to consume a token. Returns True if within limit."""
        with self._lock:
            bucket = self._buckets[platform]
            now = time.time()
            while bucket and now - bucket[0] > self._period:
                bucket.popleft()
            if len(bucket) < self._max_calls:
                bucket.append(now)
                return True
            return False
