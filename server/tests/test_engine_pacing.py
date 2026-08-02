"""Pacing and caching exist because provider bursts end in captcha and IP bans."""

import engines


def _reset() -> None:
    engines._last_slot.clear()
    engines._query_cache.clear()


def test_reserve_slot_spaces_same_provider(monkeypatch) -> None:
    """Back-to-back calls to one provider must be _MIN_INTERVAL apart."""
    _reset()
    monkeypatch.setattr(engines.time, "monotonic", lambda: 100.0)
    assert engines._reserve_slot("duckduckgo") == 0.0
    assert engines._reserve_slot("duckduckgo") == engines._MIN_INTERVAL
    assert engines._reserve_slot("mojeek") == 0.0


def test_cached_call_skips_second_fetch(monkeypatch) -> None:
    """An identical query within the TTL must not hit the provider again."""
    _reset()
    monkeypatch.setattr(engines.time, "sleep", lambda _: None)
    calls = []

    def thunk() -> list:
        calls.append(1)
        return [{"url": "https://x.com"}]

    first = engines._cached_call("duckduckgo", "q", 5, thunk)
    second = engines._cached_call("duckduckgo", "q", 5, thunk)
    assert first == second
    assert len(calls) == 1
    second[0]["url"] = "mutated"
    assert (
        engines._cached_call("duckduckgo", "q", 5, thunk)[0]["url"] == "https://x.com"
    )


def test_cached_call_expires_and_caps(monkeypatch) -> None:
    """Stale entries refetch and the cache cannot grow without bound."""
    _reset()
    monkeypatch.setattr(engines.time, "sleep", lambda _: None)
    clock = [0.0]
    monkeypatch.setattr(engines.time, "monotonic", lambda: clock[0])
    calls = []

    def thunk() -> list:
        calls.append(1)
        return []

    engines._cached_call("duckduckgo", "q", 5, thunk)
    clock[0] = engines._CACHE_TTL + 1
    engines._cached_call("duckduckgo", "q", 5, thunk)
    assert len(calls) == 2
    for i in range(engines._CACHE_CAP + 10):
        engines._cached_call("duckduckgo", f"q{i}", 5, thunk)
    assert len(engines._query_cache) <= engines._CACHE_CAP
