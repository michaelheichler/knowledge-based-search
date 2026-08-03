"""Shared pacing, caching, and cooldown state for search providers."""

import random
import threading
import time

import engine_state

_PROVIDER_FAILURES = (Exception,)
_MIN_INTERVAL = 3.0
_MAX_JITTER = 2.0
_COOLDOWN_SECONDS = 1800.0
_CACHE_TTL = 600.0
_CACHE_CAP = 128
_pace_lock = threading.Lock()
_query_cache: dict = {}


class ProviderBlocked(RuntimeError):
    """Signal that a provider returned a block page or rate-limit response."""

    def __init__(self, provider, cooldown=None):
        """Store an optional cooldown that overrides the scraper-block default."""
        super().__init__(provider)
        self.cooldown = cooldown


def _reserve_slot(name) -> float:
    """Reserve a provider slot under one lock so parallel rounds do not overlap."""
    with _pace_lock:
        now = time.time()
        interval = _MIN_INTERVAL + random.uniform(0.0, _MAX_JITTER)
        start = engine_state.reserve_slot(name, now, interval)
        return max(0.0, start - now)


def _cached_call(name, query, k, thunk) -> list:
    """Serve fresh repeated queries from cache because bursts trigger provider bans."""
    key = (name, query, k)
    with _pace_lock:
        entry = _query_cache.get(key)
        if entry and time.monotonic() - entry[0] < _CACHE_TTL:
            return [dict(hit) for hit in entry[1]]
    time.sleep(_reserve_slot(name))
    hits = thunk()
    with _pace_lock:
        _query_cache[key] = (time.monotonic(), [dict(hit) for hit in hits])
        while len(_query_cache) > _CACHE_CAP:
            _query_cache.pop(next(iter(_query_cache)))
    return hits


def _task_outcome(name, future) -> tuple[list, dict]:
    """Convert provider failures to safe outcomes and persist block cooldowns."""
    try:
        hits = future.result()
        return hits, {"status": "ok", "count": len(hits)}
    except ProviderBlocked as exc:
        cooldown = getattr(exc, "cooldown", None) or _COOLDOWN_SECONDS
        engine_state.block_provider(name, time.time() + cooldown)
        return [], {"status": "error", "error": type(exc).__name__}
    except _PROVIDER_FAILURES as exc:
        return [], {"status": "error", "error": type(exc).__name__}
