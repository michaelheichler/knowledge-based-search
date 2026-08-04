import importlib
import tempfile
from pathlib import Path

import pytest

engines = importlib.import_module("engines")
rag = importlib.import_module("rag")
search_core = importlib.import_module("search_core")
search_deep = importlib.import_module("search_deep")


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


def _assert_provenance(items) -> None:
    assert all("engines" in item for item in items)
    assert all("engine" not in item and "source" not in item for item in items)


def test_deep_research_pins_current_shape(monkeypatch) -> object:
    install_stubs(monkeypatch)

    response = search_deep.deep_research("alpha", {}, max_rounds=1)

    assert set(response) == {
        "query",
        "summary",
        "sections",
        "citations",
        "corrections",
        "quality",
    }
    assert response["summary"] == (
        "Alpha page content with enough words for summary. "
        "Beta page content with more source words."
    )
    assert response["sections"][0]["heading"] == "alpha"
    assert response["sections"][0]["sources"] == response["citations"]
    assert [item["title"] for item in response["citations"]] == [
        "Alpha guide",
        "Beta report",
    ]
    _assert_provenance(response["citations"])


def test_deep_research_falls_back_to_citation_snippets_when_summary_empty() -> object:
    citation = {
        "title": "Alpha guide",
        "url": "https://example.com/alpha",
        "snippet": "Citation snippet text",
        "source": "searxng",
        "date": "2026-01-02",
        "relevance": 0.8,
    }

    def search(query) -> object:
        return {"summary": "", "citations": [citation]}

    result = search_deep._deep_research("alpha", 1, search)

    assert result["summary"] == "Citation snippet text"


def test_deep_research_keeps_empty_summary_when_no_citations() -> object:
    def search(query) -> object:
        return {"summary": "", "citations": []}

    result = search_deep._deep_research("alpha", 1, search)

    assert result["summary"] == ""


def _patch_deep_search_backends(monkeypatch, web_response, quick_results) -> object:
    monkeypatch.setattr(search_deep, "web_search", lambda query, config: web_response)
    monkeypatch.setattr(
        search_deep,
        "quick_web_search",
        lambda query, config, num_results=8, **options: {"results": quick_results},
    )


def test_deep_search_falls_back_to_quick_snippets(monkeypatch) -> object:
    quick_results = [
        {**HITS[0], "snippet": "Alpha snippet one."},
        {**HITS[1], "snippet": "Beta snippet two."},
    ]
    _patch_deep_search_backends(
        monkeypatch,
        web_response={"summary": "", "citations": [], "result_ids": []},
        quick_results=quick_results,
    )

    response = search_deep._deep_search("alpha", {})

    assert response["summary"] == "Alpha snippet one. Beta snippet two."
    assert [item["title"] for item in response["citations"]] == [
        "Alpha guide",
        "Beta report",
    ]
    assert all(item["confidence"] == "unknown" for item in response["citations"])
    assert response["result_ids"] == []


def test_deep_search_preserves_response_when_citations_present(monkeypatch) -> object:
    called_quick = []
    response = {
        "summary": "fetched summary",
        "citations": [{"url": "https://example.com/alpha"}],
        "result_ids": ["r1"],
    }
    monkeypatch.setattr(search_deep, "web_search", lambda query, config: response)
    monkeypatch.setattr(
        search_deep,
        "quick_web_search",
        lambda query, config, num_results=8: called_quick.append(query),
    )

    assert search_deep._deep_search("alpha", {}) == response
    assert called_quick == []


def test_deep_search_preserves_empty_when_quick_also_empty(monkeypatch) -> object:
    empty = {"summary": "", "citations": [], "result_ids": []}
    _patch_deep_search_backends(monkeypatch, web_response=empty, quick_results=[])

    assert search_deep._deep_search("alpha", {}) == empty


def test_deep_research_falls_back_when_first_engine_call_empty(monkeypatch) -> object:
    install_stubs(monkeypatch)
    calls = {"n": 0}

    def flaky_search(query, config, **options) -> object:
        calls["n"] += 1
        return [] if calls["n"] == 1 else [dict(hit) for hit in HITS[: options["k"]]]

    monkeypatch.setattr(engines, "search", flaky_search)

    result = search_deep.deep_research("alpha", {}, max_rounds=1)

    assert result["summary"] == "Alpha snippet Beta snippet"
    assert [item["title"] for item in result["citations"]] == [
        "Alpha guide",
        "Beta report",
    ]
    assert all(item["confidence"] == "unknown" for item in result["citations"])
    assert result["sections"][0]["sources"] == result["citations"]
    assert calls["n"] >= 2


def _provider_failure() -> OSError:
    outcomes = {"duckduckgo": {"status": "error", "error": "OSError"}}
    return engines.AllProvidersFailed(outcomes)


def test_deep_keeps_earlier_round_when_later_provider_round_fails(monkeypatch) -> None:
    calls = []

    def web_round(query, config, raw) -> dict:
        calls.append(query)
        if len(calls) > 1:
            raise _provider_failure()
        return {
            "query": query,
            "summary": "first round evidence",
            "citations": [],
            "corrections": [],
            "providers": {"duckduckgo": {"status": "ok", "count": 1}},
        }

    monkeypatch.setattr(search_deep, "_call_web_search", web_round)
    result = search_deep.deep_research("alpha", {}, max_rounds=2)

    assert result["summary"] == "first round evidence"
    assert result["providers"]["duckduckgo"]["status"] == "error"


def test_deep_valid_empty_round_survives_later_failure() -> None:
    """A provider can succeed honestly without returning evidence."""
    empty = {
        "query": "alpha",
        "summary": "",
        "citations": [],
        "corrections": [],
        "providers": {"duckduckgo": {"status": "ok", "count": 0}},
    }
    responses = iter(
        [empty, search_deep._failed_deep_response("beta", _provider_failure())]
    )

    result = search_deep._deep_research("alpha", 2, lambda query: next(responses))

    assert result["summary"] == ""
    assert result["citations"] == []


def test_deep_raises_when_every_provider_round_fails(monkeypatch) -> None:
    def fail(query, config, raw) -> None:
        raise _provider_failure()

    monkeypatch.setattr(search_deep, "_call_web_search", fail)
    with pytest.raises(engines.AllProvidersFailed):
        search_deep.deep_research("alpha", {}, max_rounds=2)
