"""Validate the local LaTeX and BibTeX boundary used by review generation."""

import shutil
from pathlib import Path
from unittest.mock import Mock

import pytest
import review_latex

_MINIMAL_TEX = r"""\documentclass[11pt]{article}
\usepackage[a4paper,margin=1in]{geometry}
\usepackage{natbib}
\usepackage{tikz}
\usepackage{pgfplots}
\usepackage{amsmath}
\pgfplotsset{compat=1.18}
\begin{document}
A cited review needs stable author-date references \citep{grant2009,booth2019}.
\begin{equation}
  E = mc^2
\end{equation}
\begin{tikzpicture}
\begin{axis}[
  ybar,
  symbolic x coords={2020,2021,2022},
  xtick=data,
  width=0.8\textwidth,
  height=5cm
]
\addplot coordinates {(2020,2) (2021,3) (2022,4)};
\end{axis}
\end{tikzpicture}
\bibliographystyle{agsm}
\bibliography{minimal}
\end{document}
"""
_MINIMAL_BIB = r"""@article{grant2009,
  author = {Grant, Maria J. and Booth, Andrew},
  title = {A typology of reviews},
  journal = {Health Information and Libraries Journal},
  year = {2009}
}
@article{booth2019,
  author = {Booth, Andrew and Sutton, Anthea},
  title = {Systematic approaches to evidence},
  journal = {Research Methods Quarterly},
  year = {2019}
}
"""


@pytest.mark.skipif(shutil.which("pdflatex") is None, reason="pdflatex is not installed")
def test_real_compile_supports_review_toolchain(tmp_path: Path) -> None:
    """A real PDF proves the selected citation and fragment packages work together."""
    (tmp_path / "minimal.tex").write_text(_MINIMAL_TEX, encoding="utf-8")
    (tmp_path / "minimal.bib").write_text(_MINIMAL_BIB, encoding="utf-8")

    result = review_latex.run_compile(tmp_path, "minimal")

    assert result["status"] == "ok"
    pdf_path = Path(result["pdf_path"])
    assert pdf_path.is_file()
    assert review_latex.page_count(pdf_path) >= 1
    assert "Grant" in (tmp_path / "minimal.bbl").read_text(encoding="utf-8")
    assert "Citation `grant2009'" not in (tmp_path / "minimal.log").read_text(
        encoding="utf-8", errors="replace"
    )


_MODEL = {
    "title": "Baseline review",
    "question": "Which methods recur?",
    "design": r"Design claim \citep{alpha}.",
    "conduct": r"Conduct claim \citet{beta}.",
    "analysis": {"Theme": r"Thematic claim \citep{alpha}."},
    "write_up": r"Write-up claim \citep{beta}.",
    "bib": [
        {
            "key": "alpha",
            "authors": "Grant, Maria J. and Booth, Andrew",
            "year": 2009,
            "title": "A typology of reviews",
            "venue": "Review Journal",
        },
        {
            "key": "beta",
            "authors": "Booth, Andrew and Sutton, Anthea",
            "year": 2019,
            "title": "Evidence methods",
            "venue": "Methods Quarterly",
        },
    ],
    "chart": {2009: 1, 2019: 1},
    "formulas": [r"x = y"],
}


def test_render_tex_escapes_raw_fields_and_preserves_citations() -> None:
    """Escaping protects the document while citation commands remain executable."""
    model = {**_MODEL, "title": r"100% & _ # $ \\ title"}
    model["design"] = r"20% & _ # $ \\ prose \citep{alpha}."

    tex = review_latex.render_tex(model)

    for escaped in (r"\%", r"\&", r"\_", r"\#", r"\$", r"\textbackslash{}"):
        assert escaped in tex
    assert r"\citep{alpha}" in tex


def test_render_tex_keeps_snyder_sections_in_order() -> None:
    """Section order makes the method visible instead of relying on dictionary order."""
    tex = review_latex.render_tex(_MODEL)
    positions = [tex.index(rf"\section{{{name}}}") for name in ("Design", "Conduct", "Analysis", "Write-up")]

    assert positions == sorted(positions)


def test_render_tex_gates_chart_and_formula_fragments_on_data() -> None:
    """Absent source data must not produce literature-looking visual content."""
    empty = {**_MODEL, "chart": {}, "formulas": []}
    without_fragments = review_latex.render_tex(empty)
    with_fragments = review_latex.render_tex(_MODEL)

    assert r"\addplot" not in without_fragments
    assert r"\begin{equation*}" not in without_fragments
    assert r"\addplot" in with_fragments
    assert r"\begin{equation*}" in with_fragments


def test_render_bib_and_render_tex_require_citation_coverage() -> None:
    """Bibliography output carries agsm fields and rejects an uncited source."""
    bib = review_latex.render_bib(_MODEL)
    uncited = {**_MODEL, "bib": [*_MODEL["bib"], {"key": "orphan"}]}

    assert "author = {Grant, Maria J. and Booth, Andrew}" in bib
    assert "year = {2009}" in bib
    assert "journal = {Review Journal}" in bib
    with pytest.raises(ValueError, match="uncited bibliography entries"):
        review_latex.render_tex(uncited)


@pytest.mark.skipif(shutil.which("pdflatex") is None, reason="pdflatex is not installed")
def test_rendered_model_compiles_with_the_validated_toolchain(tmp_path: Path) -> None:
    """The rendered model must pass through the same real compiler as the spike."""
    (tmp_path / "review.tex").write_text(review_latex.render_tex(_MODEL), encoding="utf-8")
    (tmp_path / "review.bib").write_text(review_latex.render_bib(_MODEL), encoding="utf-8")

    result = review_latex.run_compile(tmp_path, "review")

    assert result["status"] == "ok"
    assert Path(result["pdf_path"]).is_file()
    assert review_latex.page_count(result["pdf_path"]) >= 1


def _stub_compile(directory, jobname) -> dict:
    """Subprocesses remain mocked because page-count scenarios must be deterministic."""
    pdf_path = Path(directory) / f"{jobname}.pdf"
    pdf_path.write_bytes(b"compiled-pdf")
    return {"status": "ok", "pdf_path": str(pdf_path)}


def _assert_final_artifacts(output: Path) -> None:
    assert {path.name for path in output.iterdir()} == {
        "review.tex",
        "review.bib",
        "review.pdf",
    }


def test_compile_review_publishes_first_in_range_attempt_atomically(tmp_path, monkeypatch) -> None:
    """Intermediate attempts stay private so consumers only see final artifacts."""
    run_compile = Mock(side_effect=_stub_compile)
    monkeypatch.setattr(review_latex, "run_compile", run_compile)
    monkeypatch.setattr(review_latex, "page_count", lambda _path: 3)
    shrink = Mock()
    grow = Mock()

    result = review_latex.compile_review(_MODEL, tmp_path, shrink, grow)

    assert result["status"] == "ok"
    assert result["pages"] == 3
    assert run_compile.call_count == 1
    assert not shrink.called
    assert not grow.called
    _assert_final_artifacts(tmp_path)
    assert (tmp_path / "review.pdf").read_bytes() == b"compiled-pdf"


def test_compile_review_shrinks_once_before_accepting_in_range_attempt(tmp_path, monkeypatch) -> None:
    """A page overflow must be corrected before another compile is accepted."""
    pages = iter((5, 3))
    run_compile = Mock(side_effect=_stub_compile)
    monkeypatch.setattr(review_latex, "run_compile", run_compile)
    monkeypatch.setattr(review_latex, "page_count", lambda _path: next(pages))
    shrink = Mock(side_effect=lambda model: model)
    grow = Mock(side_effect=lambda model: model)

    result = review_latex.compile_review(_MODEL, tmp_path, shrink, grow)

    assert result["status"] == "ok"
    assert result["pages"] == 3
    assert run_compile.call_count == 2
    assert shrink.call_count == 1
    assert grow.call_count == 0


def test_compile_review_uses_nearest_attempt_after_retry_budget(tmp_path, monkeypatch) -> None:
    """Preserve the nearest artifact when the fixed retry budget cannot fit layout."""
    pages = iter((1, 6, 6))
    run_compile = Mock(side_effect=_stub_compile)
    monkeypatch.setattr(review_latex, "run_compile", run_compile)
    monkeypatch.setattr(review_latex, "page_count", lambda _path: next(pages))
    shrink = Mock(side_effect=lambda model: model)
    grow = Mock(side_effect=lambda model: model)

    result = review_latex.compile_review(_MODEL, tmp_path, shrink, grow)

    assert result["status"] == "ok"
    assert result["pages"] == 1
    assert "final page count 1" in result["warning"]
    assert run_compile.call_count == review_latex.PAGE_RETRY_BUDGET
    assert shrink.call_count == 1
    assert grow.call_count == 1
    _assert_final_artifacts(tmp_path)


def test_compile_review_returns_compile_error_without_publishing(tmp_path, monkeypatch) -> None:
    """A compile error is returned unchanged and cannot publish partial artifacts."""
    error = {"status": "error", "error": "CalledProcessError", "log_tail": "fatal"}
    run_compile = Mock(return_value=error)
    monkeypatch.setattr(review_latex, "run_compile", run_compile)
    page_count = Mock()
    monkeypatch.setattr(review_latex, "page_count", page_count)
    shrink = Mock()
    grow = Mock()

    result = review_latex.compile_review(_MODEL, tmp_path, shrink, grow)

    assert result == error
    assert run_compile.call_count == 1
    assert not page_count.called
    assert not shrink.called
    assert not grow.called
    assert list(tmp_path.iterdir()) == []

