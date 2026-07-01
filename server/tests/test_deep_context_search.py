import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import engines
import mcp_server
import rag


def _make_hit(title, url, snippet="s", engine="searxng", rank=1, date=""):
    return {
        "title": title,
        "url": url,
        "snippet": snippet,
        "engine": engine,
        "engines": [engine],
        "rank": rank,
        "date": date,
    }


@pytest.fixture(autouse=True)
def reset_memory():
    mcp_server.CONTEXT_MEMORY.clear()
    mcp_server.RESULT_URLS.clear()
    yield
    mcp_server.CONTEXT_MEMORY.clear()
    mcp_server.RESULT_URLS.clear()


@pytest.fixture
def base_hits():
    return [
        _make_hit("Alpha", "https://alpha.example/a", "Alpha intro", date="2024-01-15"),
        _make_hit(
            "Beta",
            "https://beta.example/b",
            "Beta overview",
            engine="duckduckgo",
            rank=2,
        ),
    ]


def test_results_carry_required_labels(monkeypatch, base_hits):
    monkeypatch.setattr(engines, "search", lambda q, cfg, k, cap: base_hits)
    monkeypatch.setattr(rag, "rank", lambda q, docs: list(docs))
    response = mcp_server.deep_context_aware_search("alpha", fetch_top_k=0)
    assert response["query"] == "alpha" and response["context"] == ""
    for result in response["results"]:
        assert "relevance" in result and "date" in result
        assert "engines" in result and isinstance(result["engines"], list)
        assert "title" in result and "url" in result and "snippet" in result


def test_fetch_top_k_zero_no_summary_no_citations_no_fetch(monkeypatch, base_hits):
    fetch_calls = []
    monkeypatch.setattr(engines, "search", lambda q, cfg, k, cap: base_hits)
    monkeypatch.setattr(rag, "rank", lambda q, docs: list(docs))
    monkeypatch.setattr(
        mcp_server, "fetch_clean", lambda url, n: fetch_calls.append(url) or ""
    )
    response = mcp_server.deep_context_aware_search("alpha", fetch_top_k=0)
    assert (
        response["summary"] == "" and response["citations"] == [] and fetch_calls == []
    )


def test_fetch_top_k_positive_gives_summary_and_citations(monkeypatch, base_hits):
    monkeypatch.setattr(engines, "search", lambda q, cfg, k, cap: base_hits)
    monkeypatch.setattr(rag, "rank", lambda q, docs: list(docs))
    monkeypatch.setattr(mcp_server, "fetch_clean", lambda url, n: "word " * 200)
    response = mcp_server.deep_context_aware_search("alpha", fetch_top_k=2)
    assert response["summary"] != "" and len(response["citations"]) > 0


def test_memory_suppresses_seen_urls_on_second_call(monkeypatch, base_hits):
    monkeypatch.setattr(engines, "search", lambda q, cfg, k, cap: list(base_hits))
    monkeypatch.setattr(rag, "rank", lambda q, docs: list(docs))
    first = mcp_server.deep_context_aware_search("alpha", context="ctx", fetch_top_k=0)
    second = mcp_server.deep_context_aware_search("alpha", context="ctx", fetch_top_k=0)
    first_urls = {r["url"] for r in first["results"]}
    second_urls = {r["url"] for r in second["results"]}
    assert second["already_seen_suppressed"] > 0
    assert not (first_urls & second_urls)


def test_memory_does_not_repeat_issued_reformulations(monkeypatch, base_hits):
    search_queries = []

    def recording_search(q, cfg, k, cap):
        search_queries.append(q)
        return list(base_hits)

    monkeypatch.setattr(engines, "search", recording_search)
    monkeypatch.setattr(rag, "rank", lambda q, docs: list(docs))
    mcp_server.deep_context_aware_search(
        "climate data", context="ctx", max_rounds=3, fetch_top_k=0
    )
    queries_first = list(search_queries)
    search_queries.clear()
    mcp_server.deep_context_aware_search(
        "climate data", context="ctx", max_rounds=3, fetch_top_k=0
    )
    for q in search_queries:
        if q != "climate data":
            assert q not in queries_first


def test_context_appended_to_rank_query(monkeypatch, base_hits):
    captured = []

    def capturing_rank(q, docs):
        captured.append(q)
        return list(docs)

    monkeypatch.setattr(engines, "search", lambda q, cfg, k, cap: list(base_hits))
    monkeypatch.setattr(rag, "rank", capturing_rank)
    mcp_server.deep_context_aware_search(
        "alpha query", context="important context text", fetch_top_k=0
    )
    assert any("important context text" in q for q in captured)


def test_already_seen_suppressed_zero_on_first_call(monkeypatch, base_hits):
    monkeypatch.setattr(engines, "search", lambda q, cfg, k, cap: list(base_hits))
    monkeypatch.setattr(rag, "rank", lambda q, docs: list(docs))
    response = mcp_server.deep_context_aware_search("alpha", fetch_top_k=0)
    assert response["already_seen_suppressed"] == 0


def test_results_capped_at_60(monkeypatch):
    many = [_make_hit(f"H{i}", f"https://h{i}.example/", rank=i) for i in range(80)]
    monkeypatch.setattr(engines, "search", lambda q, cfg, k, cap: many)
    monkeypatch.setattr(rag, "rank", lambda q, docs: list(docs))
    assert (
        len(mcp_server.deep_context_aware_search("alpha", fetch_top_k=0)["results"])
        <= 60
    )


def test_return_shape_keys(monkeypatch, base_hits):
    monkeypatch.setattr(engines, "search", lambda q, cfg, k, cap: list(base_hits))
    monkeypatch.setattr(rag, "rank", lambda q, docs: list(docs))
    r = mcp_server.deep_context_aware_search("alpha", fetch_top_k=0)
    assert set(r) == {
        "query",
        "context",
        "results",
        "already_seen_suppressed",
        "summary",
        "citations",
        "result_ids",
    }
