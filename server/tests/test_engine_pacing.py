"""Pacing and caching exist because provider bursts end in captcha and IP bans."""

import concurrent.futures
import json
from email.message import Message

import engines
import pytest


def _reset() -> None:
    engines._query_cache.clear()


def test_reserve_slot_spaces_same_provider(monkeypatch) -> None:
    """Back-to-back calls to one provider must be _MIN_INTERVAL apart."""
    monkeypatch.setattr(engines.time, "time", lambda: 100.0)
    monkeypatch.setattr(engines.random, "uniform", lambda *_: 0.0)
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


def test_provider_cooldown_skips_until_expiry(monkeypatch) -> None:
    """A captcha block must survive task rebuilding until its cooldown expires."""
    clock = [100.0]
    monkeypatch.setattr(engines.time, "time", lambda: clock[0])
    future = concurrent.futures.Future()
    future.set_exception(engines.ProviderBlocked("duckduckgo"))
    assert engines._task_outcome("duckduckgo", future)[1]["error"] == "ProviderBlocked"

    config = {"duckduckgo": True, "mwmbl": False, "wikipedia": False}
    outcomes = {}
    assert "duckduckgo" not in engines._build_tasks("q", config, 5, outcomes)
    assert outcomes["duckduckgo"] == {"status": "cooldown"}
    with pytest.raises(engines.AllProvidersFailed):
        engines.search("q", config, k=5)

    clock[0] += engines._COOLDOWN_SECONDS + 1
    assert "duckduckgo" in engines._build_tasks("q", config, 5)


def test_cooldown_does_not_mask_live_provider_failure(monkeypatch) -> None:
    """A cooldown is not a success when every live provider fails."""
    engines.engine_state.block_provider(
        "duckduckgo", engines.time.time() + engines._COOLDOWN_SECONDS
    )

    def fail(*_args, **_kwargs) -> list:
        raise OSError("provider offline")

    monkeypatch.setattr(engines, "mwmbl", fail)
    config = {"duckduckgo": True, "mwmbl": True, "wikipedia": False}

    with pytest.raises(engines.AllProvidersFailed) as failure:
        engines.search("mixed failure", config, k=5)

    assert failure.value.outcomes["duckduckgo"] == {"status": "cooldown"}
    assert failure.value.outcomes["mwmbl"]["status"] == "error"


def test_reserve_slot_jitter_stays_bounded(monkeypatch) -> None:
    """Persisted provider spacing must stay within the configured jitter range."""
    monkeypatch.setattr(engines.time, "time", lambda: 100.0)
    jitter = iter((0.0, 0.0, 2.0, 2.0))
    monkeypatch.setattr(engines.random, "uniform", lambda *_: next(jitter))

    assert engines._reserve_slot("minimum") == 0.0
    assert engines._reserve_slot("minimum") == engines._MIN_INTERVAL
    assert engines._reserve_slot("maximum") == 0.0
    assert engines._reserve_slot("maximum") == engines._MIN_INTERVAL + 2.0


def test_429_maps_to_short_cooldown(monkeypatch) -> None:
    """A rate-limit response clears in minutes, not the scraper-block half hour."""
    import urllib.error

    def raise_429(*_args, **_kwargs) -> str:
        raise urllib.error.HTTPError("http://x", 429, "Too Many Requests", Message(), None)

    monkeypatch.setattr(engines, "_get", raise_429)
    with pytest.raises(engines.ProviderBlocked) as caught:
        engines.semanticscholar("q")
    assert caught.value.cooldown == engines._RATE_LIMIT_COOLDOWN

    clock = [1000.0]
    monkeypatch.setattr(engines.time, "time", lambda: clock[0])
    blocked_until = {}
    monkeypatch.setattr(
        engines.engine_state,
        "block_provider",
        lambda name, until: blocked_until.setdefault(name, until),
    )
    engines._task_outcome("semanticscholar", _future_with_exception(caught.value))
    assert blocked_until["semanticscholar"] == pytest.approx(1000.0 + 120.0)
    assert blocked_until["semanticscholar"] != pytest.approx(1000.0 + engines._COOLDOWN_SECONDS)


def _future_with_exception(exc):
    future = concurrent.futures.Future()
    future.set_exception(exc)
    return future


def test_min_interval_covers_arxiv_guidance() -> None:
    """arXiv asks for a 3s gap between requests; the shared floor must not regress below it."""
    assert engines._MIN_INTERVAL >= 3.0


def test_corrupt_state_file_recovers(monkeypatch, tmp_path) -> None:
    """Corrupt provider state must reset without interrupting a search call."""
    state_path = tmp_path / "engine_state.json"
    state_path.write_text("{broken", encoding="utf-8")
    monkeypatch.setattr(engines.time, "time", lambda: 100.0)
    monkeypatch.setattr(engines.random, "uniform", lambda *_: 0.0)

    assert engines._reserve_slot("duckduckgo") == 0.0
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["providers"]["duckduckgo"]["last_call"] == 100.0


def test_pubmed_efetch_uses_dedicated_pacing_entry(monkeypatch) -> None:
    """The MeSH batch call reserves its own persisted provider slot."""
    responses = [
        json.dumps({"esearchresult": {"idlist": ["111"]}}),
        json.dumps({"result": {"111": {"title": "Title", "pubdate": "2024 Jan 15"}}}),
        "<PubmedArticleSet/>",
    ]
    reserved = []

    def fake_get(*_args, **_kwargs) -> str:
        return responses.pop(0)

    monkeypatch.setattr(engines, "_get", fake_get)
    monkeypatch.setattr(
        engines, "_reserve_slot", lambda name: reserved.append(name) or 0.0
    )

    engines.pubmed("query", k=1)

    assert reserved == [engines.engine_state.PUBMED_EFETCH]
