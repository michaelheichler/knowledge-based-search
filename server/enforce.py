"""Reference-book rules stay centralized so every correction remains auditable."""

from __future__ import annotations

import json
import os
import re
from collections import Counter
from collections.abc import Iterable, Mapping
from pathlib import Path
from urllib.parse import urlsplit

Correction = dict[str, str]

_QUERY_TOKEN = re.compile(r'"[^"\n]*"|\([^()]*\)|\S+')
_EMAIL = re.compile(r'(?<![\w."])\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b(?!")')
_TITLE_RUN = re.compile(r"\b(?:[A-Z][\w'.-]*)(?:\s+[A-Z][\w'.-]*)+\b")
_WORD = re.compile(r"[^\W\d_][\w'.-]*", re.UNICODE)
_ERROR_QUERY = re.compile(
    r"(?:\b[A-Za-z][A-Za-z0-9_.]*(?:Error|Exception)\b:|\b(?:Cannot Read Property|Not Found|Undefined)\b)",
    re.IGNORECASE,
)
_OPERATOR = re.compile(
    r"^-?(?:site|filetype|intitle|inurl|intext|before|after|source|related|cache):",
    re.IGNORECASE,
)
_OPERATOR_ANYWHERE = re.compile(
    r"(?:^|\s|\() -?(?:site|filetype|intitle|inurl|intext|before|after|source|related|cache):",
    re.IGNORECASE | re.VERBOSE,
)
_FILETYPE = re.compile(
    r"^(?P<negative>-?)filetype:(?P<extension>[a-z0-9]+)$", re.IGNORECASE
)
_FILETYPE_FAMILIES = {
    "doc": ("doc", "docx"),
    "docx": ("doc", "docx"),
    "xls": ("xls", "xlsx", "csv"),
    "xlsx": ("xls", "xlsx", "csv"),
    "csv": ("xls", "xlsx", "csv"),
    "ppt": ("ppt", "pptx"),
    "pptx": ("ppt", "pptx"),
    "odt": ("odt", "ods", "odp"),
    "ods": ("odt", "ods", "odp"),
    "odp": ("odt", "ods", "odp"),
    "zip": ("zip", "rar", "7z"),
    "rar": ("zip", "rar", "7z"),
    "7z": ("zip", "rar", "7z"),
}
_STOPWORDS = {
    "a",
    "about",
    "an",
    "and",
    "are",
    "be",
    "can",
    "could",
    "do",
    "does",
    "for",
    "find",
    "give",
    "help",
    "how",
    "i",
    "information",
    "is",
    "it",
    "look",
    "looking",
    "me",
    "of",
    "on",
    "please",
    "search",
    "show",
    "tell",
    "that",
    "the",
    "to",
    "us",
    "want",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "would",
    "you",
}
_FRAME_WORDS = _STOPWORDS | {"need", "trying"}
_GENERIC_TITLE_WORDS = {
    "current",
    "data",
    "document",
    "documents",
    "guide",
    "latest",
    "recent",
    "report",
    "reports",
}
_QUERY_VERBS = {
    "can",
    "could",
    "find",
    "give",
    "help",
    "how",
    "please",
    "search",
    "show",
    "tell",
    "what",
    "where",
    "who",
    "would",
}
_TITLE_BREAK_WORDS = (
    _FRAME_WORDS
    | _GENERIC_TITLE_WORDS
    | {
        "address",
        "email",
        "facebook",
        "github",
        "linkedin",
        "profile",
        "twitter",
    }
)
_GENERIC_EVIDENCE_TERMS = _STOPWORDS | {
    "annual",
    "document",
    "paper",
    "publication",
    "report",
    "reports",
    "study",
}
_PRIMARY_SUFFIXES = (
    ".ac.uk",
    ".ac.nz",
    ".edu",
    ".edu.au",
    ".gc.ca",
    ".go.jp",
    ".go.kr",
    ".gouv.fr",
    ".gov",
    ".gov.au",
    ".gov.uk",
    ".govt.nz",
    ".int",
    ".mil",
)
_PRIMARY_DOMAINS = {"sec.gov", "clinicaltrials.gov", "europa.eu", "data.europa.eu"}
_STANDARD_DOMAINS = {
    "apnews.com",
    "bbc.com",
    "developer.mozilla.org",
    "docs.python.org",
    "github.com",
    "nature.com",
    "nytimes.com",
    "reuters.com",
    "science.org",
    "wsj.com",
}
_WEAK_DOMAINS = {
    "crunchbase.com",
    "medium.com",
    "pinterest.com",
    "rocketreach.co",
    "stackshare.io",
    "substack.com",
    "zoominfo.com",
}
_WEAK_DOMAIN_MARKERS = ("aggregator", "best-", "reviews", "seo", "top10")
_COUNTRY_SECOND_LEVELS = {"ac", "co", "com", "edu", "gov", "net", "org"}
_PRIVATE_SUFFIXES = {
    "appspot.com",
    "github.io",
    "netlify.app",
    "pages.dev",
    "vercel.app",
}
_QUALITY_DOWNWEIGHT = re.compile(
    r"\b(?:press release|sponsored|self-published|pre-?print|working paper)\b",
    re.IGNORECASE,
)
_TRUST_PATH = Path(__file__).with_name("data") / "trust.json"
_TRUST_CACHE: tuple[int, dict] | None = None
_CATEGORY_KEYWORDS = {
    "science": {
        "study",
        "paper",
        "research",
        "arxiv",
        "quantum",
        "physics",
        "biology",
        "chemistry",
    },
    "tech": {
        "ram",
        "gpu",
        "cpu",
        "chip",
        "dram",
        "ssd",
        "semiconductor",
        "nvidia",
        "amd",
        "intel",
        "linux",
        "kernel",
        "software",
        "hardware",
        "api",
    },
    "health": {"vaccine", "drug", "disease", "clinical", "therapy", "symptom"},
    "finance": {"stock", "inflation", "earnings", "interest rate", "etf", "bond"},
    "reference": {
        "documentation",
        "docs",
        "rfc",
        "spec",
        "standard",
        "syntax",
        "w3c",
        "html",
        "css",
    },
}


def enforcement_disabled(raw: bool = False) -> bool:
    """Return whether the caller explicitly requested a literal query."""
    value = os.environ.get("KBS_NO_ENFORCE", "").strip().lower()
    return raw or value in {"1", "true", "yes", "on"}


def enforce_query(query, context=None) -> tuple:
    """Rewrite a query with only the cited reference-book rules."""
    rewritten = str(query).strip()
    corrections: list[Correction] = []
    rewritten = _quote_context_segments(rewritten, context, corrections)
    rewritten = _quote_emails(rewritten, corrections)
    rewritten = _quote_proper_nouns(rewritten, corrections)
    rewritten = _expand_filetypes(rewritten, corrections)
    rewritten = _compress_agent_query(rewritten, corrections)
    return rewritten, corrections


def strip_quotes(query: str) -> str:
    """Relax exact phrases for a zero-result retry."""
    return re.sub(r'"([^"\n]+)"', r"\1", query).strip()


def wildcard_phrases(query: str) -> str:
    """Insert one search wildcard into each brittle multi-token phrase."""

    def add_wildcard(match: re.Match[str]) -> str:
        words = match.group(1).split()
        if len(words) < 2 or "*" in words:
            return match.group(0)
        return '"' + " * ".join(words) + '"'

    return re.sub(r'"([^"\n]+)"', add_wildcard, query)


def reorder_operators(query: str) -> str:
    """Move advanced operators once while preserving their literal text."""
    tokens = _QUERY_TOKEN.findall(query)
    operators = [token for token in tokens if _is_operator(token)]
    terms = [token for token in tokens if not _is_operator(token)]
    if len(operators) < 2 or not terms:
        return query
    if tokens[: len(operators)] == operators:
        reordered = terms + operators
    else:
        reordered = operators + terms
    return " ".join(reordered)


def operator_count(query: str) -> int:
    """Count advanced operators without interpreting their values."""
    return len(_OPERATOR_ANYWHERE.findall(" " + query))


def negation_retry(query: str, hits: Iterable[Mapping[str, object]]) -> str:
    """Add the most frequent irrelevant snippet term to a noisy query."""
    query_terms = _meaningful_terms(query)
    counts: Counter[str] = Counter()
    for hit in hits:
        text = str(hit.get("snippet", "")).lower()
        counts.update(
            term
            for term in re.findall(r"[a-z][a-z0-9-]{3,}", text)
            if term not in query_terms and term not in _STOPWORDS
        )
    for term, count in counts.most_common():
        if count >= 2 and f"-{term}" not in query.split():
            return f"{query} -{term}"
    return query


def results_are_noisy(query: str, hits: list[Mapping[str, object]]) -> bool:
    """Flag a large set whose snippets mostly miss every meaningful query term."""
    if len(hits) < 5:
        return False
    terms = _meaningful_terms(query)
    if not terms:
        return False
    relevant = 0
    for hit in hits:
        text = f"{hit.get('title', '')} {hit.get('snippet', '')}".lower()
        if any(term in text for term in terms):
            relevant += 1
    return relevant * 2 < len(hits)


def quality_gate(results, top_n=5) -> tuple:
    """Tag source tiers and summarize distinct-root-domain corroboration."""
    tagged = [_tag_source(item) for item in results]
    sample = tagged[: max(1, top_n)]
    domains = _result_domains(sample)
    supporting = _supporting_domains(sample)
    return tagged, {
        "distinct_root_domains": len(domains),
        "domain_metric": "approximate root domains",
        "supporting_root_domains": len(supporting),
        "low_diversity": bool(sample) and len(domains) <= 2,
        "verification": "corroborated" if len(supporting) >= 2 else "single-source",
        "reason": "lexical support, domain diversity, and source tiers (evaluate-evidence, ch55)",
    }


def _tag_source(item: Mapping[str, object]) -> dict:
    tagged = dict(item)
    url = str(tagged.get("url", ""))
    tagged["trust"] = trust_score(url)
    tagged["confidence"] = source_tier(url, tagged)
    return tagged


def _result_domains(results: Iterable[Mapping[str, object]]) -> set[str]:
    domains = {root_domain(str(item.get("url", ""))) for item in results}
    domains.discard("")
    return domains


def _supporting_domains(results: list[Mapping[str, object]]) -> set[str]:
    if not results:
        return set()
    top_terms = _evidence_terms(results[0])
    if not top_terms:
        return set()
    supported = {root_domain(str(results[0].get("url", "")))}
    for item in results[1:]:
        overlap = top_terms & _evidence_terms(item)
        if len(overlap) >= 2:
            supported.add(root_domain(str(item.get("url", ""))))
    supported.discard("")
    return supported


def _evidence_terms(item: Mapping[str, object]) -> set[str]:
    text = f"{item.get('title', '')} {item.get('snippet', '')}".lower()
    return {
        term
        for term in re.findall(r"[a-z][a-z0-9-]{3,}", text)
        if term not in _GENERIC_EVIDENCE_TERMS
    }


def _hostname(url: str) -> str:
    try:
        return (urlsplit(url).hostname or "").lower()
    except ValueError:
        return ""


def _trust_data() -> dict:
    global _TRUST_CACHE
    mtime = _TRUST_PATH.stat().st_mtime_ns
    if _TRUST_CACHE is None or _TRUST_CACHE[0] != mtime:
        _TRUST_CACHE = (
            mtime,
            json.loads(_TRUST_PATH.read_text(encoding="utf-8")),
        )
    return _TRUST_CACHE[1]


def query_category(query: str) -> str | None:
    """Infer a coarse topic from exact query keywords."""
    lowered = query.lower()
    tokens = set(re.findall(r"[a-z0-9]+", lowered))
    for category, keywords in _CATEGORY_KEYWORDS.items():
        if any(
            keyword in lowered if " " in keyword else keyword in tokens
            for keyword in keywords
        ):
            return category
    return None


def trust_score(url: str, category: str | None = None) -> int | None:
    """Return a maintained source score with an optional topic bonus."""
    data = _trust_data()
    domains = {_hostname(url).removeprefix("www."), root_domain(url)} - {""}
    categories = data["categories"]
    if category in categories:
        category_scores = [
            categories[category][domain]
            for domain in domains
            if domain in categories[category]
        ]
        if category_scores:
            return min(100, max(category_scores) + 10)
    scores = [
        scores[domain]
        for scores in [*categories.values(), data["news"]]
        for domain in domains
        if domain in scores
    ]
    return max(scores, default=None)


def trust_order(query: str, ranked: list) -> list:
    """Apply a bounded trust adjustment without replacing relevance ranking."""
    category = query_category(query)

    def adjusted_relevance(hit: Mapping[str, object]) -> float:
        score = trust_score(str(hit.get("url", "")), category)
        bonus = 0 if score is None else (score - 50) / 500
        return float(hit.get("relevance", 0) or 0) + bonus

    return sorted(ranked, key=adjusted_relevance, reverse=True)


def source_tier(url: str, item: Mapping[str, object] | None = None) -> str:
    """Classify a source with maintained scores and explicit overrides."""
    host = _hostname(url).removeprefix("www.")
    domain = root_domain(url)
    text = "" if item is None else f"{item.get('title', '')} {item.get('snippet', '')}"
    if _QUALITY_DOWNWEIGHT.search(text):
        return "weak"
    if domain in _PRIMARY_DOMAINS or host.endswith(_PRIMARY_SUFFIXES):
        return "primary"
    score = trust_score(url)
    if score is not None:
        if score >= 80:
            return "primary"
        if score >= 55:
            return "standard"
        return "weak"
    if host in _STANDARD_DOMAINS or domain in _STANDARD_DOMAINS:
        return "standard"
    if domain in _WEAK_DOMAINS or any(
        marker in domain for marker in _WEAK_DOMAIN_MARKERS
    ):
        return "weak"
    return "unknown"


def root_domain(url: str) -> str:
    """Return a cheap registrable-domain approximation for diversity checks."""
    host = _hostname(url).strip(".").removeprefix("www.")
    labels = host.split(".")
    if len(labels) <= 2:
        return host
    suffix = ".".join(labels[-2:])
    # ponytail: static suffix set, use a PSL package when one becomes a dependency
    country_suffix = len(labels[-1]) == 2 and labels[-2] in _COUNTRY_SECOND_LEVELS
    if suffix in _PRIVATE_SUFFIXES or country_suffix:
        return ".".join(labels[-3:])
    return suffix


def correction(kind: str, change: tuple[str, str], reason: str) -> Correction:
    """Build the stable public correction-trail shape."""
    before, after = change
    return {"kind": kind, "before": before, "after": after, "reason": reason}


def _record(corrections: list[Correction], item: Correction) -> str:
    if item["after"] != item["before"]:
        corrections.append(item)
    return item["after"]


def _quote_context_segments(
    query: str,
    context: Mapping[str, object] | None,
    corrections: list[Correction],
) -> str:
    before = query
    for segment in _context_segments(context):
        query = _quote_exact_segment(query, segment)
    item = correction(
        "quote-exact",
        (before, query),
        "auto-quoted exact phrase (osint-techniques ch24, osint-resources ch16)",
    )
    return _record(corrections, item)


def _context_segments(context: Mapping[str, object] | None) -> list[str]:
    if not context:
        return []
    values = [
        value
        for key in ("exact_segments", "proper_nouns")
        for value in _string_values(context.get(key, []))
    ]
    distinct = {item.strip() for item in values if item.strip()}
    return sorted(distinct, key=len, reverse=True)


def _string_values(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, Iterable):
        return [str(item) for item in value]
    return []


def _quote_exact_segment(query: str, segment: str) -> str:
    pattern = rf"(?<!\w){re.escape(segment)}(?!\w)"
    if len(segment.split()) < 2 or re.search(f'"{pattern}"', query, re.IGNORECASE):
        return query
    quoted = _quoted_ranges(query)

    def quote(match: re.Match[str]) -> str:
        if any(start <= match.start() < end for start, end in quoted):
            return match.group(0)
        return f'"{match.group(0)}"'

    return re.sub(pattern, quote, query, flags=re.IGNORECASE)


def _quote_emails(query: str, corrections: list[Correction]) -> str:
    before = query
    query = _EMAIL.sub(lambda match: f'"{match.group(0)}"', query)
    item = correction(
        "quote-email",
        (before, query),
        "auto-quoted exact email (osint-techniques ch24)",
    )
    return _record(corrections, item)


def _skip_title_quoting(query: str) -> bool:
    if _ERROR_QUERY.search(query):
        return True
    words = _WORD.findall(query)
    significant = [word for word in words if word.lower() not in _STOPWORDS]
    if not significant:
        return False
    framed = any(word.lower() in _QUERY_VERBS for word in words)
    title_case = sum(word[0].isupper() for word in significant)
    capitalized = title_case * 2 > len(significant)
    return capitalized and (not framed or len(significant) >= 5)


def _quote_proper_nouns(query: str, corrections: list[Correction]) -> str:
    if _skip_title_quoting(query):
        return query
    protected = _quoted_ranges(query)

    def quote(match: re.Match[str]) -> str:
        text = match.group(0)
        if any(start <= match.start() < end for start, end in protected):
            return text
        if any(word.lower() in _GENERIC_TITLE_WORDS for word in text.split()):
            return text
        return _render_title_run(text)

    before = query
    query = _TITLE_RUN.sub(quote, query)
    item = correction(
        "quote-proper-noun",
        (before, query),
        "auto-quoted proper noun (osint-techniques ch24, osint-resources ch16)",
    )
    return _record(corrections, item)


def _render_title_run(text: str) -> str:
    rendered: list[str] = []
    entity: list[str] = []
    for word in text.split():
        if word.lower() not in _TITLE_BREAK_WORDS:
            entity.append(word)
            continue
        _flush_entity(entity, rendered)
        rendered.append(word)
    _flush_entity(entity, rendered)
    return " ".join(rendered)


def _flush_entity(entity: list[str], rendered: list[str]) -> None:
    if entity:
        phrase = " ".join(entity)
        quoted = 1 < len(entity) <= 3
        rendered.append(f'"{phrase}"' if quoted else phrase)
        entity.clear()


def _expand_filetypes(query: str, corrections: list[Correction]) -> str:
    tokens = _QUERY_TOKEN.findall(query)
    if not any(_filetype_needs_expansion(token) for token in tokens):
        return query
    before = query
    expanded: list[str] = []
    for token in tokens:
        for piece in _expand_filetype_token(token).split(" "):
            if not (_filetype_match(piece) and piece in expanded):
                expanded.append(piece)
    query = " ".join(expanded)
    if query == before:
        return before
    item = correction(
        "expand-filetype",
        (before, query),
        "expanded sibling formats (exposingtheinvisible google-dorking, osint-techniques ch24)",
    )
    return _record(corrections, item)


def _filetype_needs_expansion(token: str) -> bool:
    match = _filetype_match(token)
    return bool(match and match.group("extension").lower() in _FILETYPE_FAMILIES)


def _filetype_match(token: str) -> re.Match[str] | None:
    inner = token[1:-1] if token.startswith("(") and token.endswith(")") else token
    return _FILETYPE.fullmatch(inner)


def _expand_filetype_token(token: str) -> str:
    match = _filetype_match(token)
    if not match:
        return token
    family = _FILETYPE_FAMILIES.get(match.group("extension").lower())
    if not family:
        return token
    negative = match.group("negative")
    if negative:
        return " ".join(f"-filetype:{item}" for item in family)
    return "(" + " OR ".join(f"filetype:{item}" for item in family) + ")"


def _compress_agent_query(query: str, corrections: list[Correction]) -> str:
    if _ERROR_QUERY.search(query):
        return query
    tokens = _QUERY_TOKEN.findall(query)
    plain = [token.strip("?,.!:;").lower() for token in tokens]
    verbose = len(tokens) >= 5 or bool(plain and plain[0] in _QUERY_VERBS)
    if not verbose:
        return query
    kept = filter(
        None,
        (_kept_token(token, word) for token, word in zip(tokens, plain, strict=True)),
    )
    after = " ".join(kept).strip() or query
    item = correction(
        "compress-agent-query",
        (query, after),
        "compressed to keyword form (osint-techniques ch24, osint-resources ch16)",
    )
    return _record(corrections, item)


def _kept_token(token: str, normalized: str) -> str:
    if token.isupper() and len(token) > 1:
        return token.rstrip("?,")
    if not _is_protected(token) and normalized in _STOPWORDS:
        return ""
    return token.rstrip("?,")


def _quoted_ranges(query: str) -> list[tuple[int, int]]:
    return [(match.start(), match.end()) for match in re.finditer(r'"[^"\n]*"', query)]


def _is_operator(token: str) -> bool:
    stripped = token.strip("()")
    return bool(_OPERATOR.match(stripped)) or (
        stripped.startswith("-") and len(stripped) > 1
    )


def _is_protected(token: str) -> bool:
    stripped = token.strip("()")
    return (
        token.startswith('"')
        or _is_operator(token)
        or token == "OR"
        or "filetype:" in token.lower()
        or "*" in token
        or bool(re.fullmatch(r"(?:19|20)\d{2}(?:\.\.(?:19|20)\d{2})?", stripped))
    )


def _meaningful_terms(query: str) -> set[str]:
    positive = " ".join(
        token
        for token in _QUERY_TOKEN.findall(query)
        if not _is_operator(token) and token != "OR"
    )
    return {
        term
        for term in re.findall(r"[a-z][a-z0-9-]{2,}", positive.lower())
        if term not in _STOPWORDS and not term.startswith("http")
    }
