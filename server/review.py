"""Review stages share one sequencing boundary to prevent out-of-order artifact publication."""

import contextlib
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path

import review_integrity
import review_latex
import review_synthesis

# ponytail: configurable review output root, add a config key when cwd is insufficient.


def _slug(query) -> str:
    """Why: archived topics need portable names across filesystems."""
    value = re.sub(r"[^a-z0-9]+", "-", str(query).lower()).strip("-")
    return value[:80] or "review"


def _timestamp() -> str:
    """Why: local timestamps make run archives sortable by creation time."""
    return datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")


def _output_directory(out_root, query) -> Path:
    """Why: collision checks prevent one-second repeat runs from overwriting evidence."""
    root = Path(out_root) / "reviews"
    base = root / f"{_slug(query)}-{_timestamp()}"
    candidate = base
    suffix = 2
    while candidate.exists():
        candidate = root / f"{base.name}-{suffix}"
        suffix += 1
    return candidate


def _atomic_write(destination: Path, content: str) -> None:
    """Why: temporary publication prevents callers from observing a partial guide."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{destination.name}.", dir=destination.parent
    )
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
    except Exception:
        with contextlib.suppress(OSError):
            os.close(descriptor)
        with contextlib.suppress(OSError):
            os.unlink(temporary)
        raise


def _guide_pool_lines(model) -> str:
    """Why: conduct counts let agents audit the bounded source scope."""
    pools = model.get("conduct", {}).get("source_pools", {})
    if not isinstance(pools, dict) or not pools:
        return "- none recorded"
    return "\n".join(f"- {pool}: {count} hit(s)" for pool, count in pools.items())


def _guide_theme_names(model) -> str:
    """Why: emitted themes must match the run's synthesis model."""
    themes = model.get("analysis", {})
    names = themes.keys() if isinstance(themes, dict) else []
    return ", ".join(str(theme) for theme in names) or "none recorded"


def _guide_page_outcome(integrity_summary) -> str:
    """Why: page warnings must stay visible beside the selected artifact."""
    pages = integrity_summary.get("pages", "unknown")
    bound = f"{review_latex.PAGE_MIN}-{review_latex.PAGE_MAX} pages"
    outcome = f"The compiled artifact contains {pages} page(s); target bound: {bound}."
    warning = integrity_summary.get("warning")
    return f"{outcome} Warning: {warning}" if warning else outcome


def _guide_content(model, integrity_summary) -> str:
    """Why: the companion guide avoids parsing binary output for method evidence."""
    design = model.get("design", {})
    question = design.get("question") or model.get("question", "not recorded")
    classification = design.get("classification", "Rapid Review")
    source_count = len(model.get("bib", []))
    return (
        "# Review methodology\n\n"
        "## Classification\n\n"
        f"{classification} Grant & Booth (2009) frame this as a time-constrained review "
        "with limited appraisal and narrative or tabular synthesis, not a Systematic Review.\n\n"
        "## Snyder phases\n\n"
        f"### Design\n\nQuestion: {question}\n\n"
        "### Conduct\n\nSource pools and ranked hit counts:\n"
        f"{_guide_pool_lines(model)}\n\n"
        f"### Analysis\n\nThemes: {_guide_theme_names(model)}\n\n"
        f"### Write-up\n\n{source_count} source(s) remained cited. {_guide_page_outcome(integrity_summary)}\n\n"
        "## Integrity check\n\n"
        f"Status: {integrity_summary.get('status', 'unknown')}. Claims are compared with their "
        f"attributed source text. Word ratio threshold: {review_integrity.WORD_RATIO_THRESHOLD}; "
        f"longest matching block threshold: {review_integrity.LONGEST_BLOCK_WORDS} words; "
        f"optional embedding cosine threshold: {review_integrity.EMBEDDING_COSINE_THRESHOLD}. "
        "Flagged claims are dropped and checked again before compilation.\n"
    )



def write_methodology_guide(model, integrity_summary, out_dir) -> str:
    """Why: agents need method details beside the PDF instead of parsing binary output."""
    destination = Path(out_dir) / "methodology.md"
    _atomic_write(destination, _guide_content(model, integrity_summary))
    return str(destination)


def _floor_result(flags) -> dict:
    """Why: the final batch must explain why flagged prose could not ship."""
    return {"status": "error", "error": "IntegrityFloor", "flags": list(flags)}


def _integrity_loop(model) -> tuple[dict, dict]:
    """Why: compilation is safe only after every completed check reports a clean model."""
    # Invariant: clean claims only, variant: claim count decreases after flags.
    while True:
        claims = review_synthesis.claims_for_integrity(model)
        integrity_summary = review_integrity.check_claims(claims)
        if integrity_summary.get("status") == "pass":
            return model, integrity_summary
        if integrity_summary.get("status") != "flagged":
            return integrity_summary, integrity_summary
        flags = list(integrity_summary.get("flags", []))
        next_model = review_synthesis.drop_flagged(model, flags)
        if next_model.get("status") != "ok":
            return _floor_result(flags), integrity_summary
        if len(next_model.get("claims", [])) >= len(model.get("claims", [])):
            return _floor_result(flags), integrity_summary
        model = next_model


def _review_response(model, compiled, guide_path) -> dict:
    """Why: stable keys let human and JSON callers archive the same run."""
    response = {
        "status": "ok",
        "pdf_path": compiled["pdf_path"],
        "tex_path": compiled["tex_path"],
        "guide_path": guide_path,
        "pages": compiled["pages"],
        "themes": list(model.get("analysis", {})),
        "sources_cited": len(model.get("bib", [])),
    }
    if compiled.get("warning"):
        response["warning"] = compiled["warning"]
    return response


def generate_review(query, hits, alternatives, out_root) -> dict:
    """Why: compilation must follow the integrity gate to keep finalized artifacts clean."""
    model = review_synthesis.build_model(query, hits, alternatives)
    if model.get("status") != "ok":
        return model
    model, integrity_summary = _integrity_loop(model)
    if model.get("status") != "ok":
        return model

    out_dir = _output_directory(out_root, query)
    out_dir.mkdir(parents=True, exist_ok=True)
    compiled = review_latex.compile_review(
        model, out_dir, review_synthesis.shrink, review_synthesis.grow
    )
    if compiled.get("status") != "ok":
        return compiled
    guide_data = dict(integrity_summary)
    guide_data.update({key: compiled[key] for key in ("pages", "warning") if key in compiled})
    guide_path = write_methodology_guide(model, guide_data, out_dir)
    return _review_response(model, compiled, guide_path)
