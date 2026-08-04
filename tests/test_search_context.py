import importlib
import tempfile
from pathlib import Path

import pytest

engines = importlib.import_module("engines")
rag = importlib.import_module("rag")
search_context = importlib.import_module("search_context")
search_core = importlib.import_module("search_core")


HITS = [
    {
        "title": "Alpha guide",
        "url": "https://example.com/alpha",
        "snippet": "Alpha snippet",
        "engine": "searxng",
        "engines": ["searxng"],
        "date": "2026-01-02",
        "relevance": 0.8,
    },
    {
        "title": "Beta report",
        "url": "https://example.com/beta",
        "snippet": "Beta snippet",
        "engine": "duckduckgo",
        "engines": ["duckduckgo"],
        "date": "2026-01-03",
        "relevance": 0.6,
    },
]

PAGES = {
    "https://example.com/alpha": "Alpha page content with enough words for summary.",
    "https://example.com/beta": "Beta page content with more source words.",
}


def install_stubs(monkeypatch) -> object:
    def fake_search(query, config, **options) -> object:
        return [dict(hit) for hit in HITS[: options["k"]]]

    def fake_rank(query, docs) -> object:
        return list(docs)

    def fake_fetch_clean(url, max_chars) -> object:
        return PAGES[url]

    monkeypatch.setattr(engines, "search", fake_search)
    monkeypatch.setattr(rag, "rank", fake_rank)
    monkeypatch.setattr(search_core, "fetch_clean", fake_fetch_clean)
    monkeypatch.setenv("KBS_STATE_FILE", str(Path(tempfile.mkdtemp()) / "state.json"))
    search_core.RESULT_URLS.clear()


def _provider_failure() -> OSError:
    outcomes = {"duckduckgo": {"status": "error", "error": "OSError"}}
    return engines.AllProvidersFailed(outcomes)


def test_deep_context_aware_search_suppresses_seen_urls(monkeypatch) -> object:
    install_stubs(monkeypatch)

    options = {"context": "same session", "fetch_top_k": 0}
    first = search_context.deep_context_aware_search("alpha", {}, **options)
    second = search_context.deep_context_aware_search("alpha", {}, **options)

    assert first["query"] == "alpha"
    assert first["context"] == "same session"
    assert [item["title"] for item in first["results"]] == [
        "Alpha guide",
        "Beta report",
    ]
    assert all(item["confidence"] == "unknown" for item in first["results"])
    assert all("engines" in item for item in first["results"])
    assert first["already_seen_suppressed"] == 0
    assert first["corrections"] == []
    assert second["already_seen_suppressed"] == 2
    assert second["results"] == []


def test_result_helpers_preserve_optional_citation_count() -> None:
    hit = {
        "title": "Paper",
        "url": "https://arxiv.org/abs/1",
        "snippet": "Abstract",
        "engine": "arxiv",
        "date": "2026-01-02",
        "relevance": 0.8,
        "citation_count": 42,
    }
    without_count = {key: value for key, value in hit.items() if key != "citation_count"}

    for helper in (search_core._brief_result, search_core._citation, search_context._label):
        assert helper(hit)["citation_count"] == 42
        assert "citation_count" not in helper(without_count)


def test_context_keeps_hits_after_later_failure(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("KBS_STATE_FILE", str(tmp_path / "state.json"))
    monkeypatch.setattr(rag, "rank", lambda query, rows: rows)
    first = engines.SearchResults(
        [dict(HITS[0])], {"duckduckgo": {"status": "ok", "count": 1}}
    )
    calls = []

    def search(query, config, **options) -> object:
        calls.append(query)
        if len(calls) > 1:
            raise _provider_failure()
        return first

    monkeypatch.setattr(engines, "search", search)
    result = search_context.deep_context_aware_search(
        "alpha", {}, max_rounds=2, fetch_top_k=0, raw=True
    )

    assert result["results"][0]["title"] == "Alpha guide"
    assert result["providers"]["duckduckgo"]["status"] == "error"


def test_context_empty_success_survives_failure(monkeypatch, tmp_path) -> None:
    """An honest empty provider response prevents a total-failure verdict."""
    monkeypatch.setenv("KBS_STATE_FILE", str(tmp_path / "state.json"))
    calls = []

    def search(query, config, **options) -> object:
        calls.append(query)
        if len(calls) > 1:
            raise _provider_failure()
        outcomes = {"duckduckgo": {"status": "ok", "count": 0}}
        return engines.SearchResults([], outcomes)

    monkeypatch.setattr(engines, "search", search)

    result = search_context.deep_context_aware_search(
        "alpha", {}, max_rounds=2, fetch_top_k=0, raw=True
    )

    assert result["results"] == []


def test_context_raises_when_every_provider_round_fails(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("KBS_STATE_FILE", str(tmp_path / "state.json"))

    def fail_search(*args, **kwargs) -> None:
        raise _provider_failure()

    monkeypatch.setattr(engines, "search", fail_search)
    with pytest.raises(engines.AllProvidersFailed):
        search_context.deep_context_aware_search(
            "alpha", {}, max_rounds=1, fetch_top_k=0, raw=True
        )
