"""Pin deterministic theme and bibliography assembly for review synthesis."""

import review_synthesis


def _hit(url, **extra) -> dict:
    hit = {
        "title": "A study",
        "url": url,
        "snippet": "The study reports a measurable result.",
        "engines": ["arxiv"],
        "date": "2024-01-02",
        "relevance": 1.0,
        "categories": None,
    }
    hit.update(extra)
    return hit


def test_group_themes_uses_categories_and_query_fallback() -> None:
    hits = [
        _hit("https://one.example/a", categories=["Physics"]),
        _hit("https://two.example/b", categories=["Physics"]),
        _hit("https://three.example/c", categories=None),
        _hit("https://four.example/d", categories=["Medicine"]),
    ]

    themes = review_synthesis.group_themes(hits, query_category="science")

    assert themes["physics"] == hits[:2]
    assert themes["related work"] == [hits[2], hits[3]]


def test_group_themes_caps_themes_without_singleton_groups() -> None:
    hits = [
        _hit(f"https://{index}.example/item", categories=[f"topic-{index}"])
        for index in range(12)
    ]

    themes = review_synthesis.group_themes(hits, query_category="science")

    assert len(themes) <= review_synthesis.THEME_CAP
    assert all(len(group) > 1 for group in themes.values())
    assert sum(map(len, themes.values())) == len(hits)


def _bibliography_hits() -> list:
    return [
        _hit(
            "https://journals.example/paper",
            title="A precise result",
            date="2023-04-05",
            authors=["Ada Lovelace"],
            venue="Journal of Examples",
        ),
        _hit("https://journals.example/other", title="An undated result", date="", categories=[]),
        _hit(
            "https://journals.example/paper",
            title="A duplicate key",
            date="2023-06-05",
            authors=["Ada Lovelace"],
        ),
    ]


def test_bibliography_uses_stable_keys_and_keeps_missing_metadata() -> None:
    bibliography = review_synthesis.build_bibliography(_bibliography_hits())

    assert bibliography[0]["key"] == "lovelace2023"
    assert bibliography[0]["authors"] == ["Ada Lovelace"]
    assert bibliography[0]["venue"] == "Journal of Examples"
    assert bibliography[0]["year"] == "2023"
    assert bibliography[1]["year"] == ""
    assert bibliography[1]["venue"] == "arxiv"
    assert len({entry["key"] for entry in bibliography}) == len(bibliography)
    assert [entry["key"] for entry in bibliography] == [
        "lovelace2023",
        "journals",
        "lovelace2023_2",
    ]
