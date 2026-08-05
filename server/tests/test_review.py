"""Pin review orchestration order and fail-closed artifact publication."""

from pathlib import Path
from unittest.mock import Mock

import review


def _model(claims=3):
    return {
        "status": "ok",
        "analysis": {"physics": []},
        "claims": [{"claim_sentence": f"claim {index}"} for index in range(claims)],
        "bib": [{"key": "paper2024"}],
    }


def _compiled(out_dir):
    return {
        "status": "ok",
        "pdf_path": str(out_dir / "review.pdf"),
        "tex_path": str(out_dir / "review.tex"),
        "pages": 3,
    }


def _patch_success(monkeypatch, calls, model):
    build = Mock(side_effect=lambda *args: calls.append("build") or model)
    claims = Mock(side_effect=lambda value: calls.append("claims") or value["claims"])
    check = Mock(side_effect=lambda value: calls.append("check") or {"status": "pass"})
    compile_review = Mock(
        side_effect=lambda value, directory, shrink, grow: calls.append("compile")
        or _compiled(Path(directory))
    )
    guide = Mock(
        side_effect=lambda value, integrity, directory: calls.append("guide")
        or str(Path(directory) / "methodology.md")
    )
    monkeypatch.setattr(review.review_synthesis, "build_model", build)
    monkeypatch.setattr(review.review_synthesis, "claims_for_integrity", claims)
    monkeypatch.setattr(review.review_integrity, "check_claims", check)
    monkeypatch.setattr(review.review_latex, "compile_review", compile_review)
    monkeypatch.setattr(review, "write_methodology_guide", guide)
    return check


def test_generate_review_keeps_synthesis_gate_compile_order(tmp_path, monkeypatch) -> None:
    calls = []
    check = _patch_success(monkeypatch, calls, _model())

    result = review.generate_review("topic", ["hit"], ["alternative"], tmp_path)

    output = Path(result["pdf_path"]).parent
    assert result["status"] == "ok"
    assert result["guide_path"] == str(output / "methodology.md")
    assert result["themes"] == ["physics"]
    assert result["sources_cited"] == 1
    assert [call for call in calls] == ["build", "claims", "check", "compile", "guide"]
    assert check.call_count == 1


def test_generate_review_drops_flagged_claims_before_rechecking(tmp_path, monkeypatch) -> None:
    calls = []
    first, clean = _model(), _model(2)
    flags = [{"claim_sentence": "claim 0", "source_id": "paper"}]
    check = Mock(side_effect=[{"status": "flagged", "flags": flags}, {"status": "pass"}])
    _patch_success(monkeypatch, calls, first)
    monkeypatch.setattr(review.review_integrity, "check_claims", check)
    monkeypatch.setattr(
        review.review_synthesis,
        "drop_flagged",
        Mock(side_effect=lambda value, found: calls.append("drop") or clean),
    )

    result = review.generate_review("topic", [], [], tmp_path)

    assert result["status"] == "ok"
    assert calls == ["build", "claims", "drop", "claims", "compile", "guide"]
    assert check.call_count == 2


def test_generate_review_stops_at_integrity_floor_without_output_directory(tmp_path, monkeypatch) -> None:
    calls = []
    _patch_success(monkeypatch, calls, _model(2))
    monkeypatch.setattr(
        review.review_integrity,
        "check_claims",
        lambda claims: {"status": "flagged", "flags": [{"claim_sentence": "copy"}]},
    )
    monkeypatch.setattr(
        review.review_synthesis,
        "drop_flagged",
        lambda value, flags: {"status": "error", "error": "minimum_claims"},
    )

    result = review.generate_review("topic", [], [], tmp_path)

    assert result["error"] == "IntegrityFloor"
    assert result["flags"] == [{"claim_sentence": "copy"}]
    assert not (tmp_path / "reviews").exists()
    assert calls == ["build", "claims"]


def test_generate_review_returns_compile_error_without_guide(tmp_path, monkeypatch) -> None:
    error = {"status": "error", "error": "CalledProcessError", "log_tail": "fatal"}
    guide = Mock()
    _patch_success(monkeypatch, [], _model())
    monkeypatch.setattr(review.review_latex, "compile_review", lambda *args: error)
    monkeypatch.setattr(review, "write_methodology_guide", guide)

    assert review.generate_review("topic", [], [], tmp_path) == error
    guide.assert_not_called()


def test_output_directory_uses_slug_and_timestamp(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(review, "_timestamp", lambda: "20260805-120000")

    output = review._output_directory(tmp_path, "A topic: with punctuation!")

    assert output == tmp_path / "reviews" / "a-topic-with-punctuation-20260805-120000"
