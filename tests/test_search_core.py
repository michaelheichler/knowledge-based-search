import importlib
import tempfile
import unittest
from pathlib import Path

import pytest

engines = importlib.import_module("engines")
search_core = importlib.import_module("search_core")
rag = importlib.import_module("rag")


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
    "https://example.com/raw": "Raw URL page content.",
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


class ScientificSearchTests(unittest.TestCase):
    def test_scientific_resolves_providers(self) -> None:
        with pytest.MonkeyPatch.context() as monkeypatch:
            calls = []
            library_calls = []

            def fake_search(query, config, **options) -> object:
                calls.append(options.get("providers"))
                return engines.SearchResults([], {"arxiv": {"status": "ok", "count": 0}})

            monkeypatch.setattr(engines, "search", fake_search)

            def fake_library(*args, **kwargs):
                library_calls.append(args)
                return []

            monkeypatch.setattr(engines, "library", fake_library)

            config = {"library_mcp_url": "http://library", "library_mcp_token": "token"}
            search_core.quick_web_search("q", config, raw=True, scientific=True)
            search_core.quick_web_search(
                "q", config, raw=True, scientific=True, platform=["arxiv"]
            )

            expected = set(engines._DIRECT_DEFAULTS) | {"searxng"} | set(
                engines.SCIENTIFIC_PLATFORMS
            )
            assert calls[0] == frozenset(expected)
            assert calls[1] == frozenset({"arxiv"})
            assert len(library_calls) == 1

    def test_library_hits_merge_and_outcomes(self) -> None:
        with pytest.MonkeyPatch.context() as monkeypatch:
            web_hit = {
                **HITS[0],
                "url": "https://arxiv.org/abs/1234",
                "engine": "arxiv",
                "engines": ["arxiv"],
            }
            library_hits = [
                {
                    "title": "Library passage one",
                    "url": "library://book?chunk=one",
                    "snippet": "Library evidence one",
                    "engine": "library",
                    "rank": 1,
                    "date": "",
                },
                {
                    "title": "Library passage two",
                    "url": "library://book?chunk=two",
                    "snippet": "Library evidence two",
                    "engine": "library",
                    "rank": 2,
                    "date": "",
                },
            ]
            monkeypatch.setattr(
                engines,
                "search",
                lambda *args, **kwargs: engines.SearchResults(
                    [web_hit], {"arxiv": {"status": "ok", "count": 1}}
                ),
            )
            monkeypatch.setattr(engines, "library", lambda *args, **kwargs: library_hits)
            monkeypatch.setattr(rag, "rank", lambda query, hits: list(hits))

            response = search_core.quick_web_search(
                "research",
                {
                    "library_mcp_url": "http://library",
                    "library_mcp_token": "token",
                },
                raw=True,
                scientific=True,
            )

            urls = {item["url"] for item in response["results"]}
            assert urls == {
                "https://arxiv.org/abs/1234",
                "library://book?chunk=one",
                "library://book?chunk=two",
            }
            assert response["providers"]["library"] == {"status": "ok", "count": 2}
            assert all(
                item["confidence"] == "primary"
                for item in response["results"]
                if item["url"].startswith("library://")
            )

    def test_library_error_is_structured_outcome(self) -> None:
        with pytest.MonkeyPatch.context() as monkeypatch:
            web_hit = engines.SearchResults(
                [dict(HITS[0])], {"duckduckgo": {"status": "ok", "count": 1}}
            )
            monkeypatch.setattr(engines, "search", lambda *args, **kwargs: web_hit)

            def fail_library(*args, **kwargs):
                raise OSError("library offline")

            monkeypatch.setattr(engines, "library", fail_library)

            response = search_core.quick_web_search(
                "research",
                {
                    "library_mcp_url": "http://library",
                    "library_mcp_token": "token",
                },
                raw=True,
                scientific=True,
            )

            assert response["results"]
            assert response["providers"]["library"] == {
                "status": "error",
                "error": "OSError",
            }

    def test_platform_library_only(self) -> None:
        with pytest.MonkeyPatch.context() as monkeypatch:
            calls = []
            library_hit = {
                "title": "Library passage",
                "url": "library://book?chunk=only",
                "snippet": "Evidence",
                "engine": "library",
                "rank": 1,
                "date": "",
            }

            def fake_search(query, config, **options) -> object:
                calls.append(options["providers"])
                return engines.SearchResults([], {})

            monkeypatch.setattr(engines, "search", fake_search)
            monkeypatch.setattr(engines, "library", lambda *args, **kwargs: [library_hit])
            monkeypatch.setattr(rag, "rank", lambda query, hits: list(hits))

            response = search_core.quick_web_search(
                "research",
                {
                    "library_mcp_url": "http://library",
                    "library_mcp_token": "token",
                },
                raw=True,
                scientific=True,
                platform=["library"],
            )

            assert calls == [frozenset()]
            assert [item["url"] for item in response["results"]] == [
                "library://book?chunk=only"
            ]
            assert response["providers"]["library"] == {"status": "ok", "count": 1}

    def test_result_helpers_preserve_optional_citation_count(self) -> None:
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

        for helper in (
            search_core._brief_result,
            search_core._citation,
            search_core._label,
        ):
            assert helper(hit)["citation_count"] == 42
            assert "citation_count" not in helper(without_count)


def test_quick_web_search_pins_current_shape(monkeypatch) -> object:
    install_stubs(monkeypatch)

    response = search_core.quick_web_search("alpha", {}, num_results=2)

    assert set(response) == {"query", "results", "corrections", "quality"}
    assert response["query"] == "alpha"
    assert response["corrections"] == []
    assert [item["title"] for item in response["results"]] == [
        "Alpha guide",
        "Beta report",
    ]
    assert all(item["confidence"] == "unknown" for item in response["results"])
    _assert_provenance(response["results"])
    assert response["quality"]["verification"] == "single-source"


def test_web_search_stores_result_id_for_get_content(monkeypatch) -> object:
    install_stubs(monkeypatch)

    response = search_core.web_search("alpha", {}, num_results=1)

    assert response["query"] == "alpha"
    assert response["summary"] == "Alpha page content with enough words for summary."
    assert response["result_ids"] == ["r1"]
    assert response["corrections"] == []
    assert response["citations"][0]["title"] == "Alpha guide"
    assert response["citations"][0]["confidence"] == "unknown"
    _assert_provenance(response["citations"])
    assert response["quality"]["verification"] == "single-source"
    assert search_core.get_content("r1") == {
        "source_url": "https://example.com/alpha",
        "page_content": "Alpha page content with enough words for summary.",
    }


def test_get_content_accepts_raw_url(monkeypatch) -> object:
    install_stubs(monkeypatch)

    assert search_core.get_content("https://example.com/raw") == {
        "source_url": "https://example.com/raw",
        "page_content": "Raw URL page content.",
    }



@pytest.mark.parametrize(
    "ref", ["file:///tmp/x", "ftp://example.com/x", "HTTP://example.com/x"]
)
def test_get_content_routes_all_url_schemes_to_validation(monkeypatch, ref) -> None:
    """Scheme-shaped input must reach fetch policy instead of reference lookup."""
    seen = []

    def blocked(url, max_chars) -> None:
        seen.append(url)
        raise ValueError("blocked-fetch")

    monkeypatch.setattr(search_core, "fetch_clean", blocked)

    with pytest.raises(ValueError, match="blocked-fetch"):
        search_core.get_content(ref)
    assert seen == [ref]


def test_deep_research_pins_current_shape(monkeypatch) -> object:
    install_stubs(monkeypatch)

    response = search_core.deep_research("alpha", {}, max_rounds=1)

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


def test_deep_context_aware_search_suppresses_seen_urls(monkeypatch) -> object:
    install_stubs(monkeypatch)

    options = {"context": "same session", "fetch_top_k": 0}
    first = search_core.deep_context_aware_search("alpha", {}, **options)
    second = search_core.deep_context_aware_search("alpha", {}, **options)

    assert first["query"] == "alpha"
    assert first["context"] == "same session"
    assert [item["title"] for item in first["results"]] == [
        "Alpha guide",
        "Beta report",
    ]
    assert all(item["confidence"] == "unknown" for item in first["results"])
    _assert_provenance(first["results"])
    assert first["already_seen_suppressed"] == 0
    assert first["corrections"] == []
    assert second["already_seen_suppressed"] == 2
    assert second["results"] == []


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

    result = search_core._deep_research("alpha", 1, search)

    assert result["summary"] == "Citation snippet text"


def test_deep_research_keeps_empty_summary_when_no_citations() -> object:
    def search(query) -> object:
        return {"summary": "", "citations": []}

    result = search_core._deep_research("alpha", 1, search)

    assert result["summary"] == ""


def _patch_deep_search_backends(monkeypatch, web_response, quick_results) -> object:
    monkeypatch.setattr(search_core, "web_search", lambda query, config: web_response)
    monkeypatch.setattr(
        search_core,
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

    response = search_core._deep_search("alpha", {})

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
    monkeypatch.setattr(search_core, "web_search", lambda query, config: response)
    monkeypatch.setattr(
        search_core,
        "quick_web_search",
        lambda query, config, num_results=8: called_quick.append(query),
    )

    assert search_core._deep_search("alpha", {}) == response
    assert called_quick == []


def test_deep_search_preserves_empty_when_quick_also_empty(monkeypatch) -> object:
    empty = {"summary": "", "citations": [], "result_ids": []}
    _patch_deep_search_backends(monkeypatch, web_response=empty, quick_results=[])

    assert search_core._deep_search("alpha", {}) == empty


def test_deep_research_falls_back_when_first_engine_call_empty(monkeypatch) -> object:
    install_stubs(monkeypatch)
    calls = {"n": 0}

    def flaky_search(query, config, **options) -> object:
        calls["n"] += 1
        return [] if calls["n"] == 1 else [dict(hit) for hit in HITS[: options["k"]]]

    monkeypatch.setattr(engines, "search", flaky_search)

    result = search_core.deep_research("alpha", {}, max_rounds=1)

    assert result["summary"] == "Alpha snippet Beta snippet"
    assert [item["title"] for item in result["citations"]] == [
        "Alpha guide",
        "Beta report",
    ]
    assert all(item["confidence"] == "unknown" for item in result["citations"])
    assert result["sections"][0]["sources"] == result["citations"]
    assert calls["n"] >= 2


def _provider_failure() -> engines.AllProvidersFailed:
    outcomes = {"duckduckgo": {"status": "error", "error": "OSError"}}
    return engines.AllProvidersFailed(outcomes)


def test_refinement_failure_keeps_hits_from_same_round(monkeypatch) -> None:
    initial = engines.SearchResults(
        [dict(HITS[0])], {"duckduckgo": {"status": "ok", "count": 1}}
    )
    state = search_core._RefinementState("alpha", "alpha", initial, set(), [])
    request = search_core._SearchRequest("alpha", {}, 5, 5, True)

    def fail(query, config, **options) -> None:
        raise _provider_failure()

    monkeypatch.setattr(engines, "search", fail)
    search_core._apply_refinement(state, request, ("candidate", {"kind": "retry"}))

    assert state.hits[0]["title"] == "Alpha guide"
    assert state.hits.outcomes["duckduckgo"]["status"] == "error"


def test_refinement_stops_after_failed_correction(monkeypatch) -> None:
    """One failed correction ends the budget so a second cannot misreport all-failed."""
    calls = []

    def searcher(query, config, **options) -> engines.SearchResults:
        calls.append(query)
        if len(calls) == 1:
            return engines.SearchResults(
                [], {"duckduckgo": {"status": "ok", "count": 0}}
            )
        raise _provider_failure()

    monkeypatch.setattr(engines, "search", searcher)
    result = search_core.quick_web_search('"John Smith"', {})

    assert len(calls) == 2
    assert result["results"] == []


def test_refinement_failure_keeps_prior_empty_success(monkeypatch) -> None:
    outcomes = {"duckduckgo": {"status": "ok", "count": 0}}
    initial = engines.SearchResults([], outcomes)
    state = search_core._RefinementState("alpha", "alpha", initial, set(), [])
    request = search_core._SearchRequest("alpha", {}, 5, 5, True)

    def fail(*args, **kwargs) -> None:
        raise _provider_failure()

    monkeypatch.setattr(engines, "search", fail)

    search_core._apply_refinement(state, request, ("candidate", {"kind": "retry"}))

    assert state.current == "alpha"


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

    monkeypatch.setattr(search_core, "_call_web_search", web_round)
    result = search_core.deep_research("alpha", {}, max_rounds=2)

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
        [empty, search_core._failed_deep_response("beta", _provider_failure())]
    )

    result = search_core._deep_research("alpha", 2, lambda query: next(responses))

    assert result["summary"] == ""
    assert result["citations"] == []


def test_deep_raises_when_every_provider_round_fails(monkeypatch) -> None:
    def fail(query, config, raw) -> None:
        raise _provider_failure()

    monkeypatch.setattr(search_core, "_call_web_search", fail)
    with pytest.raises(engines.AllProvidersFailed):
        search_core.deep_research("alpha", {}, max_rounds=2)


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
    result = search_core.deep_context_aware_search(
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

    result = search_core.deep_context_aware_search(
        "alpha", {}, max_rounds=2, fetch_top_k=0, raw=True
    )

    assert result["results"] == []


def test_context_raises_when_every_provider_round_fails(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("KBS_STATE_FILE", str(tmp_path / "state.json"))

    def fail_search(*args, **kwargs) -> None:
        raise _provider_failure()

    monkeypatch.setattr(engines, "search", fail_search)
    with pytest.raises(engines.AllProvidersFailed):
        search_core.deep_context_aware_search(
            "alpha", {}, max_rounds=1, fetch_top_k=0, raw=True
        )
