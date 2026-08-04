"""Trust scoring and ranking stay separate from query rewriting."""

from __future__ import annotations

import json
import math
import re
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from urllib.parse import urlsplit

from enforce import _STOPWORDS

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
_LIBRARY_TRUST = 95
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


def quality_gate(results, top_n=5, query: str = "") -> tuple:
    """Tag source tiers and summarize distinct-root-domain corroboration."""
    category = query_category(query) if query else None
    tagged = [_tag_source(item, category) for item in results]
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


_RRF_K = 60
_MISSING_DATE_PENALTY = 5
_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _usable_date(item: Mapping[str, object]) -> str:
    date = item.get("date", "")
    value = date if isinstance(date, str) else ""
    return value if _ISO_DATE.fullmatch(value) else ""


def _trust_with_penalties(
    item: Mapping[str, object], category: str | None = None
) -> int | None:
    trust = trust_score(str(item.get("url", "")), category)
    count = item.get("citation_count")
    if isinstance(trust, int) and isinstance(count, int) and count > 0:
        trust = min(100, trust + min(5, int(math.log10(count + 1) * 2)))
    if isinstance(trust, int) and not _usable_date(item):
        trust = max(0, trust - _MISSING_DATE_PENALTY)
    return trust


def _ranking_trust(item: Mapping[str, object], category: str | None) -> int:
    trust = _trust_with_penalties(item, category)
    return trust if trust is not None else -1


def _rrf(rankings: Sequence[Sequence[int]]) -> dict[int, float]:
    scores: dict[int, float] = {}
    for ranking in rankings:
        for position, index in enumerate(ranking):
            scores[index] = scores.get(index, 0.0) + 1.0 / (
                _RRF_K + position + 1
            )
    return scores


def rrf_rank(query: str, hits: list) -> list:
    """Return descending three-list RRF scores with every hit in each list."""
    category = query_category(query)
    indices = range(len(hits))
    relevance = sorted(
        indices,
        key=lambda index: float(hits[index].get("relevance", 0) or 0),
        reverse=True,
    )
    trust = sorted(
        indices,
        key=lambda index: _ranking_trust(hits[index], category),
        reverse=True,
    )
    dates = sorted(
        indices,
        key=lambda index: _usable_date(hits[index]),
        reverse=True,
    )
    scores = _rrf([relevance, trust, dates])
    return [hits[index] for index in sorted(indices, key=lambda index: -scores[index])]


def _tag_source(
    item: Mapping[str, object], category: str | None = None
) -> dict[str, object]:
    tagged = dict(item)
    url = str(tagged.get("url", ""))
    tagged["trust"] = _trust_with_penalties(tagged, category)
    tagged["confidence"] = source_tier(url, tagged)
    return tagged


def _result_domains(results: Iterable[Mapping[str, object]]) -> set[str]:
    domains = {root_domain(str(item.get("url", ""))) for item in results}
    domains.discard("")
    return domains


def _supporting_domains(results: Sequence[Mapping[str, object]]) -> set[str]:
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
    if url.startswith("library://"):
        return _LIBRARY_TRUST
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


def source_tier(url: str, item: Mapping[str, object] | None = None) -> str:
    """Classify a source with maintained scores and explicit overrides."""
    if url.startswith("library://"):
        return "primary"
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
