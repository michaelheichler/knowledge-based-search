"""Review synthesis boundary for ranked literature hits."""

import re
from collections import defaultdict
from urllib.parse import urlsplit

import trust

THEME_CAP = 5
RELATED_THEME = "related work"
# ponytail: deterministic templates, add local-LLM drafting when REQ-18 is adopted.


def _normalise_theme(value) -> str:
    """Required because adapter labels otherwise create duplicate sections."""
    return re.sub(r"\s+", " ", str(value).strip().lower()) or RELATED_THEME


def _category_values(value) -> list:
    """Required because scalar metadata must not be iterated as characters."""
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, (list, tuple)):
        return [item for item in value if str(item).strip()]
    return []


def group_themes(hits, query=None, query_category=None) -> dict:
    """Required because singleton suppression prevents source-by-source prose."""
    fallback = query_category or trust.query_category(query or "") or RELATED_THEME
    grouped = defaultdict(list)
    for hit in hits:
        categories = _category_values(hit.get("categories"))
        grouped[_normalise_theme(categories[0] if categories else fallback)].append(hit)

    related = grouped.pop(RELATED_THEME, [])
    for theme in list(grouped):
        if len(grouped[theme]) == 1:
            related.extend(grouped.pop(theme))
    if related:
        grouped[RELATED_THEME].extend(related)

    if len(grouped) <= THEME_CAP:
        return dict(grouped)
    named = [(theme, items) for theme, items in grouped.items() if theme != RELATED_THEME]
    retained = named[: THEME_CAP - 1]
    overflow = [items for _, items in named[THEME_CAP - 1 :]]
    overflow.extend([grouped[RELATED_THEME]] if RELATED_THEME in grouped else [])
    related_items = [hit for items in overflow for hit in items]
    result = dict(retained)
    if related_items:
        result[RELATED_THEME] = related_items
    return result


def _parse_year(value) -> str:
    """Required because missing dates cannot support fabricated chart points."""
    match = re.search(r"\b(?:19|20)\d{2}\b", str(value or ""))
    return match.group(0) if match else ""


def _author_value(hit) -> object:
    """Required because agsm needs the original author field."""
    return hit.get("authors") or hit.get("author") or ""


def _author_slug(authors) -> str:
    """Required because citation keys must not vary across runs."""
    if isinstance(authors, (list, tuple)):
        authors = authors[0] if authors else ""
    if isinstance(authors, dict):
        authors = authors.get("family") or authors.get("name") or ""
    text = str(authors or "").strip()
    if "," in text:
        text = text.split(",", 1)[0]
    else:
        text = text.split()[-1] if text.split() else ""
    return re.sub(r"[^a-z0-9]", "", text.lower())


def _domain_slug(url) -> str:
    """Required because an authorless source still needs a stable citation key."""
    host = urlsplit(str(url or "")).hostname or ""
    labels = [label for label in host.lower().split(".") if label]
    name = labels[-2] if len(labels) > 1 else (labels[0] if labels else "source")
    return re.sub(r"[^a-z0-9]", "", name)


def _citation_key(hit, used) -> str:
    """Required because duplicate metadata must not discard a source."""
    base = _author_slug(_author_value(hit)) or _domain_slug(hit.get("url"))
    key = f"{base}{_parse_year(hit.get('date'))}"
    candidate = key
    suffix = 2
    while candidate in used:
        candidate = f"{key}_{suffix}"
        suffix += 1
    used.add(candidate)
    return candidate


def _venue(hit) -> str:
    """Required because missing journals should not erase provider provenance."""
    venue = hit.get("venue") or hit.get("journal")
    engines = hit.get("engines") or hit.get("engine") or ""
    if not venue and isinstance(engines, (list, tuple)):
        venue = engines[0] if engines else ""
    return str(venue or engines or "")


def build_bibliography(hits) -> list:
    """Required because only chart data, not citations, needs publication years."""
    used = set()
    entries = []
    for hit in hits:
        entries.append(
            {
                "key": _citation_key(hit, used),
                "source_id": hit.get("source_id") or hit.get("url") or "",
                "authors": _author_value(hit),
                "year": _parse_year(hit.get("date")),
                "title": hit.get("title", ""),
                "venue": _venue(hit),
                "url": hit.get("url", ""),
            }
        )
    return entries
