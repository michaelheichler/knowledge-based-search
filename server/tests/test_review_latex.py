"""Validate the local LaTeX and BibTeX boundary used by review generation."""

import shutil
from pathlib import Path

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

