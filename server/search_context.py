"""Context-aware search stays separate from the shared search orchestration."""

from dataclasses import dataclass, replace

import enforce
import engines
import rag
import search_core
import state as context_state  # type: ignore[import-not-found]
import trust
from search_core import (
    _bounded_int,
    _cap_chars,
    _chunks,
    _citation,
    _merge_outcome_maps,
    _prepare_query,
    _provenance,
    _reformulate,
    _resolve_sources,
    _run_engine_search,
    _SearchRequest,
    _store_result,
    _summary,
    _with_provider_outcomes,
)


@dataclass(frozen=True)
class _PoolOptions:
    query: str
    config: dict
    per_engine: int
    max_rounds: int
    raw: bool
    scientific: bool = False
    platform: list | None = None


@dataclass(frozen=True)
class _ContextOptions:
    query: str
    config: dict
    context: str = ""
    max_rounds: int = 3
    per_engine: int = 20
    fetch_top_k: int = 5
    session: str | None = None
    raw: bool = False
    scientific: bool = False
    platform: list | None = None


@dataclass(frozen=True)
class _ContextRun:
    options: _ContextOptions
    searched: str
    labeled: list
    suppressed: int
    details: tuple
    corrections: list
    quality: dict


@dataclass(frozen=True)
class _DetailRequest:
    labeled: list
    rank_query: str
    fetch_top_k: int
    session: str | None


def deep_context_aware_search(*args, **kwargs) -> dict:
    """Run context search with shared query enforcement and quality metadata."""
    options = _bounded_context_options(_ContextOptions(*args, **kwargs))
    return _run_context_search(options)


def _bounded_context_options(options: _ContextOptions) -> _ContextOptions:
    limits = _context_limits(
        options.max_rounds, options.per_engine, options.fetch_top_k
    )
    return replace(
        options, max_rounds=limits[0], per_engine=limits[1], fetch_top_k=limits[2]
    )


def _pool_options(options: _ContextOptions) -> _PoolOptions:
    return _PoolOptions(
        options.query,
        options.config,
        options.per_engine,
        options.max_rounds,
        options.raw,
        options.scientific,
        options.platform,
    )


def _context_rank_query(query: str, context: str) -> str:
    return query if not context.strip() else f"{query} {context}"


def _run_context_search(options: _ContextOptions):
    memory_key = options.context.strip() or options.query.strip()
    memory = context_state.get_context_memory(options.session, memory_key)
    searched, pool, corrections = _gather_pool(_pool_options(options), memory)
    rank_query = _context_rank_query(searched, options.context)
    kept, suppressed = _suppress_seen(
        trust.rrf_rank(rank_query, rag.rank(rank_query, pool)), memory["seen_urls"]
    )
    labeled, quality = trust.quality_gate(
        (_label(hit) for hit in kept), query=rank_query
    )
    _remember_context_results(labeled, memory)
    context_state.save_context_memory(options.session, memory_key, memory)
    details = _context_details(
        _DetailRequest(labeled, rank_query, options.fetch_top_k, options.session)
    )
    run = _ContextRun(
        options, searched, labeled, suppressed, details, corrections, quality
    )
    return _with_provider_outcomes(_context_response(run), pool)


def _remember_context_results(labeled, memory):
    memory["seen_urls"].update(
        engines.norm_url(hit["url"]) for hit in labeled if hit.get("url")
    )


def _context_response(run: _ContextRun):
    summary, citations, result_ids = run.details
    return {
        "query": run.searched,
        "context": run.options.context,
        "results": run.labeled,
        "already_seen_suppressed": run.suppressed,
        "summary": _cap_chars(summary, 1800),
        "citations": citations,
        "result_ids": result_ids,
        "corrections": run.corrections,
        "quality": run.quality,
    }


def _context_limits(max_rounds, per_engine, fetch_top_k):
    return (
        _bounded_int(max_rounds, 1, 6),
        _bounded_int(per_engine, 1, 20),
        _bounded_int(fetch_top_k, 0, 20),
    )


def _context_details(request: _DetailRequest):
    if request.fetch_top_k <= 0:
        return "", [], []
    return _context_fetch(request)


def _merge_pool(pool, new_hits):
    outcomes = getattr(pool, "outcomes", None)
    if outcomes is not None:
        _merge_outcome_maps(outcomes, getattr(new_hits, "outcomes", None))
    seen = {engines.norm_url(hit["url"]) for hit in pool}
    for hit in new_hits:
        key = engines.norm_url(hit["url"])
        if key not in seen:
            pool.append(hit)
            seen.add(key)
    return pool


def _initial_context_pool(request, corrections):
    try:
        searched, pool = _run_engine_search(request, corrections)
        return searched, pool, None, True
    except engines.AllProvidersFailed as exc:
        pool = engines.SearchResults([], dict(exc.outcomes))
        return request.query, pool, exc, False


def _append_context_round(pool, query, options, providers=None):
    search_options = {"providers": providers} if providers is not None else {}
    try:
        hits = engines.search(
            query,
            options.config,
            k=options.per_engine,
            cap=options.per_engine * 6,
            **search_options,
        )
    except engines.AllProvidersFailed as exc:
        outcomes = getattr(pool, "outcomes", None)
        if outcomes is not None:
            _merge_outcome_maps(outcomes, exc.outcomes)
        return exc, False
    _merge_pool(pool, hits)
    return None, True


def _build_search_request(options, searched):
    """Provider selection and request construction stay together because rounds share one shape."""
    providers, include_library = _resolve_sources(
        options.config,
        {"scientific": options.scientific, "platform": options.platform},
    )
    request = _SearchRequest(
        searched,
        options.config,
        options.per_engine,
        options.per_engine * 6,
        not enforce.enforcement_disabled(options.raw),
        providers,
        include_library,
    )
    return request, providers


def _gather_pool(options: _PoolOptions, memory):
    searched, corrections = _prepare_query(options.query, options.raw)
    request, providers = _build_search_request(options, searched)
    searched, pool, failure, succeeded = _initial_context_pool(request, corrections)
    if searched not in memory["issued_queries"]:
        memory["issued_queries"].append(searched)
    for sub_query in _reformulate(searched, options.max_rounds - 1):
        if sub_query in memory["issued_queries"]:
            continue
        memory["issued_queries"].append(sub_query)
        round_failure, round_succeeded = _append_context_round(
            pool, sub_query, options, providers
        )
        failure = round_failure or failure
        succeeded = succeeded or round_succeeded
    if not succeeded and failure is not None:
        raise failure
    return searched, pool, corrections


def _suppress_seen(ranked, seen_urls, cap=60):
    suppressed = 0
    kept = []
    for hit in ranked:
        if engines.norm_url(hit["url"]) in seen_urls:
            suppressed += 1
            continue
        kept.append(hit)
        if len(kept) >= cap:
            break
    return kept, suppressed


def _label(hit):
    return {
        "title": hit.get("title", ""),
        "url": hit.get("url", ""),
        "snippet": hit.get("snippet", ""),
        "engines": _provenance(hit),
        "relevance": hit.get("relevance", 0.0),
        "date": hit.get("date", ""),
        **({"citation_count": hit["citation_count"]} if "citation_count" in hit else {}),
    }


def _context_fetch(request: _DetailRequest):
    summary = ""
    citations = []
    result_ids = []
    for hit in request.labeled[: request.fetch_top_k]:
        url = hit.get("url", "")
        if not url:
            continue
        content = search_core._try_fetch(url, 32000)
        citations.append(_citation(hit))
        result_ids.append(_store_result(url, request.session))
        chunks = _chunks(hit, content)
        ranked = rag.rank(request.rank_query, chunks) if chunks else []
        summary += " " + _summary(ranked)
    return summary.strip(), citations, result_ids
