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


def test_trust_order_adjusts_relevance_stably() -> None:
    ranked = [
        {
            "title": "Unknown leader",
            "url": "https://unknown.example/a",
            "relevance": 0.60,
        },
        {"title": "Trusted", "url": "https://nature.com/a", "relevance": 0.52},
        {"title": "No URL", "relevance": 0.40},
        {"title": "Unknown peer", "url": "https://other.example/a", "relevance": 0.40},
    ]

    ordered = enforce.trust_order("general results", ranked)

    assert [hit["title"] for hit in ordered] == [
        "Trusted",
        "Unknown leader",
        "No URL",
        "Unknown peer",
    ]


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
