"""Review synthesis boundary for ranked literature hits."""

import re
from collections import Counter, defaultdict
from urllib.parse import urlsplit

import library_engine
import review_integrity
import trust

FILLER_DENYLIST = (
    "it is worth noting",
    "in today's world",
    "it is important to note",
)
_REPORTING_VERBS = ("indicates", "associates", "describes", "supports")
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
_WORDS = re.compile(r"[a-z0-9]+")
_FORMULA_PATTERNS = (
    re.compile(r"\\begin\{(?:equation|equation\*|align|align\*)\}(.*?)\\end\{(?:equation|equation\*|align|align\*)\}", re.DOTALL),
    re.compile(r"\\\((.+?)\\\)|\\\[(.+?)\\\]", re.DOTALL),
    re.compile(
        r"(?<!\w)([A-Za-z]\s*=\s*[A-Za-z0-9_+*/^().-]+"
        r"(?:\s*[+*/^=-]\s*[A-Za-z0-9_().]+)*)(?=\s|[.,;!?]|$)"
    ),
)

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


def _source_text(hit) -> str:
    """Required because library claims need deeper text without losing their snippet fallback."""
    snippet = str(hit.get("snippet") or hit.get("source_text") or "")[:300]
    url = str(hit.get("url") or "")
    if not url.startswith("library://"):
        return str(hit.get("source_text") or hit.get("snippet") or "")
    try:
        payload = library_engine.get_passage_from_url(url)
    except (KeyError, OSError, RuntimeError, TypeError, ValueError):
        return snippet
    deep_text = payload.get("text") or payload.get("passage") or payload.get("content")
    return str(deep_text) if deep_text else snippet


def _sentences(text) -> list:
    """Required because integrity checks compare claims with source sentences."""
    parts = [part.strip() for part in _SENTENCE_SPLIT.split(text.strip()) if part.strip()]
    return parts or ([text.strip()] if text.strip() else [])


def _query_terms(query) -> set:
    """Required because term overlap favors sentences that answer the stated question."""
    return {word for word in _WORDS.findall(str(query or "").lower()) if len(word) > 2}


def _sentence_terms(sentence) -> set:
    """Required because punctuation must not affect informative-sentence scoring."""
    return set(_WORDS.findall(sentence.lower()))


def _select_sentence(text, query) -> str:
    """Required because one representative sentence keeps claims bounded and attributable."""
    sentences = _sentences(text)
    terms = _query_terms(query)
    ranked = sorted(
        enumerate(sentences),
        key=lambda pair: (
            -len(terms & _sentence_terms(pair[1])),
            -len(_WORDS.findall(pair[1])),
            pair[0],
        ),
    )
    return ranked[0][1] if ranked else ""


def _register(sentence) -> str:
    """Required because generated prose must not begin with filler openers."""
    result = sentence.strip()
    # Invariant: processed prefixes are absent from result. Variant: remaining denylist items.
    for filler in FILLER_DENYLIST:
        if result.lower().startswith(filler):
            result = result[len(filler) :].lstrip(" ,:;")
    return result[:1].upper() + result[1:]


def _reporting_frame(theme, source_sentence, key) -> str:
    """Required because a reporting frame changes copied source order and register."""
    words = source_sentence.rstrip(".!?").split()
    pivot = max(1, len(words) // 2)
    reordered = " ".join(words[pivot:] + words[:pivot])
    verb = _REPORTING_VERBS[len(words) % len(_REPORTING_VERBS)]
    citation = f"\\citep{{{key}}}"
    return _register(f"{str(theme).title()} evidence {verb} {reordered} {citation}.")


def _formula_value(match) -> str:
    """Required because unmatched groups must not become fabricated formulas."""
    return next((group for group in match.groups() if group), "").strip()


def _formula_values(matches) -> list:
    """Required because each regex shape contributes only its captured expression."""
    return [value for match in matches if (value := _formula_value(match))]


def _unique(values) -> list:
    """Required because repeated source formulas should render once."""
    return list(dict.fromkeys(values))


def _pattern_formulas(pattern, text) -> list:
    """Required because each formula pattern has one bounded extraction pass."""
    return _formula_values(pattern.finditer(text))


def _formula_matches(text) -> list:
    """Required because formulas must be copied from retrieved source text."""
    values = []
    for pattern in _FORMULA_PATTERNS:
        values.extend(_pattern_formulas(pattern, text))
    return _unique(values)


def build_claims(themes, query="", bibliography=None) -> list:
    """Required because every emitted sentence must retain one source attribution."""
    grouped = themes.items() if hasattr(themes, "items") else [(RELATED_THEME, themes)]
    flattened = [(theme, hit) for theme, hits in grouped for hit in hits]
    entries = list(bibliography or build_bibliography([hit for _, hit in flattened]))
    claims = []
    for ordinal, ((theme, hit), entry) in enumerate(zip(flattened, entries)):
        source_text = _source_text(hit)
        source_sentence = _select_sentence(source_text, query)
        if not source_sentence:
            continue
        claims.append(
            {
                "claim_sentence": _reporting_frame(theme, source_sentence, entry["key"]),
                "source_id": hit.get("source_id") or hit.get("url") or "",
                "source_text": source_text,
                "citation_key": entry["key"],
                "theme": _normalise_theme(theme),
                "rank": ordinal,
            }
        )
    return claims


def formulas_from_hits(hits) -> list:
    """Required because formula-free sources must produce no equation candidate."""
    formulas = []
    for hit in hits:
        formulas.extend(_formula_matches(_source_text(hit)))
    return _unique(formulas)


def chart_from_bibliography(bibliography) -> dict:
    """Required because chart counts must come only from real bibliography years."""
    counts = Counter(
        str(entry.get("year"))
        for entry in bibliography
        if re.fullmatch(r"(?:19|20)\d{2}", str(entry.get("year") or ""))
    )
    return dict(sorted(counts.items()))


def integrity_result(claims) -> dict:
    """Required because the synthesis boundary exposes the existing fail-closed gate."""
    return review_integrity.check_claims(claims)

