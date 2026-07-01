import os
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import rag


def test_rank_fuses_embed_rerank_and_bm25(monkeypatch):
    calls = []
    results = [
        {"title": "alpha", "snippet": "one"},
        {"title": "beta", "snippet": "two"},
        {"title": "gamma", "snippet": "three"},
    ]

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

    class FakeResponse:
        documents = [[1, 2, 0]]
        scores = [[3.0, 2.0, 1.0]]

    class FakeBM25:
        def index(self, tokens, show_progress=False):
            calls.append(("index", tokens, show_progress))

        def retrieve(self, query_tokens, k, show_progress=False):
            calls.append(("retrieve", query_tokens, k, show_progress))
            return FakeResponse()

    fake_bm25s = types.SimpleNamespace(
        BM25=FakeBM25, tokenize=lambda value, show_progress=False: value
    )
    monkeypatch.setattr(rag, "embed", fake_embed)
    monkeypatch.setattr(rag, "rerank", fake_rerank)
    monkeypatch.setattr(rag, "bm25s", fake_bm25s)

    ranked = rag.rank("alpha", results)

    assert ranked == [results[2], results[0], results[1]]
    assert max(result["relevance"] for result in ranked) == 1.0
    assert ("embed", ["alpha", "alpha one", "beta two", "gamma three"]) in calls
    assert ("rerank", "alpha", ["alpha one", "beta two", "gamma three"]) in calls
    assert any(call[0] == "index" for call in calls)
    assert any(call[0] == "retrieve" for call in calls)


def test_rank_falls_back_to_bm25_only(monkeypatch):
    calls = []
    results = ["alpha one", "beta two", "gamma three"]

    class FakeResponse:
        documents = [[1, 0, 2]]
        scores = [[3.0, 2.0, 1.0]]

    class FakeBM25:
        def index(self, tokens, show_progress=False):
            calls.append("index")

        def retrieve(self, query_tokens, k, show_progress=False):
            calls.append("retrieve")
            return FakeResponse()

    monkeypatch.setattr(rag, "embed", lambda texts, **kwargs: None)
    monkeypatch.setattr(
        rag, "rerank", lambda query, docs, **kwargs: calls.append("rerank")
    )
    monkeypatch.setattr(
        rag,
        "bm25s",
        types.SimpleNamespace(
            BM25=FakeBM25, tokenize=lambda value, show_progress=False: value
        ),
    )

    ranked = rag.rank("beta", results)

    assert ranked == [results[1], results[0], results[2]]
    assert calls == ["index", "retrieve", "rerank"]


def test_rank_uses_rerank_when_embed_fails(monkeypatch):
    results = ["alpha one", "beta two", "gamma three"]

    class FakeResponse:
        documents = [[2, 1, 0]]

    class FakeBM25:
        def index(self, tokens, show_progress=False):
            return None

        def retrieve(self, query_tokens, k, show_progress=False):
            return FakeResponse()

    def fake_rerank(query, docs, **kwargs):
        return [{"index": 0}, {"index": 1}, {"index": 2}]

    monkeypatch.setattr(rag, "embed", lambda texts, **kwargs: None)
    monkeypatch.setattr(rag, "rerank", fake_rerank)
    monkeypatch.setattr(
        rag,
        "bm25s",
        types.SimpleNamespace(
            BM25=FakeBM25, tokenize=lambda value, show_progress=False: value
        ),
    )

    ranked = rag.rank("alpha", results)

    assert ranked == [results[0], results[1], results[2]]


def test_rank_equal_relevance_uses_newer_date(monkeypatch):
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


def test_rank_higher_relevance_undated_beats_lower_recent(monkeypatch):
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


def test_rank_relevance_scores_ignore_dates(monkeypatch):
    dated_results = [
        {"title": "alpha", "snippet": "one", "date": "2025-01-01"},
        {"title": "beta", "snippet": "two", "date": "2026-01-01"},
        {"title": "gamma", "snippet": "three", "date": "2024-01-01"},
    ]
    undated_results = [
        {"title": result["title"], "snippet": result["snippet"]}
        for result in dated_results
    ]

    class FakeResponse:
        documents = [[0, 1, 2]]

    class FakeBM25:
        def index(self, tokens, show_progress=False):
            return None

        def retrieve(self, query_tokens, k, show_progress=False):
            return FakeResponse()

    monkeypatch.setattr(rag, "embed", lambda texts, **kwargs: None)
    monkeypatch.setattr(rag, "rerank", lambda query, docs, **kwargs: None)
    monkeypatch.setattr(
        rag,
        "bm25s",
        types.SimpleNamespace(
            BM25=FakeBM25, tokenize=lambda value, show_progress=False: value
        ),
    )

    dated_ranked = rag.rank("alpha", dated_results)
    undated_ranked = rag.rank("alpha", undated_results)

    dated_relevance = {result["title"]: result["relevance"] for result in dated_ranked}
    undated_relevance = {
        result["title"]: result["relevance"] for result in undated_ranked
    }

    assert dated_relevance == undated_relevance
