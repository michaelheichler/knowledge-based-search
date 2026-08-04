import engines
import pytest
import rag
import search_context
import search_core
import state


def _make_hit(title, url, **options) -> object:
    engine = options.get("engine", "searxng")
    return {
        "title": title,
        "url": url,
        "snippet": options.get("snippet", "s"),
        "engine": engine,
        "engines": [engine],
        "rank": options.get("rank", 1),
        "date": options.get("date", ""),
    }


@pytest.fixture(autouse=True)
def reset_memory(monkeypatch, tmp_path) -> object:
    monkeypatch.setenv("KBS_STATE_FILE", str(tmp_path / "state.json"))
    state.clear_session()
    search_core.RESULT_URLS.clear()
    yield
    state.clear_session()
    search_core.RESULT_URLS.clear()


@pytest.fixture
def base_hits() -> object:
    return [
        _make_hit(
            "Alpha",
            "https://alpha.example/a",
            snippet="Alpha intro",
            date="2024-01-15",
        ),
        _make_hit(
            "Beta",
            "https://beta.example/b",
            snippet="Beta overview",
            engine="duckduckgo",
            rank=2,
        ),
    ]


def test_results_carry_required_labels(monkeypatch, base_hits) -> object:
    monkeypatch.setattr(engines, "search", lambda q, cfg, k, cap: base_hits)
    monkeypatch.setattr(rag, "rank", lambda q, docs: list(docs))
    response = search_context.deep_context_aware_search("alpha", {}, fetch_top_k=0)
    assert response["query"] == "alpha" and response["context"] == ""
    for result in response["results"]:
        assert "relevance" in result and "date" in result
        assert "engines" in result and isinstance(result["engines"], list)
        assert "engine" not in result and "source" not in result
        assert "title" in result and "url" in result and "snippet" in result


def test_fetch_zero_skips_details(monkeypatch, base_hits) -> None:
    fetch_calls = []
    monkeypatch.setattr(engines, "search", lambda q, cfg, k, cap: base_hits)
    monkeypatch.setattr(rag, "rank", lambda q, docs: list(docs))
    monkeypatch.setattr(
        search_core, "fetch_clean", lambda url, n: fetch_calls.append(url) or ""
    )
    response = search_context.deep_context_aware_search("alpha", {}, fetch_top_k=0)
    assert (
        response["summary"] == "" and response["citations"] == [] and fetch_calls == []
    )


def test_fetch_positive_returns_details(monkeypatch, base_hits) -> None:
    monkeypatch.setattr(engines, "search", lambda q, cfg, k, cap: base_hits)
    monkeypatch.setattr(rag, "rank", lambda q, docs: list(docs))
    monkeypatch.setattr(search_core, "fetch_clean", lambda url, n: "word " * 200)
    response = search_context.deep_context_aware_search("alpha", {}, fetch_top_k=2)
    assert response["summary"] != "" and len(response["citations"]) > 0
    assert all("engines" in citation for citation in response["citations"])
    assert all(
        "engine" not in item and "source" not in item for item in response["citations"]
    )


def test_memory_suppresses_seen_urls_on_second_call(monkeypatch, base_hits) -> object:
    monkeypatch.setattr(engines, "search", lambda q, cfg, k, cap: list(base_hits))
    monkeypatch.setattr(rag, "rank", lambda q, docs: list(docs))
    first = search_context.deep_context_aware_search(
        "alpha", {}, context="ctx", fetch_top_k=0
    )
    second = search_context.deep_context_aware_search(
        "alpha", {}, context="ctx", fetch_top_k=0
    )
    first_urls = {result["url"] for result in first["results"]}
    second_urls = {result["url"] for result in second["results"]}
    assert second["already_seen_suppressed"] > 0
    assert not (first_urls & second_urls)


def test_context_memory_is_session_scoped(monkeypatch, base_hits) -> object:
    monkeypatch.setattr(engines, "search", lambda q, cfg, k, cap: list(base_hits))
    monkeypatch.setattr(rag, "rank", lambda q, docs: list(docs))

    first_a = search_context.deep_context_aware_search(
        "alpha", {}, context="ctx", fetch_top_k=0, session="a"
    )
    second_a = search_context.deep_context_aware_search(
        "alpha", {}, context="ctx", fetch_top_k=0, session="a"
    )
    first_b = search_context.deep_context_aware_search(
        "alpha", {}, context="ctx", fetch_top_k=0, session="b"
    )

    assert first_a["results"]
    assert second_a["already_seen_suppressed"] > 0
    assert first_b["already_seen_suppressed"] == 0
    assert first_b["results"]


def test_context_memory_uses_kbs_session_env(monkeypatch, base_hits) -> object:
    monkeypatch.setattr(engines, "search", lambda q, cfg, k, cap: list(base_hits))
    monkeypatch.setattr(rag, "rank", lambda q, docs: list(docs))

    monkeypatch.setenv("KBS_SESSION", "env-a")
    first = search_context.deep_context_aware_search(
        "alpha", {}, context="ctx", fetch_top_k=0
    )
    second = search_context.deep_context_aware_search(
        "alpha", {}, context="ctx", fetch_top_k=0
    )
    monkeypatch.setenv("KBS_SESSION", "env-b")
    third = search_context.deep_context_aware_search(
        "alpha", {}, context="ctx", fetch_top_k=0
    )

    assert first["results"]
    assert second["already_seen_suppressed"] > 0
    assert third["already_seen_suppressed"] == 0


def test_memory_does_not_repeat_issued_reformulations(monkeypatch, base_hits) -> object:
    search_queries = []

    def recording_search(query, config, **options) -> object:
        search_queries.append(query)
        return list(base_hits)

    monkeypatch.setattr(engines, "search", recording_search)
    monkeypatch.setattr(rag, "rank", lambda q, docs: list(docs))
    search_context.deep_context_aware_search(
        "climate data", {}, context="ctx", max_rounds=3, fetch_top_k=0
    )
    queries_first = list(search_queries)
    search_queries.clear()
    search_context.deep_context_aware_search(
        "climate data", {}, context="ctx", max_rounds=3, fetch_top_k=0
    )
    for query in search_queries:
        if query != "climate data":
            assert query not in queries_first


def test_context_appended_to_rank_query(monkeypatch, base_hits) -> object:
    captured = []

    def capturing_rank(q, docs) -> object:
        captured.append(q)
        return list(docs)

    monkeypatch.setattr(engines, "search", lambda q, cfg, k, cap: list(base_hits))
    monkeypatch.setattr(rag, "rank", capturing_rank)
    search_context.deep_context_aware_search(
        "alpha query", {}, context="important context text", fetch_top_k=0
    )
    assert any("important context text" in query for query in captured)


def test_already_seen_suppressed_zero_on_first_call(monkeypatch, base_hits) -> object:
    monkeypatch.setattr(engines, "search", lambda q, cfg, k, cap: list(base_hits))
    monkeypatch.setattr(rag, "rank", lambda q, docs: list(docs))
    response = search_context.deep_context_aware_search("alpha", {}, fetch_top_k=0)
    assert response["already_seen_suppressed"] == 0


def test_results_capped_at_60(monkeypatch) -> object:
    many = [_make_hit(f"H{i}", f"https://h{i}.example/", rank=i) for i in range(80)]
    monkeypatch.setattr(engines, "search", lambda q, cfg, k, cap: many)
    monkeypatch.setattr(rag, "rank", lambda q, docs: list(docs))
    assert (
        len(
            search_context.deep_context_aware_search("alpha", {}, fetch_top_k=0)["results"]
        )
        <= 60
    )


def test_return_shape_keys(monkeypatch, base_hits) -> object:
    monkeypatch.setattr(engines, "search", lambda q, cfg, k, cap: list(base_hits))
    monkeypatch.setattr(rag, "rank", lambda q, docs: list(docs))
    response = search_context.deep_context_aware_search("alpha", {}, fetch_top_k=0)
    assert set(response) == {
        "query",
        "context",
        "results",
        "already_seen_suppressed",
        "summary",
        "citations",
        "result_ids",
        "corrections",
        "quality",
    }
