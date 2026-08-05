"""Review stages share one sequencing boundary to prevent out-of-order artifact publication."""

import contextlib
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

import review_integrity
import review_latex
import review_synthesis
import trust

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


_GUIDE_POOL_DOMAINS = {
    "arxiv": "arxiv.org",
    "pubmed": "ncbi.nlm.nih.gov",
    "semanticscholar": "semanticscholar.org",
    "crossref": "crossref.org",
}


def _guide_source_pools(model) -> dict:
    """Why: raw pool counts stay available after Conduct is flattened for LaTeX."""
    pools = model.get("source_pools")
    if not isinstance(pools, dict):
        pools = model.get("conduct", {}).get("source_pools", {})
    return pools if isinstance(pools, dict) else {}


def _guide_pool_lines(model) -> str:
    """Why: connected pool sentences let agents audit the bounded source scope."""
    pools = _guide_source_pools(model)
    if pools:
        details = []
        for pool, count in pools.items():
            unit = "hit" if str(count) == "1" else "hits"
            details.append(f"{pool} ({count} ranked {unit})")
        return ", ".join(details)
    scope = model.get("search_scope")
    if isinstance(scope, dict) and scope:
        return ", ".join(str(value).rstrip(".") for value in scope.values())
    return "no source pools were recorded"


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


def _guide_pool_domain(model, pool) -> str:
    """Why: provider names need their configured domain before trust lookup."""
    pool_name = str(pool).lower()
    if pool_name in _GUIDE_POOL_DOMAINS:
        return _GUIDE_POOL_DOMAINS[pool_name]
    entries = model.get("_bibliography_pool", model.get("bib", []))
    if not isinstance(entries, list):
        return ""
    for entry in entries:
        source_id = str(entry.get("source_id") or "").lower()
        if source_id.startswith(f"{pool_name}:"):
            hostname = (urlsplit(str(entry.get("url") or "")).hostname or "").lower()
            return hostname.removeprefix("www.")
    return ""


def _guide_configured_score(data, domain) -> int | None:
    """Why: methodology reports the fixed score, not the ranking bonus."""
    if not domain:
        return None
    categories = data.get("categories", {})
    science = categories.get("science", {}) if isinstance(categories, dict) else {}
    if domain in science:
        return science[domain]
    for scores in categories.values() if isinstance(categories, dict) else []:
        if isinstance(scores, dict) and domain in scores:
            return scores[domain]
    return None


def _guide_trust_lines(model) -> str:
    """Why: each present pool must expose the trust configuration used for appraisal."""
    pools = _guide_source_pools(model)
    if not pools:
        return "no source-pool trust tiers were recorded"
    data = trust._trust_data()
    lines = []
    for pool in pools:
        pool_name = str(pool)
        if pool_name.lower() == "library":
            lines.append("library: 95")
            continue
        domain = _guide_pool_domain(model, pool_name)
        score = _guide_configured_score(data, domain)
        label = domain or pool_name
        if pool_name.lower() == "pubmed" and domain:
            label = f"{domain} ({pool_name})"
        lines.append(f"{label}: {score if score is not None else 'not configured'}")
    return ", ".join(lines)


def _guide_alternatives(model) -> str:
    """Why: agents need explicit terminology choices even when the list is empty."""
    alternatives = model.get("terminology_alternatives", [])
    if not isinstance(alternatives, list) or not alternatives:
        return "No terminology alternatives were surfaced for this query."
    lines = []
    for index, item in enumerate(alternatives, 1):
        if not isinstance(item, dict):
            item = {}
        note = item.get("note", "")
        suffix = f" ({note})" if note else ""
        lines.append(f"  {index}. {item.get('term', '')}{suffix}")
    return "\n".join(lines)


def _guide_conduct(model) -> str:
    """Why: source scope and appraisal need connected sentences for agent handoff."""
    return (
        "## Conduct\n\n"
        "### Search scope and source selection\n\n"
        "This review searched the following source pools, combining relevance rank and "
        "recency rank on every query, no mode strips either signal: "
        f"{_guide_pool_lines(model)}. Source selection is bounded by kbs's existing keyless "
        "provider allowlist. No additional database or paywalled source was queried.\n\n"
        "### Quality and trust appraisal\n\n"
        "Each source pool carries a fixed trust tier from kbs's trust configuration "
        f"(`server/data/trust.json`): {_guide_trust_lines(model)}. Library hits carry a fixed "
        "tier of 95 with no domain to score. Per-paper ranking additionally weighs citation "
        "count where the provider exposes it (Semantic Scholar, CrossRef) and query-term "
        "alignment.\n\n"
        "### Terminology alternatives considered\n\n"
        f"{_guide_alternatives(model)}"
    )


def _guide_analysis(model) -> str:
    """Why: synthesis ownership must remain explicit at the agent boundary."""
    return (
        "## Analysis\n\n"
        f"Themes identified: {_guide_theme_names(model)}. Each theme's evidence is presented "
        "as directly quoted, cited excerpts. The connecting synthesis sentence per theme is "
        "delegated to the calling agent to write via the `% AGENT-SYNTHESIS` markers in "
        "review.tex. kbs does not paraphrase or fabricate synthesis prose."
    )


def _guide_integrity(integrity_summary) -> str:
    """Why: the guide names both attribution and citation completeness guarantees."""
    return (
        "## Integrity check\n\n"
        f"Status: {integrity_summary.get('status', 'unknown')}. `check_quotes` verifies every "
        "quoted excerpt to exactly match a sentence in its attributed, retrieved source text "
        "before finalization, guarding against fabrication or misattribution. "
        "`review_latex._validate_citations` verifies citation completeness bidirectionally. "
        "Every bibliography entry is cited in the body and every citation key resolves to a "
        "bibliography entry."
    )


def _guide_classification(model) -> str:
    """Why: the classification keeps the review type beside its framing."""
    classification = model.get("design", {}).get("classification", "Rapid Review")
    return (
        "## Classification\n\n"
        f"{classification} Grant & Booth (2009) frame this as a time-constrained review "
        "with limited appraisal and narrative or tabular synthesis, not a Systematic Review."
    )


def _guide_design(model) -> str:
    """Why: the research question anchors every run-specific method statement."""
    design = model.get("design", {})
    question = design.get("question") or model.get("question", "not recorded")
    return f"## Design\n\nResearch question: {question}"


def _guide_write_up(model, integrity_summary) -> str:
    """Why: source and page outcomes stay tied to the finalized artifact."""
    source_count = len(model.get("bib", []))
    return (
        f"## Write-up\n\n{source_count} source(s) remained cited. "
        f"{_guide_page_outcome(integrity_summary)}"
    )


def _guide_limitations() -> str:
    """Why: only run-specific judgment belongs to the downstream agent."""
    return (
        "## Limitations\n\n"
        "[AGENT: describe the limitations of this specific run's search scope and evidence "
        "coverage, for example thin themes, provider gaps, or terms not tried. kbs does not "
        "narrate this itself. It is real judgment about this run, not a templated disclaimer.]"
    )


def _guide_content(model, integrity_summary) -> str:
    """Why: the companion guide narrates method evidence without generating prose."""
    sections = [
        "# Review methodology",
        _guide_classification(model),
        _guide_design(model),
        _guide_conduct(model),
        _guide_analysis(model),
        _guide_write_up(model, integrity_summary),
        _guide_integrity(integrity_summary),
        _guide_limitations(),
    ]
    return "\n\n".join(sections) + "\n"



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
    # Invariant: only attributable quotes reach compilation. Variant: model items decrease after flags.
    while True:
        quotes = review_synthesis.quotes_for_integrity(model)
        integrity_summary = review_integrity.check_quotes(quotes)
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
