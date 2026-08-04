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


def install_bucket_stubs(monkeypatch) -> None:
    install_stubs(monkeypatch)

    def fake_search(query, config, **options) -> object:
        hits = [
            {**HITS[0], "categories": ["Physics"]},
            {**HITS[1], "categories": ["Chemistry"]},
        ]
        return engines.SearchResults(
            hits, {"stub": {"status": "ok", "count": len(hits)}}
        )

    monkeypatch.setattr(engines, "search", fake_search)


_LIBRARY_HITS = [
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
_LIBRARY_CONFIG = {"library_mcp_url": "http://library", "library_mcp_token": "token"}


def _install_library_stubs(monkeypatch, web_hit, library_hits) -> None:
    monkeypatch.setattr(
        engines,
        "search",
        lambda *args, **kwargs: engines.SearchResults(
            [web_hit], {"arxiv": {"status": "ok", "count": 1}}
        ),
    )
    monkeypatch.setattr(engines, "library", lambda *args, **kwargs: library_hits)
    monkeypatch.setattr(rag, "rank", lambda query, hits: list(hits))


def _install_library_only_stubs(monkeypatch, calls, library_hit) -> None:
    def fake_search(query, config, **options) -> object:
        calls.append(options["providers"])
        return engines.SearchResults([], {})

    monkeypatch.setattr(engines, "search", fake_search)
    monkeypatch.setattr(engines, "library", lambda *args, **kwargs: [library_hit])
    monkeypatch.setattr(rag, "rank", lambda query, hits: list(hits))


def _fail_library(*args, **kwargs) -> None:
    raise OSError("library offline")


class ScientificSearchTests(unittest.TestCase):
    def test_scientific_resolves_providers(self) -> None:
        with pytest.MonkeyPatch.context() as monkeypatch:
            calls = []
            library_calls = []
            monkeypatch.setattr(
                engines,
                "search",
                lambda query, config, **options: calls.append(options.get("providers"))
                or engines.SearchResults([], {"arxiv": {"status": "ok", "count": 0}}),
            )
            monkeypatch.setattr(
                engines,
                "library",
                lambda *args, **kwargs: library_calls.append(args) or [],
            )
            config = {"library_mcp_url": "http://library", "library_mcp_token": "token"}
            search_core.quick_web_search("q", config, raw=True, scientific=True)
            search_core.quick_web_search("q", config, raw=True, scientific=True, platform=["arxiv"])
            expected = set(engines.SCIENTIFIC_PLATFORMS)
            assert calls[0] == frozenset(expected)
            assert not set(engines._DIRECT_DEFAULTS) & calls[0]
            assert "searxng" not in calls[0]
            assert calls[1] == frozenset({"arxiv"})
            assert len(library_calls) == 1

    def test_scientific_quick_search_json_carries_buckets_and_existing_fields(self) -> None:
        with pytest.MonkeyPatch.context() as monkeypatch:
            install_bucket_stubs(monkeypatch)
            plain = search_core.quick_web_search("science", {}, raw=True)
            response = search_core.quick_web_search(
                "science", {}, raw=True, scientific=True
            )

            plain_keys = set(plain)
            assert {"results", "providers"} <= plain_keys
            assert plain_keys <= set(response)
            assert response["buckets"]
            assert all(
                {"name", "results"} <= set(bucket)
                and bucket["results"]
                for bucket in response["buckets"]
            )

    def test_scientific_web_search_populates_buckets(self) -> None:
        with pytest.MonkeyPatch.context() as monkeypatch:
            install_bucket_stubs(monkeypatch)
            response = search_core.web_search(
                "science", {}, raw=True, scientific=True
            )

            assert response["buckets"]
            assert all(bucket["results"] for bucket in response["buckets"])

    def test_non_scientific_search_has_no_buckets_key(self) -> None:
        with pytest.MonkeyPatch.context() as monkeypatch:
            install_stubs(monkeypatch)

            response = search_core.quick_web_search("alpha", {}, raw=True)

            assert "buckets" not in response
            assert set(response) == {"query", "results", "corrections", "quality"}

    def test_library_hits_merge_and_outcomes(self) -> None:
        with pytest.MonkeyPatch.context() as monkeypatch:
            web_hit = {**HITS[0], "url": "https://arxiv.org/abs/1234", "engine": "arxiv", "engines": ["arxiv"]}
            library_hits = [dict(item) for item in _LIBRARY_HITS]
            _install_library_stubs(monkeypatch, web_hit, library_hits)
            response = search_core.quick_web_search(
                "research", _LIBRARY_CONFIG, raw=True, scientific=True
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
            monkeypatch.setattr(engines, "library", _fail_library)
            response = search_core.quick_web_search(
                "research", _LIBRARY_CONFIG, raw=True, scientific=True
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
            _install_library_only_stubs(monkeypatch, calls, library_hit)
            response = search_core.quick_web_search(
                "research",
                _LIBRARY_CONFIG,
                raw=True,
                scientific=True,
                platform=["library"],
            )
            assert calls == [frozenset()]
            assert [item["url"] for item in response["results"]] == [
                "library://book?chunk=only"
            ]
            assert response["providers"]["library"] == {"status": "ok", "count": 1}

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


def _provider_failure() -> OSError:
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

    def searcher(query, config, **options) -> list:
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


def test_scientific_buckets_preserve_rank_order_and_uncategorized_last() -> None:
    items = [
        {"title": "first", "categories": ["Physics"]},
        {"title": "second", "categories": ["Chemistry"]},
        {"title": "third", "categories": []},
        {"title": "fourth", "categories": ["Physics"]},
    ]

    buckets = search_core._bucket_results(items)

    assert [bucket["name"] for bucket in buckets] == [
        "Physics",
        "Chemistry",
        "Uncategorized",
    ]
    assert [item["title"] for item in buckets[0]["results"]] == [
        "first",
        "fourth",
    ]
    assert items[0]["bucket"] == "Physics"
    assert items[2]["bucket"] == "Uncategorized"
