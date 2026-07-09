import importlib
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "server"))

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


def install_stubs(monkeypatch):
    def fake_search(query, config, k, cap):
        return [dict(hit) for hit in HITS[:k]]

    def fake_rank(query, docs):
        return list(docs)

    def fake_fetch_clean(url, max_chars):
        return PAGES[url]

    monkeypatch.setattr(engines, "search", fake_search)
    monkeypatch.setattr(rag, "rank", fake_rank)
    monkeypatch.setattr(search_core, "fetch_clean", fake_fetch_clean)
    monkeypatch.setenv("KBS_STATE_FILE", str(Path(tempfile.mkdtemp()) / "state.json"))
    search_core.RESULT_URLS.clear()


def test_quick_web_search_pins_current_shape(monkeypatch):
    install_stubs(monkeypatch)

    assert search_core.quick_web_search("alpha", {}, num_results=2) == {
        "results": [
            {
                "title": "Alpha guide",
                "url": "https://example.com/alpha",
                "snippet": "Alpha snippet",
                "engine": "searxng",
                "date": "2026-01-02",
                "relevance": 0.8,
            },
            {
                "title": "Beta report",
                "url": "https://example.com/beta",
                "snippet": "Beta snippet",
                "engine": "duckduckgo",
                "date": "2026-01-03",
                "relevance": 0.6,
            },
        ]
    }


def test_web_search_stores_result_id_for_get_content(monkeypatch):
    install_stubs(monkeypatch)

    response = search_core.web_search("alpha", {}, num_results=1)

    assert response == {
        "summary": "Alpha page content with enough words for summary.",
        "citations": [
            {
                "title": "Alpha guide",
                "url": "https://example.com/alpha",
                "snippet": "Alpha snippet",
                "source": "searxng",
                "date": "2026-01-02",
                "relevance": 0.8,
            }
        ],
        "result_ids": ["r1"],
    }
    assert search_core.get_content("r1") == {
        "source_url": "https://example.com/alpha",
        "page_content": "Alpha page content with enough words for summary.",
    }


def test_get_content_accepts_raw_url(monkeypatch):
    install_stubs(monkeypatch)

    assert search_core.get_content("https://example.com/raw") == {
        "source_url": "https://example.com/raw",
        "page_content": "Raw URL page content.",
    }


def test_deep_research_pins_current_shape(monkeypatch):
    install_stubs(monkeypatch)

    assert search_core.deep_research("alpha", {}, max_rounds=1) == {
        "summary": (
            "Alpha page content with enough words for summary. "
            "Beta page content with more source words."
        ),
        "sections": [
            {
                "heading": "alpha",
                "content": (
                    "Alpha page content with enough words for summary. "
                    "Beta page content with more source words."
                ),
                "sources": [
                    {
                        "title": "Alpha guide",
                        "url": "https://example.com/alpha",
                        "snippet": "Alpha snippet",
                        "source": "searxng",
                        "date": "2026-01-02",
                        "relevance": 0.8,
                    },
                    {
                        "title": "Beta report",
                        "url": "https://example.com/beta",
                        "snippet": "Beta snippet",
                        "source": "duckduckgo",
                        "date": "2026-01-03",
                        "relevance": 0.6,
                    },
                ],
            }
        ],
        "citations": [
            {
                "title": "Alpha guide",
                "url": "https://example.com/alpha",
                "snippet": "Alpha snippet",
                "source": "searxng",
                "date": "2026-01-02",
                "relevance": 0.8,
            },
            {
                "title": "Beta report",
                "url": "https://example.com/beta",
                "snippet": "Beta snippet",
                "source": "duckduckgo",
                "date": "2026-01-03",
                "relevance": 0.6,
            },
        ],
    }


def test_deep_context_aware_search_suppresses_seen_urls(monkeypatch):
    install_stubs(monkeypatch)

    first = search_core.deep_context_aware_search(
        "alpha", {}, context="same session", fetch_top_k=0
    )
    second = search_core.deep_context_aware_search(
        "alpha", {}, context="same session", fetch_top_k=0
    )

    assert first == {
        "query": "alpha",
        "context": "same session",
        "results": [
            {
                "title": "Alpha guide",
                "url": "https://example.com/alpha",
                "snippet": "Alpha snippet",
                "engines": ["searxng"],
                "relevance": 0.8,
                "date": "2026-01-02",
            },
            {
                "title": "Beta report",
                "url": "https://example.com/beta",
                "snippet": "Beta snippet",
                "engines": ["duckduckgo"],
                "relevance": 0.6,
                "date": "2026-01-03",
            },
        ],
        "already_seen_suppressed": 0,
        "summary": "",
        "citations": [],
        "result_ids": [],
    }
    assert second["already_seen_suppressed"] == 2
    assert second["results"] == []


def test_deep_research_falls_back_to_citation_snippets_when_summary_empty():
    citation = {
        "title": "Alpha guide",
        "url": "https://example.com/alpha",
        "snippet": "Citation snippet text",
        "source": "searxng",
        "date": "2026-01-02",
        "relevance": 0.8,
    }

    def search(query):
        return {"summary": "", "citations": [citation]}

    result = search_core._deep_research("alpha", 1, search)

    assert result["summary"] == "Citation snippet text"


def test_deep_research_keeps_empty_summary_when_no_citations():
    def search(query):
        return {"summary": "", "citations": []}

    result = search_core._deep_research("alpha", 1, search)

    assert result["summary"] == ""


def _patch_deep_search_backends(monkeypatch, web_response, quick_results):
    monkeypatch.setattr(search_core, "web_search", lambda query, config: web_response)
    monkeypatch.setattr(
        search_core,
        "quick_web_search",
        lambda query, config, num_results=8: {"results": quick_results},
    )


def test_deep_search_falls_back_to_quick_snippets(monkeypatch):
    quick_results = [
        {
            "title": "Alpha guide",
            "url": "https://example.com/alpha",
            "snippet": "Alpha snippet one.",
            "engine": "searxng",
            "date": "2026-01-02",
            "relevance": 0.8,
        },
        {
            "title": "Beta report",
            "url": "https://example.com/beta",
            "snippet": "Beta snippet two.",
            "engine": "duckduckgo",
            "date": "2026-01-03",
            "relevance": 0.6,
        },
    ]
    _patch_deep_search_backends(
        monkeypatch,
        web_response={"summary": "", "citations": [], "result_ids": []},
        quick_results=quick_results,
    )

    response = search_core._deep_search("alpha", {})

    assert response == {
        "summary": "Alpha snippet one. Beta snippet two.",
        "citations": [
            {
                "title": "Alpha guide",
                "url": "https://example.com/alpha",
                "snippet": "Alpha snippet one.",
                "source": "searxng",
                "date": "2026-01-02",
                "relevance": 0.8,
            },
            {
                "title": "Beta report",
                "url": "https://example.com/beta",
                "snippet": "Beta snippet two.",
                "source": "duckduckgo",
                "date": "2026-01-03",
                "relevance": 0.6,
            },
        ],
        "result_ids": [],
    }


def test_deep_search_preserves_response_when_citations_present(monkeypatch):
    called_quick = []
    response = {
        "summary": "fetched summary",
        "citations": [
            {
                "title": "Alpha",
                "url": "https://example.com/alpha",
                "snippet": "s",
                "source": "searxng",
                "date": "",
                "relevance": 0.5,
            }
        ],
        "result_ids": ["r1"],
    }
    monkeypatch.setattr(search_core, "web_search", lambda query, config: response)
    monkeypatch.setattr(
        search_core,
        "quick_web_search",
        lambda query, config, num_results=8: (
            called_quick.append(query) or {"results": []}
        ),
    )

    assert search_core._deep_search("alpha", {}) == response
    assert called_quick == []


def test_deep_search_preserves_empty_when_quick_also_empty(monkeypatch):
    empty = {"summary": "", "citations": [], "result_ids": []}
    _patch_deep_search_backends(monkeypatch, web_response=empty, quick_results=[])

    assert search_core._deep_search("alpha", {}) == empty


def test_deep_research_falls_back_when_first_engine_call_empty(monkeypatch):
    install_stubs(monkeypatch)
    calls = {"n": 0}

    def flaky_search(query, config, k, cap):
        calls["n"] += 1
        if calls["n"] == 1:
            return []
        return [dict(hit) for hit in HITS[:k]]

    monkeypatch.setattr(engines, "search", flaky_search)

    result = search_core.deep_research("alpha", {}, max_rounds=1)

    assert result["summary"] == "Alpha snippet Beta snippet"
    assert result["citations"] == [
        {
            "title": "Alpha guide",
            "url": "https://example.com/alpha",
            "snippet": "Alpha snippet",
            "source": "searxng",
            "date": "2026-01-02",
            "relevance": 0.8,
        },
        {
            "title": "Beta report",
            "url": "https://example.com/beta",
            "snippet": "Beta snippet",
            "source": "duckduckgo",
            "date": "2026-01-03",
            "relevance": 0.6,
        },
    ]
    assert result["sections"][0]["sources"] == result["citations"]
    assert calls["n"] >= 2
