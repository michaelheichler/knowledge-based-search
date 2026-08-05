"""Pin lexical and optional semantic integrity signals."""

import pytest
import review_integrity


@pytest.fixture(autouse=True)
def _disable_embeddings(monkeypatch) -> None:
    """Test invariant: lexical tests do not depend on local model availability."""
    monkeypatch.setattr(review_integrity.rag, "embed", lambda _texts: None)


def _result(claim, source, source_id="source") -> dict:
    """Test invariant: every fixture carries one explicit source attribution."""
    return review_integrity.check_claims(
        [{"claim_sentence": claim, "source_id": source_id, "source_text": source}]
    )


def test_word_ratio_threshold_flags_exact_boundary() -> None:
    """Boundary invariant: a ratio equal to the threshold is unsafe."""
    result = _result(
        "a b c d e f g x y z",
        "a b c d e f g u v w",
    )

    assert result["status"] == "flagged"
    assert any(
        flag["signal"] == "word_ratio" and flag["score"] == 0.7
        for flag in result["flags"]
    )


def test_word_ratio_threshold_allows_just_below_boundary() -> None:
    """Boundary invariant: a ratio below the threshold does not flag alone."""
    result = _result(
        "a b c d e f x y z q",
        "a b c d e f u v w t",
    )

    assert result == {"status": "pass"}


def test_longest_block_threshold_flags_exact_boundary() -> None:
    """Boundary invariant: eight contiguous words are an unsafe lifted clause."""
    result = _result(
        "a b c d e f g h x1 x2 x3 x4 x5 x6 x7 x8",
        "a b c d e f g h y1 y2 y3 y4 y5 y6 y7 y8",
    )

    assert result["status"] == "flagged"
    assert any(
        flag["signal"] == "longest_block" and flag["score"] == 8
        for flag in result["flags"]
    )


def test_longest_block_threshold_allows_seven_words() -> None:
    """Boundary invariant: seven contiguous words do not flag alone."""
    result = _result(
        "a b c d e f g x1 x2 x3 x4 x5 x6 x7 x8 x9",
        "a b c d e f g y1 y2 y3 y4 y5 y6 y7 y8 y9",
    )

    assert result == {"status": "pass"}


def test_embedded_verbatim_clause_flags_block_signal_without_ratio() -> None:
    """Clause invariant: reworded surroundings cannot hide a copied block."""
    result = _result(
        "This finding aligns with prior work suggesting that regular exercise reduces the risk of cardiovascular disease in older adults, though effect sizes varied by study population.",
        "Our meta-analysis confirms that regular exercise reduces the risk of cardiovascular disease in older adults across all cohorts studied.",
    )

    assert result["status"] == "flagged"
    assert {flag["signal"] for flag in result["flags"]} == {"longest_block"}


def test_genuine_paraphrase_passes_lexical_signals() -> None:
    """Paraphrase invariant: changed wording must pass both lexical signals."""
    result = _result(
        "Older adults may experience fewer cardiovascular complications when they exercise regularly.",
        "Regular exercise reduces cardiovascular disease risk among older adults.",
    )

    assert result == {"status": "pass"}


def test_empty_source_text_produces_no_flags() -> None:
    """Source invariant: no retrieved text means no comparison is possible."""
    assert _result("A claim without retrieved evidence.", "") == {"status": "pass"}


def test_only_cited_source_sentences_are_compared() -> None:
    """Attribution invariant: unrelated corpus text cannot flag a claim."""
    result = _result(
        "The source repeats this exact claim.",
        "An unrelated source discusses another result.",
    )

    assert result == {"status": "pass"}


def test_multiple_flagged_claims_are_returned_in_one_report() -> None:
    """Batch invariant: every flagged claim is returned without fail-first behavior."""
    result = review_integrity.check_claims(
        [
            {
                "claim_sentence": "The first claim is copied exactly.",
                "source_id": "one",
                "source_text": "The first claim is copied exactly.",
            },
            {
                "claim_sentence": "The second claim is copied exactly.",
                "source_id": "two",
                "source_text": "The second claim is copied exactly.",
            },
        ]
    )

    assert result["status"] == "flagged"
    assert {flag["source_id"] for flag in result["flags"]} == {"one", "two"}


def test_embedding_flags_reorder_only_copy_and_embeds_unique_sentences(monkeypatch) -> None:
    """Semantic invariant: reordered copies can flag without lexical overlap."""
    claim = "kappa iota theta eta zeta epsilon delta gamma beta alpha"
    source = "alpha beta gamma delta epsilon zeta eta theta iota kappa"
    calls = []

    def fake_embed(texts) -> list:
        calls.append(list(texts))
        return [[1.0, 0.0] if text == claim else [0.95, 0.3122499] for text in texts]

    monkeypatch.setattr(review_integrity.rag, "embed", fake_embed)

    result = _result(claim, source)

    assert {flag["signal"] for flag in result["flags"]} == {"embedding_cosine"}
    assert calls == [[claim, source]]


def test_embedding_none_degrades_to_layer_one_only(monkeypatch) -> None:
    """Degrade invariant: missing model vectors never add an error or raise."""
    monkeypatch.setattr(review_integrity.rag, "embed", lambda _texts: None)

    result = _result("The source sentence is copied exactly.", "The source sentence is copied exactly.")

    assert result["status"] == "flagged"
    assert {flag["signal"] for flag in result["flags"]} == {"word_ratio"}


def test_embedding_cosine_threshold_has_exact_and_below_boundaries(monkeypatch) -> None:
    """Boundary invariant: cosine equality flags and a lower score passes."""
    claim = "claim words differ from source terms"
    source = "source terms describe another finding"
    score = {"value": 0.90}

    monkeypatch.setattr(review_integrity.rag, "embed", lambda texts: [[score["value"]] for _ in texts])
    monkeypatch.setattr(review_integrity.rag, "_cosine", lambda left, _right: left[0])
    assert any(
        flag["signal"] == "embedding_cosine"
        for flag in _result(claim, source)["flags"]
    )

    score["value"] = 0.899
    assert _result(claim, source) == {"status": "pass"}
