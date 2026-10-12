import time
from collections import defaultdict, deque

from app.exceptions.app_exception import AppException


class RateLimiter:
    def __init__(self, max_attempts: int, window_seconds: int):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._hits: dict[str, deque] = defaultdict(deque)

    def check(self, key: str) -> None:
        """Record an attempt; raise if there have been too many."""
        now = time.monotonic()
        hits = self._hits[key]

        while hits and now - hits[0] > self.window_seconds:
            hits.popleft()

        if len(hits) >= self.max_attempts:
            raise AppException(
                "Too many attempts. Please try again later.",
                status_code=429,
            )

        hits.append(now)

    def reset(self, key: str) -> None:
        self._hits.pop(key, None)


login_limiter = RateLimiter(max_attempts=5, window_seconds=15 * 60)