"""Small shared helpers: errors, time, rate limit, tracked background tasks."""
import asyncio
import logging
import time
from collections import defaultdict, deque
from datetime import datetime, timezone

from fastapi import Request

log = logging.getLogger("scamshield")


class ApiErr(Exception):
    def __init__(self, status: int, code: str, message: str):
        self.status, self.code, self.message = status, code, message


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def iso(dt: datetime) -> str:
    return dt.isoformat() + "Z"


_hits: dict[str, deque] = defaultdict(deque)


async def rate_limit(request: Request) -> None:
    """Per-IP limit: 30 requests / minute on the endpoints that use it."""
    ip = request.client.host if request.client else "?"
    now = time.monotonic()
    q = _hits[ip]
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= 30:
        raise ApiErr(429, "rate_limited", "Too many requests. Please wait a minute.")
    q.append(now)


_tasks: set[asyncio.Task] = set()


def spawn(coro) -> asyncio.Task:
    t = asyncio.create_task(coro)
    _tasks.add(t)
    t.add_done_callback(_tasks.discard)
    return t


async def cancel_all_tasks() -> None:
    for t in list(_tasks):
        t.cancel()
    await asyncio.gather(*_tasks, return_exceptions=True)
