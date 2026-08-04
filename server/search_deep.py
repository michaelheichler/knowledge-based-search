"""Deep research rounds stay separate from the shared search orchestration."""

import enforce
import engines
import trust
from search_core import (
    _SUMMARY_MAX_CHARS,
    _bounded_int,
    _cap_chars,
    _citation,
    _merge_outcome_maps,
    _outcomes_succeeded,
    _provider_outcomes,
    _reformulate,
    _summary,
    _summary_text,
    quick_web_search,
    web_search,
)

_SECTION_MAX_CHARS = 700
_REFINEMENT_KINDS = {
    "relax-quotes",
    "reorder-operators",
    "wildcard-phrase",
    "progressive-negation",
}


def deep_research(query, config, max_rounds=3, **options) -> dict:
    """Run bounded multi-query research with enforcement on each dispatch."""
    raw = bool(options.get("raw", False))
    scientific = bool(options.get("scientific", False))
    platform = options.get("platform")
    if scientific or platform is not None:
        search = lambda sub_query: _deep_search(
            sub_query, config, raw, scientific=True, platform=platform
        )
    else:
        search = lambda sub_query: _deep_search(sub_query, config, raw)
    return _deep_research(query, max_rounds, search)


def _failed_deep_response(query, failure, response=None):
    if response is None:
        _, quality = trust.quality_gate([])
        response = {
            "query": query,
            "summary": "",
            "citations": [],
            "result_ids": [],
            "corrections": [],
            "quality": quality,
        }
    failed = dict(response)
    providers = _provider_outcomes([response])
    _merge_outcome_maps(providers, failure.outcomes)
    failed["providers"] = providers
    failed["_provider_failure"] = failure
    return failed


def _deep_search(sub_query, config, raw=False, scientific=False, platform=None):
    try:
        if scientific or platform is not None:
            response = _call_web_search(
                sub_query, config, raw, scientific=True, platform=platform
            )
        else:
            response = _call_web_search(sub_query, config, raw)
    except engines.AllProvidersFailed as exc:
        return _failed_deep_response(sub_query, exc)
    if response.get("citations") or (response.get("summary") or "").strip():
        return response
    if enforce.enforcement_disabled(raw) or _corrective_rounds(response) >= 2:
        return response
    if scientific or platform is not None:
        return _deep_fallback(
            sub_query, config, response, scientific=True, platform=platform
        )
    return _deep_fallback(sub_query, config, response)


def _deep_fallback(sub_query, config, response, scientific=False, platform=None):
    fallback_query = response.get("query", sub_query)
    try:
        if scientific or platform is not None:
            quick = _call_literal_quick(fallback_query, config, scientific=True, platform=platform)
        else:
            quick = _call_literal_quick(fallback_query, config)
    except engines.AllProvidersFailed as exc:
        return _failed_deep_response(fallback_query, exc, response)
    results = quick.get("results", [])
    if not results:
        return response
    citations, quality = trust.quality_gate((_citation(result) for result in results), query=fallback_query)
    data = {
        "query": quick.get("query", sub_query),
        "summary": _cap_chars(_summary(results), _SUMMARY_MAX_CHARS),
        "citations": citations,
        "result_ids": [],
        "corrections": response.get("corrections", []) + quick.get("corrections", []),
        "quality": quality,
    }
    providers = _provider_outcomes([response, quick])
    if providers:
        data["providers"] = providers
    return data


def _call_web_search(query, config, raw, scientific=False, platform=None):
    options = (
        {"scientific": True, "platform": platform}
        if scientific or platform is not None
        else {}
    )
    if raw:
        return web_search(query, config, raw=True, **options)
    return web_search(query, config, **options)


def _call_literal_quick(query, config, scientific=False, platform=None):
    options = (
        {"scientific": True, "platform": platform}
        if scientific or platform is not None
        else {}
    )
    return quick_web_search(query, config, num_results=5, raw=True, **options)


def _corrective_rounds(response) -> int:
    return sum(
        item.get("kind") in _REFINEMENT_KINDS
        for item in response.get("corrections", [])
    )


def _deep_research(query: str, max_rounds: int, search):
    searches, queries = _deep_searches(query, max_rounds, search)
    citations, quality = trust.quality_gate(
        _dedupe_citations(searches), query=query
    )
    sections = _deep_sections(searches, queries)
    summary = _summary_text([item["summary"] for item in searches])
    if not summary and citations:
        summary = _summary(citations)
    data = {
        "query": searches[0].get("query", query),
        "summary": _cap_chars(summary, _SUMMARY_MAX_CHARS),
        "sections": sections,
        "citations": citations,
        "corrections": _dedupe_corrections(searches),
        "quality": quality,
    }
    providers = _provider_outcomes(searches)
    if providers:
        data["providers"] = providers
    return data


def _round_succeeded(response) -> bool:
    if response.get("citations") or (response.get("summary") or "").strip():
        return True
    providers = response.get("providers")
    if providers is None:
        return response.get("_provider_failure") is None
    return _outcomes_succeeded(providers)


def _raise_when_no_round_succeeded(searches) -> None:
    if any(_round_succeeded(response) for response in searches):
        return
    failures = [item.get("_provider_failure") for item in searches]
    failures = [failure for failure in failures if failure is not None]
    if failures:
        raise failures[-1]


def _deep_searches(query, max_rounds, search):
    max_rounds = _bounded_int(max_rounds, 1, 6)
    queries = [query, *_reformulate(query, max_rounds - 1)]
    searches = [search(item) for item in queries]
    _raise_when_no_round_succeeded(searches)
    return searches, queries


def _deep_sections(searches, queries):
    return [
        {
            "heading": item.get("query", queries[index]),
            "content": _cap_chars(item["summary"], _SECTION_MAX_CHARS),
            "sources": item["citations"],
        }
        for index, item in enumerate(searches)
    ]


def _dedupe_corrections(searches):
    seen = set()
    kept = []
    items = (item for search in searches for item in search.get("corrections", []))
    for item in items:
        key = tuple(
            item.get(name, "") for name in ("kind", "before", "after", "reason")
        )
        if key not in seen:
            seen.add(key)
            kept.append(item)
    return kept


def _dedupe_citations(searches):
    seen = set()
    citations = []
    items = (item for search in searches for item in search.get("citations", []))
    for citation in items:
        url = citation.get("url", "")
        key = engines.norm_url(url) if url else ""
        if key and key not in seen:
            seen.add(key)
            citations.append(citation)
    return citations
