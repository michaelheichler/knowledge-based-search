"""Local LaTeX compilation boundary for literature reviews."""

import subprocess
from pathlib import Path

from pypdf import PdfReader

_COMPILE_TIMEOUT = 120.0
_PDFLATEX = ("pdflatex", "-interaction=nonstopmode", "-halt-on-error")


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
