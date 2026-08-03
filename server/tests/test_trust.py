import json
import os

import enforce


def test_trust_score_uses_news_and_curated_categories() -> None:
    assert enforce.trust_score("https://www.indystar.com/story") == 80
    assert enforce.trust_score("https://developer.mozilla.org/en-US/docs/Web/API") == 95
    assert enforce.trust_score("https://nature.com/article", "science") == 100
    assert (
        enforce.trust_score(
            "https://developer.mozilla.org/en-US/docs/Web/API", "reference"
        )
        == 100
    )
    assert enforce.trust_score("https://unknown.example/article") is None


def test_source_tier_maps_scores() -> None:
    assert enforce.source_tier("https://indystar.com/story") == "primary"
    assert enforce.source_tier("https://videocardz.com/story") == "standard"
    assert enforce.source_tier("https://lifenews.com/story") == "weak"
    assert enforce.source_tier("https://unknown.example/story") == "unknown"


def test_query_category_uses_first_keyword_match() -> None:
    assert enforce.query_category("quantum research software") == "science"
    assert enforce.query_category("NVIDIA GPU benchmarks") == "tech"
    assert enforce.query_category("clinical vaccine therapy") == "health"
    assert enforce.query_category("interest rate and bond outlook") == "finance"
    assert enforce.query_category("HTML syntax documentation") == "reference"
    assert enforce.query_category("local weather forecast") is None


def test_rrf_rank_fuses_equal_weight_signals(monkeypatch) -> None:
    hits = [
        {
            "title": "two-list leader",
            "url": "https://example.com/a",
            "relevance": 1.0,
            "date": "2025-01-01",
        },
        {
            "title": "one-list leader",
            "url": "https://example.com/b",
            "relevance": 0.5,
            "date": "2026-01-01",
        },
    ]
    monkeypatch.setattr(
        enforce,
        "trust_score",
        lambda url, category=None: 90 if url.endswith("/a") else 80,
    )

    ordered = enforce.rrf_rank("general results", hits)

    assert ordered[0]["title"] == "two-list leader"


def test_rrf_rank_penalizes_and_places_undated_hits_last(monkeypatch) -> None:
    hits = [
        {
            "title": "dated",
            "url": "https://example.com/dated",
            "relevance": 1.0,
            "date": "2026-01-01",
        },
        {
            "title": "undated",
            "url": "https://example.com/undated",
            "relevance": 1.0,
        },
    ]
    monkeypatch.setattr(enforce, "trust_score", lambda url, category=None: 80)

    ordered = enforce.rrf_rank("general results", hits)
    tagged = enforce._tag_source(hits[1])

    assert [hit["title"] for hit in ordered] == ["dated", "undated"]
    assert tagged["trust"] == 75


def test_rrf_rank_trust_matches_displayed_trust(monkeypatch) -> None:
    hit = {
        "url": "https://nature.com/paper",
        "relevance": 1.0,
        "citation_count": 100,
    }
    monkeypatch.setattr(enforce, "trust_score", lambda url, category=None: 90)

    ranked_trust = enforce._ranking_trust(
        hit, enforce.query_category("general")
    )
    displayed_trust = enforce._tag_source(hit)["trust"]

    assert ranked_trust == displayed_trust == 89


def test_rrf_rank_preserves_input_order_for_equal_scores(monkeypatch) -> None:
    hits = [
        {
            "title": "first",
            "url": "https://example.com/a",
            "relevance": 1.0,
            "date": "2026-01-01",
        },
        {
            "title": "second",
            "url": "https://example.com/b",
            "relevance": 1.0,
            "date": "2026-01-01",
        },
    ]
    monkeypatch.setattr(enforce, "trust_score", lambda url, category=None: 80)

    ordered = enforce.rrf_rank("general results", hits)

    assert [hit["title"] for hit in ordered] == ["first", "second"]


def test_trust_data_reloads_after_file_change(monkeypatch, tmp_path) -> None:
    path = tmp_path / "trust.json"
    path.write_text(
        json.dumps({"news": {"example.com": 20}, "categories": {}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(enforce, "_TRUST_PATH", path)
    monkeypatch.setattr(enforce, "_TRUST_CACHE", None)

    assert enforce.trust_score("https://example.com") == 20

    previous_mtime = path.stat().st_mtime_ns
    path.write_text(
        json.dumps({"news": {"example.com": 80}, "categories": {}}),
        encoding="utf-8",
    )
    os.utime(path, ns=(previous_mtime + 1, previous_mtime + 1))

    assert enforce.trust_score("https://example.com") == 80

def test_library_scheme_gets_fixed_primary_tier() -> None:
    url = "library://sentient-design?chunk=abc"
    item = {"title": "Sponsored research", "snippet": "Press release"}

    assert enforce.source_tier(url, item) == "primary"
    assert enforce.trust_score(url) == 95


def test_new_science_domains_scored() -> None:
    urls = [
        "https://doi.org/10.1000/x",
        "https://semanticscholar.org/paper/x",
        "https://api.semanticscholar.org/graph/v1/paper/x",
    ]

    for url in urls:
        score = enforce.trust_score(url)
        assert score is not None and score >= 90


def test_citation_count_bonus_capped_and_monotonic() -> None:
    counts = [0, 10, 1000, 10**9]
    scores = [
        enforce._tag_source(
            {
                "url": "https://arxiv.org/abs/1",
                "citation_count": count,
                "date": "2026-01-01",
            }
        )["trust"]
        for count in counts
    ]

    assert scores[0] == enforce.trust_score("https://arxiv.org/abs/1")
    assert scores == sorted(scores)
    assert all(score <= 100 for score in scores)
    assert scores[-1] - scores[0] <= 5


def test_citation_bonus_needs_known_domain() -> None:
    tagged = enforce._tag_source(
        {"url": "https://unknown.example/paper", "citation_count": 10**9}
    )

    assert tagged["trust"] is None
