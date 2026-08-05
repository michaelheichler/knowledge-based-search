"""Pin deterministic theme and bibliography assembly for review synthesis."""

import rag
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


def _claim_hit(url="https://science.example/paper", **extra) -> dict:
    defaults = {
        "title": "Evidence study",
        "categories": ["Physics"],
        "date": "2022-05-01",
        "snippet": "Quantum methods improve retrieval accuracy in clinical settings.",
    }
    defaults.update(extra)
    return _hit(url, **defaults)


def test_claims_keep_attribution_and_use_one_real_citation() -> None:
    hit = _claim_hit()
    themes = review_synthesis.group_themes([hit], query_category="science")
    bibliography = review_synthesis.build_bibliography([hit])

    claims = review_synthesis.build_claims(themes, "quantum retrieval", bibliography)

    assert len(claims) == 1
    claim = claims[0]
    assert claim["source_id"] == hit["url"]
    assert claim["source_text"] == hit["snippet"]
    assert claim["claim_sentence"] != hit["snippet"]
    assert claim["claim_sentence"].count("\\citep{") == 1
    assert bibliography[0]["key"] in claim["claim_sentence"]


def test_library_claims_use_deepened_text_and_keep_snippet_on_failure(monkeypatch) -> None:
    hit = _claim_hit("library://book-1?chunk=2", snippet="Short library snippet.")
    themes = {"physics": [hit]}
    bibliography = review_synthesis.build_bibliography([hit])
    monkeypatch.setattr(
        review_synthesis.library_engine,
        "get_passage_from_url",
        lambda _url: {"text": "The complete attributed library passage has detail."},
    )

    deep_claim = review_synthesis.build_claims(themes, "library detail", bibliography)[0]

    assert deep_claim["source_text"].startswith("The complete attributed")

    def fail(_url) -> None:
        raise OSError("offline")

    monkeypatch.setattr(review_synthesis.library_engine, "get_passage_from_url", fail)
    shallow_claim = review_synthesis.build_claims(themes, "library detail", bibliography)[0]

    assert shallow_claim["source_text"] == "Short library snippet."


def test_formula_and_chart_candidates_require_source_data() -> None:
    formula_hit = _claim_hit(
        snippet="The estimate follows x = y + 1 for the observed sample.",
    )
    formula_free = _claim_hit(
        "https://science.example/other",
        snippet="The result describes a qualitative comparison without equations.",
    )
    bibliography = review_synthesis.build_bibliography([formula_hit, formula_free])

    assert review_synthesis.formulas_from_hits([formula_hit]) == ["x = y + 1"]
    assert review_synthesis.formulas_from_hits([formula_free]) == []
    assert review_synthesis.chart_from_bibliography(bibliography) == {"2022": 2}


def test_generated_claims_do_not_start_with_filler_phrases() -> None:
    hit = _claim_hit()
    themes = {"physics": [hit]}
    bibliography = review_synthesis.build_bibliography([hit])

    claim = review_synthesis.build_claims(themes, "quantum retrieval", bibliography)[0]
    lowered = claim["claim_sentence"].lower()

    assert not any(lowered.startswith(phrase) for phrase in review_synthesis.FILLER_DENYLIST)


def test_review_integrity_accepts_claim_shape(monkeypatch) -> None:
    hit = _claim_hit()
    themes = {"physics": [hit]}
    bibliography = review_synthesis.build_bibliography([hit])
    monkeypatch.setattr(rag, "embed", lambda _texts: None)

    claim = review_synthesis.build_claims(themes, "quantum retrieval", bibliography)[0]

    assert {"claim_sentence", "source_id", "source_text"} <= claim.keys()
    assert review_synthesis.review_integrity.check_claims([claim])["status"] in {
        "pass",
        "flagged",
    }
