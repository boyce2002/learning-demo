from __future__ import annotations

from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from fastapi import Request

from .config import Settings


def is_trusted_write(request: Request, settings: Settings) -> bool:
    if request.headers.get("sec-fetch-site", "").lower() == "cross-site":
        return False
    origin = request.headers.get("origin")
    if not origin:
        return True
    forwarded_proto = request.headers.get("x-forwarded-proto", request.url.scheme)
    forwarded_host = request.headers.get("x-forwarded-host", request.headers.get("host", ""))
    request_origin = f"{forwarded_proto}://{forwarded_host}".rstrip("/")
    allowed = {item.rstrip("/") for item in settings.allowed_origins}
    allowed.add(request_origin)
    return origin.rstrip("/") in allowed


class InMemoryRateLimiter:
    """Small single-instance guard for the public demo's write endpoints."""

    def __init__(self) -> None:
        self._events: dict[tuple[str, str], deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, visitor_id: str, action: str, limit: int, window_seconds: int) -> bool:
        now = monotonic()
        cutoff = now - window_seconds
        key = (visitor_id, action)
        with self._lock:
            events = self._events[key]
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= limit:
                return False
            events.append(now)
            return True
