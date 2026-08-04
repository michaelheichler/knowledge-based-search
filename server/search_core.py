# ruff: noqa: BLE001

"""Shared orchestration keeps retry budgets consistent across commands."""

import re
from dataclasses import dataclass, replace

import enforce
import engines
import rag
import state as context_state  # type: ignore[import-not-found]
import trust
from fetch import fetch_clean

RESULT_URLS = {}
_SUMMARY_MAX_WORDS = 1000
_SUMMARY_MAX_CHARS = 4000
_DOCUMENT_TOKENS = (
    "report",
    "reports",
    "data",
    "dataset",
    "statistics",
    "filing",
    "filings",
    "whitepaper",
    "white paper",
    "spec",
    "specification",
    "manual",
    "paper",
)


@dataclass(frozen=True)
class _SearchRequest:
    query: str
    config: dict
    k: int
    cap: int
    refine: bool = True
    providers: frozenset | None = None
    include_library: bool = False


@dataclass
class _RefinementState:
    original: str
    current: str
    hits: list
    used: set[str]
    corrections: list


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


def _resolve_sources(config, options) -> tuple[frozenset | None, bool]:
    """Library rides beside the providers set because it never enters the paced fan-out."""
    if not options.get("scientific"):
        return None, False
    library_configured = bool(
        config.get("library_mcp_url") and config.get("library_mcp_token")
    )
    platforms = options.get("platform")
    if platforms is None:
        return frozenset(engines.SCIENTIFIC_PLATFORMS), library_configured
    return frozenset(platforms) - {"library"}, "library" in platforms and library_configured


def _required_int(value):
    try:
        return int(value)
    except TypeError as exc:
        raise TypeError(str(exc)) from exc
    except ValueError as exc:
        raise ValueError(str(exc)) from exc


def _bounded_int(value, lower, upper):
    return max(lower, min(upper, _required_int(value)))


def _prepare_query(query: str, raw: bool, context=None):
    if enforce.enforcement_disabled(raw):
        return query, []
    return enforce.enforce_query(query, context)


def _run_engine_search(request: _SearchRequest, corrections):
    search_options = (
        {"providers": request.providers} if request.providers is not None else {}
    )
    hits = engines.search(
        request.query, request.config, k=request.k, cap=request.cap, **search_options
    )
    state = _RefinementState(request.query, request.query, hits, set(), corrections)
    if request.refine and request.providers != frozenset():
        _spend_refinement_budget(state, request)
    if request.providers is None:
        _assert_dual_primary(state.hits, request.config)
    if request.include_library:
        _append_library_hits(state, request)
    return state.current, state.hits


def _append_library_hits(state: _RefinementState, request: _SearchRequest) -> None:
    try:
        hits = engines.library(request.query, k=request.k, config=request.config)
    except engines._PROVIDER_FAILURES as exc:
        outcomes = getattr(state.hits, "outcomes", None)
        if outcomes is not None:
            outcomes["library"] = {"status": "error", "error": type(exc).__name__}
        return
    for hit in hits:
        hit["engines"] = ["library"]
    state.hits.extend(hits)
    outcomes = getattr(state.hits, "outcomes", None)
    if outcomes is not None:
        outcomes["library"] = {"status": "ok", "count": len(hits)}


def _spend_refinement_budget(state: _RefinementState, request: _SearchRequest):
    # ponytail: fixed budget, adapt only after measured recall justifies it
    for _ in range(2):
        attempt = _next_refinement(state)
        if attempt is None:
            return
        if not _apply_refinement(state, request, attempt):
            return


def _apply_refinement(state: _RefinementState, request: _SearchRequest, attempt):
    candidate, item = attempt
    state.corrections.append(item)
    search_options = (
        {"providers": request.providers} if request.providers is not None else {}
    )
    try:
        retried = engines.search(
            candidate, request.config, k=request.k, cap=request.cap, **search_options
        )
    except engines.AllProvidersFailed as exc:
        outcomes = getattr(state.hits, "outcomes", None)
        if not state.hits and not _outcomes_succeeded(outcomes):
            raise
        if outcomes is not None:
            _merge_outcome_maps(outcomes, exc.outcomes)
        return False
    if retried or not state.hits:
        state.current = candidate
        state.hits = retried
    return True


def _next_refinement(state: _RefinementState):
    return (
        _empty_refinement(state) or _weak_refinement(state) or _noisy_refinement(state)
    )


def _empty_refinement(state: _RefinementState):
    if state.hits:
        return None
    if '"' in state.current and "relax-quotes" not in state.used:
        change = ("relax-quotes", enforce.strip_quotes(state.current))
        reason = "stripped exact quotes after zero results (osint-techniques ch24, osint-resources ch16)"
        return _refinement(state, change, reason)
    if (
        enforce.operator_count(state.current) >= 2
        and "reorder-operators" not in state.used
    ):
        change = ("reorder-operators", enforce.reorder_operators(state.current))
        reason = "reordered operators after zero results (exposingtheinvisible google-dorking)"
        return _refinement(state, change, reason)
    return None


def _weak_refinement(state: _RefinementState):
    if (
        len(state.hits) > 1
        or '"' not in state.original
        or "wildcard-phrase" in state.used
    ):
        return None
    change = ("wildcard-phrase", enforce.wildcard_phrases(state.original))
    reason = "added wildcard inside brittle phrase (osint-techniques ch24, ch17)"
    return _refinement(state, change, reason)


def _noisy_refinement(state: _RefinementState):
    if not enforce.results_are_noisy(state.current, state.hits):
        return None
    change = ("progressive-negation", enforce.negation_retry(state.current, state.hits))
    reason = "excluded frequent irrelevant snippet term (osint-techniques ch24)"
    return _refinement(state, change, reason)


def _refinement(state: _RefinementState, change: tuple[str, str], reason: str):
    kind, candidate = change
    state.used.add(kind)
    if candidate == state.current:
        return None
    return candidate, enforce.correction(kind, (state.current, candidate), reason)


def _assert_dual_primary(hits, config):
    if hits or not config.get("searxng_url") or not config.get("duckduckgo", True):
        return
    outcomes = getattr(hits, "outcomes", None)
    if outcomes is not None:
        assert {"searxng", "duckduckgo"}.issubset(outcomes), (
            "null verdict requires both primary outcomes"
        )


def _bucket_results(items: list[dict]) -> list[dict]:
    groups: dict[str, list[dict]] = {}
    first_positions: dict[str, int] = {}
    for position, item in enumerate(items):
        categories = item.get("categories")
        bucket = (
            categories[0]
            if isinstance(categories, list)
            and categories
            and isinstance(categories[0], str)
            and categories[0]
            else "Uncategorized"
        )
        item["bucket"] = bucket
        groups.setdefault(bucket, []).append(item)
        first_positions.setdefault(bucket, position)
    names = sorted(
        groups,
        key=lambda name: (name == "Uncategorized", first_positions[name]),
    )
    return [{"name": name, "results": groups[name]} for name in names]


def quick_web_search(query, config, num_results=8, **options) -> dict:
    """Return ranked snippets with enforcement and source-quality metadata."""
    raw = bool(options.get("raw", False))
    num_results = _bounded_int(num_results, 1, 20)
    searched, corrections = _prepare_query(query, raw, options.get("context"))
    refine = not enforce.enforcement_disabled(raw)
    providers, include_library = _resolve_sources(config, options)
    request = _SearchRequest(searched, config, num_results, num_results, refine, providers, include_library)
    searched, hits = _run_engine_search(request, corrections)
    ranked = trust.rrf_rank(searched, rag.rank(searched, hits))
    results, quality = trust.quality_gate(
        (_brief_result(hit) for hit in ranked[:num_results]), query=searched
    )
    data = {
        "query": searched,
        "results": results,
        "corrections": corrections,
        "quality": quality,
    }
    if options.get("scientific"):
        data["buckets"] = _bucket_results(results)
    return _with_provider_outcomes(data, hits)


def web_search(query, config, num_results=5, **options) -> dict:
    """Fetch and summarize ranked results with transparent enforcement metadata."""
    raw = bool(options.get("raw", False))
    num_results = _bounded_int(num_results, 1, 10)
    searched, corrections = _prepare_query(query, raw, options.get("context"))
    refine = not enforce.enforcement_disabled(raw)
    providers, include_library = _resolve_sources(config, options)
    request = _SearchRequest(searched, config, num_results, num_results, refine, providers, include_library)
    searched, hits = _run_engine_search(request, corrections)
    ranked_hits = trust.rrf_rank(searched, rag.rank(searched, hits))[:num_results]
    chunks, citations, result_ids = _search_details(ranked_hits)
    ranked_chunks = rag.rank(searched, chunks) if chunks else []
    tagged, quality = trust.quality_gate(citations, query=searched)
    data = {
        "query": searched,
        "summary": _cap_chars(_summary(ranked_chunks), _SUMMARY_MAX_CHARS),
        "citations": tagged,
        "result_ids": result_ids,
        "corrections": corrections,
        "quality": quality,
    }
    if options.get("scientific"):
        data["buckets"] = _bucket_results(tagged)
    return _with_provider_outcomes(data, hits)


def _search_details(ranked_hits):
    chunks = []
    citations = []
    result_ids = []
    for hit in ranked_hits:
        url = hit.get("url", "")
        if not url:
            continue
        content = _try_fetch(url, 32000)
        citations.append(_citation(hit))
        result_ids.append(_store_result(url))
        chunks.extend(_chunks(hit, content))
    return chunks, citations, result_ids


def _merge_outcome(target, name, outcome) -> None:
    existing = target.get(name)
    if existing is None or outcome.get("status") == "error":
        target[name] = dict(outcome)
        return
    if existing.get("status") != "ok":
        return
    existing["count"] = existing.get("count", 0) + outcome.get("count", 0)


def _merge_outcome_maps(target, incoming):
    for name, outcome in (incoming or {}).items():
        _merge_outcome(target, name, outcome)
    return target


def _outcomes_succeeded(outcomes) -> bool:
    return any(item.get("status") == "ok" for item in (outcomes or {}).values())


def _provider_outcomes(responses):
    outcomes = {}
    for response in responses:
        _merge_outcome_maps(outcomes, response.get("providers"))
    return outcomes


def _with_provider_outcomes(data, hits):
    outcomes = getattr(hits, "outcomes", None)
    if outcomes is not None:
        data["providers"] = outcomes
    return data


def get_content(ref: str, session: str | None = None) -> dict:
    """Fetch a stored result reference or a direct web URL."""
    if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*://", ref):
        url = ref
    else:
        session_id = context_state.resolve_session(session)
        url = RESULT_URLS.get((session_id, ref))
        url = url or context_state.get_result_url(ref, session)
        if not url:
            raise KeyError(ref)
    return {"source_url": url, "page_content": fetch_clean(url, 32000)}


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


def _gather_pool(options: _PoolOptions, memory):
    searched, corrections = _prepare_query(options.query, options.raw)
    providers, include_library = _resolve_sources(options.config, {"scientific": options.scientific, "platform": options.platform})
    request = _SearchRequest(searched, options.config, options.per_engine, options.per_engine * 6, not enforce.enforcement_disabled(options.raw), providers, include_library)
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


def _provenance(hit):
    provenance = hit.get("engines")
    if provenance:
        return list(provenance)
    engine = hit.get("engine", "")
    return [engine] if engine else []


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
        content = _try_fetch(url, 32000)
        citations.append(_citation(hit))
        result_ids.append(_store_result(url, request.session))
        chunks = _chunks(hit, content)
        ranked = rag.rank(request.rank_query, chunks) if chunks else []
        summary += " " + _summary(ranked)
    return summary.strip(), citations, result_ids


def _brief_result(hit):
    return {
        "title": hit.get("title", ""),
        "url": hit.get("url", ""),
        "snippet": hit.get("snippet", ""),
        "engines": _provenance(hit),
        "date": hit.get("date", ""),
        "relevance": hit.get("relevance", 0.0),
        "categories": hit.get("categories", []),
        **({"citation_count": hit["citation_count"]} if "citation_count" in hit else {}),
    }


def _citation(hit):
    return {
        "title": hit.get("title", ""),
        "url": hit.get("url", ""),
        "snippet": hit.get("snippet", ""),
        "engines": _provenance(hit),
        "date": hit.get("date", ""),
        "relevance": hit.get("relevance", 0.0),
        "categories": hit.get("categories", []),
        "confidence": hit.get("confidence")
        or trust.source_tier(hit.get("url", ""), hit),
        **({"citation_count": hit["citation_count"]} if "citation_count" in hit else {}),
    }


def _store_result(url, session=None):
    ref = context_state.store_result_url(url, session)
    session_id = context_state.resolve_session(session)
    RESULT_URLS[(session_id, ref)] = url
    while len(RESULT_URLS) > context_state.RESULT_REF_CAP:
        RESULT_URLS.pop(next(iter(RESULT_URLS)))
    return ref


def _try_fetch(url, max_chars):
    try:
        return fetch_clean(url, max_chars)
    except Exception:
        return ""


def _chunks(hit, content, words_per_chunk=180):
    words = content.split()
    if not words:
        words = hit.get("snippet", "").split()
    chunks = []
    for start in range(0, len(words), words_per_chunk):
        text = " ".join(words[start : start + words_per_chunk])
        if text:
            chunks.append(
                {
                    "title": hit.get("title", ""),
                    "url": hit.get("url", ""),
                    "snippet": text,
                    "engine": hit.get("engine", ""),
                }
            )
    return chunks[:4]


def _summary(chunks):
    parts = []
    for chunk in chunks:
        parts.extend(str(chunk.get("snippet", "")).split())
        if len(parts) >= _SUMMARY_MAX_WORDS:
            break
    return " ".join(parts[:_SUMMARY_MAX_WORDS])


def _summary_text(items):
    items = [str(item) for item in items if str(item).strip()]
    if not items:
        return ""
    words = []
    per_item = max(1, _SUMMARY_MAX_WORDS // len(items))
    for item in items:
        words.extend(item.split()[:per_item])
    return " ".join(words[:_SUMMARY_MAX_WORDS])


def _cap_chars(text, limit):
    value = str(text)
    if len(value) <= limit:
        return value
    capped = value[:limit]
    whitespace_at = max(
        (index for index, char in enumerate(capped) if char.isspace()), default=-1
    )
    if whitespace_at <= 0:
        return capped
    return capped[:whitespace_at].rstrip()


def _reformulate(query, limit):
    limit = max(0, _required_int(limit))
    original = query.strip()
    if not limit or not original:
        return []
    candidates = _reformulation_candidates(original)
    distinct = list(dict.fromkeys(item for item in candidates if item != original))
    return distinct[:limit]


def _reformulation_candidates(original):
    candidates = []
    words = original.split()
    if len(words) > 1 and not (original.startswith('"') and original.endswith('"')):
        candidates.append(f'"{original}"')
    lower = original.lower()
    word_tokens = set(re.findall("[a-z]+", lower))
    if "white paper" in lower or any(
        token in word_tokens for token in _DOCUMENT_TOKENS if " " not in token
    ):
        candidates.append(f"{original} filetype:pdf")
    removable = {"best", "top"}
    cleaned = " ".join(word for word in words if word.lower() not in removable)
    candidates.append(cleaned if cleaned != original else " ".join(words[:3]))
    candidates.extend(
        f"{original} {suffix}"
        for suffix in ("sources", "evidence", "official", "analysis", "comparison")
    )
    return candidates
