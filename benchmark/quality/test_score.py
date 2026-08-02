import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import score


def _r(url, relevance=0.0, date="", engines=None):
    return {"url": url, "relevance": relevance, "date": date, "engines": engines or ["searxng"]}


def test_unique_domain_ratio_dedup():
    results = [_r("https://a.com/1"), _r("https://a.com/2"), _r("https://b.com/3")]
    assert score.unique_domain_ratio(results) == round(2 / 3, 3)


def test_date_present_ratio():
    results = [_r("https://a.com", date="2026-01-01"), _r("https://b.com")]
    assert score.date_present_ratio(results) == 0.5


def test_recency_hit_counts_recent_in_top5():
    results = [_r("https://a.com", date="2026-01-01"), _r("https://b.com", date="2010-01-01")]
    assert score.recency_hit(results) == 0.5


def test_mean_and_top1_relevance():
    results = [_r("https://a.com", relevance=1.0), _r("https://b.com", relevance=0.5)]
    assert score.mean_relevance(results) == 0.75
    assert score.top1_relevance(results) == 1.0


def test_engine_diversity_counts_distinct():
    results = [_r("https://a.com", engines=["searxng", "mojeek"]), _r("https://b.com", engines=["searxng"])]
    assert score.engine_diversity(results) == 2


def test_score_query_adds_recency_only_for_recency_category():
    results = [_r("https://a.com", date="2026-01-01")]
    assert "recency_hit" in score.score_query(results, "recency")
    assert "recency_hit" not in score.score_query(results, "research")


def test_variants_well_formed():
    import run_variants
    names = [v["name"] for v in run_variants.VARIANTS]
    assert len(names) == len(set(names))
    for variant in run_variants.VARIANTS:
        assert {"name", "engines", "per_engine", "rank"} <= set(variant)


def test_pool_from_cache_subsets_and_merges():
    import run_variants
    cache = {
        "searxng": [{"url": "https://a.com", "engine": "searxng", "rank": i} for i in range(1, 6)],
        "mojeek": [{"url": "https://b.com", "engine": "mojeek", "rank": 1}],
    }
    pool = run_variants._pool_from_cache(cache, {"engines": None, "per_engine": 2})
    urls = {hit["url"] for hit in pool}
    assert urls == {"https://a.com", "https://b.com"}


def test_has_hits_distinguishes_empty_from_populated():
    import json
    import tempfile

    import run_variants

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
        json.dump({"searxng": [], "mojeek": []}, handle)
        empty = handle
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
        json.dump({"searxng": [{"url": "https://a.com"}]}, handle)
        populated = handle

    assert run_variants._has_hits(empty.name) is False
    assert run_variants._has_hits(populated.name) is True
    assert run_variants._has_hits("/no/such/file.json") is False


def test_pool_from_cache_respects_engine_filter():
    import run_variants
    cache = {
        "searxng": [{"url": "https://a.com", "engine": "searxng", "rank": 1}],
        "mojeek": [{"url": "https://b.com", "engine": "mojeek", "rank": 1}],
    }
    pool = run_variants._pool_from_cache(cache, {"engines": ["searxng"], "per_engine": 10})
    assert {hit["url"] for hit in pool} == {"https://a.com"}
