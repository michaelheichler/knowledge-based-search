"""Pin quote attribution integrity."""

import review_integrity


def _quote(quote_text, source_text, source_id="source") -> dict:
    return {
        "quote_text": quote_text,
        "source_id": source_id,
        "source_text": source_text,
        "citation_key": "paper2024",
    }


def test_exact_source_sentence_passes_attribution_gate() -> None:
    result = review_integrity.check_quotes(
        [_quote("The study reports improved recall.", "The study reports improved recall.")]
    )

    assert result == {"status": "pass"}


def test_quote_absent_from_source_flags_fabrication() -> None:
    quote = _quote(
        "The study reports improved precision.",
        "The study reports improved recall.",
        "paper-a",
    )

    result = review_integrity.check_quotes([quote])

    assert result == {
        "status": "flagged",
        "flags": [
            {
                "quote_text": quote["quote_text"],
                "source_id": "paper-a",
                "signal": "attribution",
            }
        ],
    }


def test_quote_from_wrong_source_flags_misattribution() -> None:
    result = review_integrity.check_quotes(
        [
            _quote(
                "The trial reports improved recall.",
                "The trial reports improved precision.",
                "wrong-paper",
            )
        ]
    )

    assert result["status"] == "flagged"
    assert result["flags"][0]["source_id"] == "wrong-paper"
    assert result["flags"][0]["quote_text"] == "The trial reports improved recall."


def test_attribution_normalization_tolerates_case_and_punctuation() -> None:
    result = review_integrity.check_quotes(
        [_quote("The Study reports improved recall", "the study reports improved recall!")]
    )

    assert result == {"status": "pass"}


def test_multiple_invalid_quotes_report_each_source_id() -> None:
    result = review_integrity.check_quotes(
        [
            _quote("First fabricated sentence.", "First source sentence.", "one"),
            _quote("Second fabricated sentence.", "Second source sentence.", "two"),
        ]
    )

    assert result["status"] == "flagged"
    assert {flag["source_id"] for flag in result["flags"]} == {"one", "two"}
