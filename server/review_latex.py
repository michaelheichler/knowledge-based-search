"""Local LaTeX boundary; contract: raw title/question, cited Snyder prose, bib records, year counts, extracted formulas."""

import re
import subprocess
from pathlib import Path

from pypdf import PdfReader

_COMPILE_TIMEOUT = 120.0
_PDFLATEX = ("pdflatex", "-interaction=nonstopmode", "-halt-on-error")
_CITATION = re.compile(r"\\cite[pt]\{([^{}]+)\}")
_LATEX_ESCAPES = {
    "\\": r"\textbackslash{}",
    "%": r"\%",
    "&": r"\&",
    "_": r"\_",
    "#": r"\#",
    "$": r"\$",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def _escape_raw(value) -> str:
    return "".join(_LATEX_ESCAPES.get(char, char) for char in str(value))


def _escape_prose(value) -> str:
    text = str(value)
    parts = []
    cursor = 0
    for marker in _CITATION.finditer(text):
        parts.append(_escape_raw(text[cursor : marker.start()]))
        parts.append(marker.group(0))
        cursor = marker.end()
    parts.append(_escape_raw(text[cursor:]))
    return "".join(parts)


def _render_prose(value) -> str:
    if isinstance(value, dict):
        return "\n\n".join(
            f"\\subsection{{{_escape_raw(theme)}}}\n{_render_prose(prose)}"
            for theme, prose in value.items()
        )
    if isinstance(value, (list, tuple)):
        return "\n\n".join(_render_prose(item) for item in value)
    return _escape_prose(value or "")


def _section_blocks(model) -> str:
    sections = (
        ("Design", model.get("design", "")),
        ("Conduct", model.get("conduct", "")),
        ("Analysis", model.get("analysis", "")),
        ("Write-up", model.get("write_up", model.get("write-up", ""))),
    )
    return "\n\n".join(
        f"\\section{{{title}}}\n{_render_prose(content)}"
        for title, content in sections
    )


def _citation_keys(text) -> set[str]:
    return {
        key.strip()
        for marker in _CITATION.finditer(text)
        for key in marker.group(1).split(",")
        if key.strip()
    }


def _validate_citations(body, entries) -> None:
    bib_keys = {entry.get("key", "") for entry in entries}
    cited_keys = _citation_keys(body)
    missing = sorted(key for key in bib_keys if key and key not in cited_keys)
    unknown = sorted(key for key in cited_keys if key not in bib_keys)
    problems = []
    if missing:
        problems.append(f"uncited bibliography entries: {', '.join(missing)}")
    if unknown:
        problems.append(f"unknown citation keys: {', '.join(unknown)}")
    if problems:
        raise ValueError("; ".join(problems))


def _chart_fragment(chart) -> str:
    if not chart:
        return ""
    pairs = list(chart.items()) if isinstance(chart, dict) else list(chart)
    pairs.sort(key=lambda pair: str(pair[0]))
    years = ",".join(str(year) for year, _ in pairs)
    coordinates = " ".join(f"({year},{count})" for year, count in pairs)
    return f"""\\begin{{figure}}[htbp]
\\centering
\\begin{{tikzpicture}}
\\begin{{axis}}[ybar,symbolic x coords={{{years}}},xtick=data]
\\addplot coordinates {{{coordinates}}};
\\end{{axis}}
\\end{{tikzpicture}}
\\caption{{Publication-year distribution from the supplied source metadata.}}
\\end{{figure}}"""


def _formula_fragment(formulas) -> str:
    return "\n\n".join(
        f"\\begin{{equation*}}\n{formula}\n\\end{{equation*}}"
        for formula in formulas or []
    )


def _document_source(model, body, extras) -> str:
    return f"""\\documentclass[11pt]{{article}}
\\usepackage[a4paper,margin=1in]{{geometry}}
\\usepackage{{natbib}}
\\usepackage{{url}}
\\usepackage{{tikz}}
\\usepackage{{pgfplots}}
\\usepackage{{amsmath}}
\\pgfplotsset{{compat=1.18}}
\\title{{{_escape_raw(model.get("title", ""))}}}
\\date{{}}
\\begin{{document}}
\\maketitle
\\textbf{{Research question.}} {_escape_raw(model.get("question", ""))}

{body}

{extras}

\\bibliographystyle{{agsm}}
\\bibliography{{review}}
\\end{{document}}
"""


def render_tex(model) -> str:
    """Render the contracted review model into a compilable source artifact."""
    entries = model.get("bib", [])
    body = _section_blocks(model)
    _validate_citations(body, entries)
    extras = "\n\n".join(
        part
        for part in (
            _formula_fragment(model.get("formulas", [])),
            _chart_fragment(model.get("chart", {})),
        )
        if part
    )
    return _document_source(model, body, extras)




def render_bib(model) -> str:
    """Keep bibliography metadata compatible with the agsm style."""
    rendered = []
    for entry in model.get("bib", []):
        key = entry.get("key")
        if not key:
            raise ValueError("every bibliography entry needs a key")
        authors = entry.get("authors", entry.get("author", ""))
        if isinstance(authors, (list, tuple)):
            authors = " and ".join(str(author) for author in authors)
        venue = entry.get("venue", entry.get("journal", ""))
        fields = [
            f"  author = {{{_escape_raw(authors)}}},",
            f"  title = {{{_escape_raw(entry.get('title', ''))}}},",
            f"  journal = {{{_escape_raw(venue)}}},",
            f"  year = {{{_escape_raw(entry.get('year', ''))}}}",
        ]
        if entry.get("url"):
            fields.append(f"  url = {{{_escape_raw(entry['url'])}}}")
        rendered.append("@article{" + str(key) + ",\n" + "\n".join(fields) + "\n}")
    return "\n\n".join(rendered) + ("\n" if rendered else "")


def run_compile(tex_dir, jobname) -> dict:
    """A separate BibTeX pass stabilizes citations before artifacts are returned."""
    directory = Path(tex_dir)
    commands = (
        [*_PDFLATEX, f"{jobname}.tex"],
        ["bibtex", jobname],
        [*_PDFLATEX, f"{jobname}.tex"],
        [*_PDFLATEX, f"{jobname}.tex"],
    )
    options = {"cwd": directory, "capture_output": True, "text": True, "timeout": _COMPILE_TIMEOUT}
    try:
        for command in commands:
            subprocess.run(command, check=True, **options)
    except (OSError, subprocess.SubprocessError) as exc:
        result = {"status": "error", "error": type(exc).__name__}
        log_path = directory / f"{jobname}.log"
        try:
            result["log_tail"] = "\n".join(
                log_path.read_text(encoding="utf-8", errors="replace").splitlines()[-40:]
            )
        except OSError:
            pass
        return result
    return {"status": "ok", "pdf_path": str(directory / f"{jobname}.pdf")}


def page_count(pdf_path) -> int:
    """pypdf avoids a second external process for page-bound checks."""
    return len(PdfReader(pdf_path).pages)
