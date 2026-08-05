"""Pin deterministic theme and bibliography assembly for review synthesis."""

import review_latex
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
    assert claim["quote_text"] == hit["snippet"]
    assert claim["quote_text"] in review_synthesis._sentences(claim["source_text"])
    assert claim["citation_key"] == bibliography[0]["key"]
    assert "\\citep{" not in claim["quote_text"]
    assert set(claim) == {
        "quote_text",
        "source_id",
        "source_text",
        "citation_key",
        "theme",
        "rank",
    }




def _scientific_provider_hits() -> list:
    return [
        _claim_hit(
            f"https://{provider}.example/paper",
            title=f"{provider} paper",
            snippet=f"{provider} reports a measured quantum retrieval result.",
            engines=[provider],
        )
        for provider in ("arxiv", "pubmed", "semanticscholar")
    ]


def test_crossref_metadata_skips_claims_but_remains_counted_and_bibliographed() -> None:
    provider_hits = _scientific_provider_hits()
    hits = [
        _claim_hit(
            "https://doi.org/10.1234/crossref",
            title="CrossRef metadata work",
            snippet="Journal of Quantum Studies - Lovelace",
            engines=["crossref"],
            source_text_is_metadata=True,
        ),
        *provider_hits,
    ]
    bibliography = review_synthesis.build_bibliography(hits)
    claims = review_synthesis.build_claims({"science": hits}, "quantum retrieval", bibliography)

    assert review_synthesis._pool_counts(hits) == {
        "crossref": 1,
        "arxiv": 1,
        "pubmed": 1,
        "semanticscholar": 1,
    }
    assert {entry["source_id"] for entry in bibliography} == {hit["url"] for hit in hits}
    assert {claim["source_id"] for claim in claims} == {hit["url"] for hit in provider_hits}
    assert len(claims) == len(provider_hits)


def test_claims_keep_bibliography_pairing_after_theme_reordering() -> None:
    hits = [
        _claim_hit("https://science.example/a", title="A physics paper", categories=["physics"]),
        _claim_hit("https://science.example/b", title="A biology paper", categories=["biology"]),
        _claim_hit("https://science.example/c", title="Another physics paper", categories=["physics"]),
    ]
    themes = review_synthesis.group_themes(hits, query_category="science")
    bibliography = review_synthesis.build_bibliography(hits)

    claims = review_synthesis.build_claims(themes, "quantum retrieval", bibliography)
    entries = {entry["key"]: entry for entry in bibliography}

    assert [hit["url"] for _, hit in [(theme, hit) for theme, items in themes.items() for hit in items]] != [
        hit["url"] for hit in hits
    ]
    assert len(claims) == len(hits)
    assert all(entries[claim["citation_key"]]["source_id"] == claim["source_id"] for claim in claims)


def test_realistic_claims_clear_integrity_gate(monkeypatch) -> None:
    hit = _claim_hit(
        snippet=(
            "Researchers compared longitudinal patient outcomes across three hospital systems using "
            "a preregistered protocol and found that targeted retrieval reduced errors without "
            "increasing review time."
        )
    )
    themes = {"physics": [hit]}
    bibliography = review_synthesis.build_bibliography([hit])
    claims = review_synthesis.build_claims(themes, "targeted retrieval", bibliography)

    assert len(hit["snippet"].split()) >= 20
    assert review_synthesis.review_integrity.check_quotes(
        review_synthesis.quotes_for_integrity({"claims": claims})
    )["status"] == "pass"


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


def test_quote_text_is_verbatim_not_reworded() -> None:
    hit = _claim_hit()
    themes = {"physics": [hit]}
    bibliography = review_synthesis.build_bibliography([hit])

    claim = review_synthesis.build_claims(themes, "quantum retrieval", bibliography)[0]

    assert claim["quote_text"] == hit["snippet"]


def test_quote_record_carries_gate_ready_shape() -> None:
    hit = _claim_hit()
    themes = {"physics": [hit]}
    bibliography = review_synthesis.build_bibliography([hit])

    claim = review_synthesis.build_claims(themes, "quantum retrieval", bibliography)[0]

    assert {"quote_text", "source_id", "source_text", "citation_key"} <= claim.keys()


def _model_hits() -> list:
    rows = [
        ("https://physics.example/one", "Physics one", "Physics", "2020-01-01", "Quantum retrieval improves measured accuracy in controlled trials."),
        ("https://physics.example/two", "Physics two", "Physics", "2021-01-01", "Quantum retrieval reduces error across repeated measurements."),
        ("https://medicine.example/one", "Medicine one", "Medicine", "2021-06-01", "Clinical teams report stronger outcomes after retrieval training."),
        ("https://medicine.example/two", "Medicine two", "Medicine", "2022-06-01", "Clinical studies associate retrieval practice with better outcomes."),
    ]
    return [
        _hit(url, title=title, categories=[category], date=date, snippet=snippet)
        for url, title, category, date, snippet in rows
    ]


def test_build_model_contains_four_phases_and_source_pool_counts() -> None:
    alternatives = [{"term": "information retrieval", "note": "broader term"}]

    model = review_synthesis.build_model("quantum retrieval", _model_hits(), alternatives)

    assert model["status"] == "ok"
    assert {"design", "conduct", "analysis", "write_up"} <= model.keys()
    assert model["conduct"]["source_pools"] == {"arxiv": 4}
    assert model["conduct"]["terminology_alternatives"] == alternatives
    assert set(model["analysis"]) == {"physics", "medicine"}
    assert review_latex.render_tex(model)


def test_write_up_is_dense_synthesis_not_analysis_copy() -> None:
    model = review_synthesis.build_model("quantum retrieval", _model_hits(), [])
    analysis_sentences = [sentence for sentences in model["analysis"].values() for sentence in sentences]

    assert model["write_up"]
    assert model["write_up"] != analysis_sentences


def test_shrink_and_grow_drop_whole_claims_and_restore_bibliography() -> None:
    model = review_synthesis.build_model("quantum retrieval", _model_hits(), [])
    original_keys = {entry["key"] for entry in model["bib"]}

    smaller = review_synthesis.shrink(model)
    grown = review_synthesis.grow(smaller)

    assert len(smaller["claims"]) == len(model["claims"]) - 1
    assert {entry["key"] for entry in smaller["bib"]} < original_keys
    assert len(grown["claims"]) == len(model["claims"])
    assert {entry["key"] for entry in grown["bib"]} == original_keys


def test_drop_flagged_removes_orphaned_bibliography_entries() -> None:
    model = review_synthesis.build_model("quantum retrieval", _model_hits(), [])
    flagged = [{"source_id": model["claims"][0]["source_id"]}]

    filtered = review_synthesis.drop_flagged(model, flagged)
    claimed_keys = {claim["citation_key"] for claim in filtered["claims"]}

    assert filtered["status"] == "ok"
    assert all(entry["key"] in claimed_keys for entry in filtered["bib"])
    assert len(filtered["claims"]) == len(model["claims"]) - 1


def test_build_model_returns_error_below_minimum_claim_floor() -> None:
    model = review_synthesis.build_model("quantum retrieval", _model_hits()[:1], [])

    assert model["status"] == "error"
    assert model["error"] == "minimum_claims"
    assert model["minimum_claims"] == review_synthesis.MIN_CLAIMS


def test_quotes_for_integrity_exposes_only_gate_contract() -> None:
    model = review_synthesis.build_model("quantum retrieval", _model_hits(), [])

    quotes = review_synthesis.quotes_for_integrity(model)

    assert all(
        set(quote) == {"quote_text", "source_id", "source_text", "citation_key"}
        for quote in quotes
    )
    assert len(quotes) == len(model["claims"])


def test_drop_flagged_returns_error_when_floor_would_be_breached() -> None:
    model = review_synthesis.build_model("quantum retrieval", _model_hits()[:2], [])
    flags = [{"source_id": claim["source_id"]} for claim in model["claims"]]

    result = review_synthesis.drop_flagged(model, flags)

    assert result["status"] == "error"
    assert result["error"] == "minimum_claims"


def test_shrink_at_floor_and_grow_without_withheld_claims_are_unchanged() -> None:
    model = review_synthesis.build_model("quantum retrieval", _model_hits()[:2], [])

    assert review_synthesis.shrink(model) == model
    assert review_synthesis.grow(model) == model


def test_render_tex_accepts_the_assembled_model() -> None:
    model = review_synthesis.build_model("quantum retrieval", _model_hits(), [])

    tex = review_latex.render_tex(model)

    assert "\\section{Analysis}" in tex
    assert "\\citep{" in tex
    assert "\\bibliography{review}" in tex
