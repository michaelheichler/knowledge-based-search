"""Pin review orchestration order and fail-closed artifact publication."""

import re
import shutil
from pathlib import Path
from unittest.mock import Mock

import pytest
import review
import review_integrity


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


def _methodology_model() -> dict:
    return {
        "design": {
            "classification": "Rapid Review",
            "topic": "quantum methods",
            "question": "Which quantum methods recur?",
        },
        "conduct": {
            "source_pools": {"arxiv": 2, "pubmed": 1},
            "search_scope": {"arxiv": "2 ranked hit(s)", "pubmed": "1 ranked hit(s)"},
        },
        "analysis": {"measurement": [], "simulation": []},
        "bib": [{"key": "paper2024"}],
    }


def _assert_methodology_content(content: str) -> None:
    for value in ("Rapid Review", "Grant & Booth (2009)", "arxiv: 2", "pubmed: 1"):
        assert value in content
    for value in ("measurement", "simulation", "3 page(s)"):
        assert value in content
    for threshold in (
        review_integrity.WORD_RATIO_THRESHOLD,
        review_integrity.LONGEST_BLOCK_WORDS,
        review_integrity.EMBEDDING_COSINE_THRESHOLD,
    ):
        assert str(threshold) in content


def test_methodology_guide_records_run_data_and_writes_atomically(tmp_path, monkeypatch) -> None:
    replacements = []
    original_replace = review.os.replace
    monkeypatch.setattr(
        review.os,
        "replace",
        lambda source, destination: (
            replacements.append((Path(source), Path(destination))),
            original_replace(source, destination),
        )[1],
    )

    path = Path(review.write_methodology_guide(_methodology_model(), {"status": "pass", "pages": 3}, tmp_path))
    _assert_methodology_content(path.read_text(encoding="utf-8"))

    assert path == tmp_path / "methodology.md"
    assert len(replacements) == 1
    assert replacements[0][1] == path
    assert not list(tmp_path.glob(".methodology.md.*"))


def _install_real_guide_stubs(monkeypatch):
    model = {**_methodology_model(), "status": "ok", "claims": []}

    def compile_stub(_model, directory, *_callbacks) -> dict:
        output = Path(directory)
        return {
            "status": "ok",
            "pdf_path": str(output / "review.pdf"),
            "tex_path": str(output / "review.tex"),
            "pages": 3,
        }

    monkeypatch.setattr(review.review_synthesis, "build_model", lambda *args: model)
    monkeypatch.setattr(review.review_synthesis, "claims_for_integrity", lambda value: [])
    monkeypatch.setattr(review.review_integrity, "check_claims", lambda claims: {"status": "pass"})
    monkeypatch.setattr(review.review_latex, "compile_review", compile_stub)



def test_generate_review_guide_lands_with_compiled_pdf(tmp_path, monkeypatch) -> None:
    _install_real_guide_stubs(monkeypatch)

    result = review.generate_review("topic", [], [], tmp_path)

    output = Path(result["pdf_path"]).parent
    guide = Path(result["guide_path"])
    assert guide == output / "methodology.md"
    assert guide.is_file()
    assert output / "review.pdf" == Path(result["pdf_path"])
    assert "arxiv: 2" in guide.read_text(encoding="utf-8")


def _canned_review_hits() -> list[dict]:
    return [
        {
            "title": "Quantum signal methods",
            "source_id": "arxiv:2401.00001",
            "snippet": "Quantum methods improve signal quality.",
            "engines": ["arxiv"],
            "categories": ["measurement"],
            "date": "2024-01-01",
            "authors": "Doe, Jane",
        },
        {
            "title": "Quantum measurement design",
            "source_id": "pubmed:12345678",
            "snippet": "Quantum methods guide measurement design.",
            "engines": ["pubmed"],
            "categories": ["simulation"],
            "date": "2023-01-01",
            "authors": "Smith, Alex",
        },
    ]


def _citation_keys(tex: str) -> set[str]:
    markers = re.findall(r"\\cite[pt]\{([^{}]+)\}", tex)
    return {key.strip() for marker in markers for key in marker.split(",")}


@pytest.mark.skipif(shutil.which("pdflatex") is None, reason="pdflatex is not installed")
def test_real_review_pipeline_publishes_cited_pdf_and_methodology(tmp_path: Path) -> None:
    result = review.generate_review("quantum methods", _canned_review_hits(), [], tmp_path)

    assert result["status"] == "ok"
    output = Path(result["pdf_path"]).parent
    assert Path(result["pdf_path"]).is_file()
    assert 2 <= result["pages"] <= 4 or result.get("warning")
    tex = (output / "review.tex").read_text(encoding="utf-8")
    bib = (output / "review.bib").read_text(encoding="utf-8")
    bib_keys = set(re.findall(r"@\w+\{([^,]+),", bib))
    assert re.search(r"\\cite[pt]\{", tex)
    assert r"\bibliographystyle{agsm}" in tex
    assert bib_keys
    assert bib_keys <= _citation_keys(tex)
    assert (output / "methodology.md").is_file()




