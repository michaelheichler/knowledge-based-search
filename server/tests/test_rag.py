import types

import rag


def _install_bm25(monkeypatch, response, calls=None) -> None:
    class FakeBM25:
        def index(self, tokens, show_progress=False):
            if calls is not None:
                calls.append("index")

        def retrieve(self, query_tokens, k, show_progress=False):
            if calls is not None:
                calls.append("retrieve")
            return response

    fake_bm25s = types.SimpleNamespace(
        BM25=FakeBM25, tokenize=lambda value, show_progress=False: value
    )
    monkeypatch.setattr(rag, "bm25s", fake_bm25s)


def _install_dense(monkeypatch, calls) -> None:
    def fake_embed(texts, **kwargs):
        calls.append(("embed", texts))
        return [[1.0, 0.0], [0.9, 0.0], [0.0, 1.0], [0.8, 0.0]]

    def fake_rerank(query, docs, **kwargs):
        calls.append(("rerank", query, docs))
        return [
            {"index": 2, "score": 9.0},
            {"index": 0, "score": 8.0},
            {"index": 1, "score": 7.0},
        ]

    monkeypatch.setattr(rag, "embed", fake_embed)
    monkeypatch.setattr(rag, "rerank", fake_rerank)


def test_rank_fuses_embed_rerank_and_bm25(monkeypatch) -> None:
    calls = []
    results = [
        {"title": "alpha", "snippet": "one"},
        {"title": "beta", "snippet": "two"},
        {"title": "gamma", "snippet": "three"},
    ]
    response = types.SimpleNamespace(documents=[[1, 2, 0]], scores=[[3.0, 2.0, 1.0]])
    _install_bm25(monkeypatch, response, calls)
    _install_dense(monkeypatch, calls)
    ranked = rag.rank("alpha", results)
    assert ranked == [results[2], results[0], results[1]]
    assert max(result["relevance"] for result in ranked) == 1.0
    assert ("embed", ["alpha", "alpha one", "beta two", "gamma three"]) in calls
    assert ("rerank", "alpha", ["alpha one", "beta two", "gamma three"]) in calls
    assert "index" in calls
    assert "retrieve" in calls


def test_rank_falls_back_to_bm25_only(monkeypatch) -> None:
    calls = []
    results = ["alpha one", "beta two", "gamma three"]
    response = types.SimpleNamespace(documents=[[1, 0, 2]], scores=[[3.0, 2.0, 1.0]])
    _install_bm25(monkeypatch, response, calls)
    monkeypatch.setattr(rag, "embed", lambda texts, **kwargs: None)
    monkeypatch.setattr(rag, "rerank", lambda query, docs, **kwargs: calls.append("rerank"))
    ranked = rag.rank("beta", results)
    assert ranked == [results[1], results[0], results[2]]
    assert calls == ["index", "retrieve", "rerank"]


def test_rank_uses_rerank_when_embed_fails(monkeypatch) -> None:
    results = ["alpha one", "beta two", "gamma three"]
    response = types.SimpleNamespace(documents=[[2, 1, 0]])
    _install_bm25(monkeypatch, response)
    monkeypatch.setattr(rag, "embed", lambda texts, **kwargs: None)
    monkeypatch.setattr(
        rag,
        "rerank",
        lambda query, docs, **kwargs: [
            {"index": 0},
            {"index": 1},
            {"index": 2},
        ],
    )
    ranked = rag.rank("alpha", results)
    assert ranked == [results[0], results[1], results[2]]


def test_rank_equal_relevance_uses_newer_date(monkeypatch) -> None:
    results = [
        {"title": "older", "snippet": "one", "date": "2025-01-01"},
        {"title": "newer", "snippet": "two", "date": "2026-01-01"},
        {"title": "lower", "snippet": "three", "date": "2027-01-01"},
    ]
    monkeypatch.setattr(rag, "_bm25_order", lambda query, docs: [0, 1, 2])
    monkeypatch.setattr(rag, "_rrf", lambda orders: [(0, 1.0), (1, 1.0), (2, 0.5)])
    monkeypatch.setattr(rag, "embed", lambda texts, **kwargs: None)
    monkeypatch.setattr(rag, "rerank", lambda query, docs, **kwargs: None)
    ranked = rag.rank("beta", results)
    assert ranked == [results[1], results[0], results[2]]
    assert ranked[0]["relevance"] == ranked[1]["relevance"]


def test_rank_higher_relevance_undated_beats_lower_recent(monkeypatch) -> None:
    results = [
        {"title": "strong", "snippet": "one"},
        {"title": "recent", "snippet": "two", "date": "2026-01-01"},
    ]
    monkeypatch.setattr(rag, "_bm25_order", lambda query, docs: [0, 1])
    monkeypatch.setattr(rag, "_rrf", lambda orders: [(0, 1.0), (1, 0.5)])
    monkeypatch.setattr(rag, "embed", lambda texts, **kwargs: None)
    monkeypatch.setattr(rag, "rerank", lambda query, docs, **kwargs: None)
    ranked = rag.rank("beta", results)
    assert ranked == [results[0], results[1]]
    assert ranked[0]["relevance"] > ranked[1]["relevance"]


def test_rank_relevance_scores_ignore_dates(monkeypatch) -> None:
    dated_results = [
        {"title": "alpha", "snippet": "one", "date": "2025-01-01"},
        {"title": "beta", "snippet": "two", "date": "2026-01-01"},
        {"title": "gamma", "snippet": "three", "date": "2024-01-01"},
    ]
    undated_results = [
        {"title": result["title"], "snippet": result["snippet"]}
        for result in dated_results
    ]
    _install_bm25(monkeypatch, types.SimpleNamespace(documents=[[0, 1, 2]]))
    monkeypatch.setattr(rag, "embed", lambda texts, **kwargs: None)
    monkeypatch.setattr(rag, "rerank", lambda query, docs, **kwargs: None)
    dated_ranked = rag.rank("alpha", dated_results)
    undated_ranked = rag.rank("alpha", undated_results)
    dated_relevance = {result["title"]: result["relevance"] for result in dated_ranked}
    undated_relevance = {
        result["title"]: result["relevance"] for result in undated_ranked
    }
    assert dated_relevance == undated_relevance
