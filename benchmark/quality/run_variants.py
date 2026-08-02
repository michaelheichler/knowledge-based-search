"""Run config variants over cached per-engine hits so the comparison is fair."""

import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "server"))
import cli
import engines
import rag

CONFIG = cli.load_config()
SEARXNG_URL = CONFIG.get("searxng_url")
ALL_ENGINES = tuple(
    name
    for name in ("searxng", "duckduckgo", "startpage", "mojeek")
    if name != "searxng" or SEARXNG_URL
)
FETCH_K = 20
VARIANTS = [
    {"name": "baseline", "engines": None, "per_engine": 10, "rank": "full"},
    {"name": "wide", "engines": None, "per_engine": 20, "rank": "full"},
    {"name": "bm25_only", "engines": None, "per_engine": 10, "rank": "bm25"},
]
if SEARXNG_URL:
    VARIANTS.append(
        {
            "name": "searxng_only",
            "engines": ["searxng"],
            "per_engine": 10,
            "rank": "full",
        }
    )


def _fetch_engine(name, query):
    try:
        if name == "searxng" and SEARXNG_URL:
            return engines.searxng(query, SEARXNG_URL, FETCH_K)
        if name == "duckduckgo":
            return engines.duckduckgo(query, FETCH_K)
        if name == "startpage":
            return engines.startpage(query, k=FETCH_K)
        if name == "mojeek":
            return engines.mojeek(query, k=FETCH_K)
    except engines._PROVIDER_FAILURES:
        return []
    return []


def _fetch_query(query):
    return {name: _fetch_engine(name, query) for name in ALL_ENGINES}


def _has_hits(path):
    if not os.path.exists(path):
        return False
    try:
        with open(path, encoding="utf-8") as handle:
            return any(json.load(handle).values())
    except (OSError, ValueError):
        return False


def _ensure_cache(here, queries):
    cache_dir = os.path.join(here, "cache")
    os.makedirs(cache_dir, exist_ok=True)
    for query in queries:
        path = os.path.join(cache_dir, query["id"] + ".json")
        if _has_hits(path):
            continue
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(_fetch_query(query["query"]), handle)
        time.sleep(3.0)


def _load_cache(here, query_id):
    with open(
        os.path.join(here, "cache", query_id + ".json"), encoding="utf-8"
    ) as handle:
        return json.load(handle)


def _pool_from_cache(cache, variant):
    allowed = variant["engines"] if variant["engines"] is not None else cache
    lists = [cache.get(name, [])[: variant["per_engine"]] for name in allowed]
    return engines.merge(lists, variant["per_engine"] * 6)


def _bm25_rank(query, hits):
    docs = [rag._doc_text(hit) for hit in hits]
    order = rag._bm25_order(query, docs)
    ranked = []
    for position, index in enumerate(order):
        if 0 <= index < len(hits):
            hits[index]["relevance"] = round(1.0 - position / max(len(order), 1), 2)
            ranked.append(hits[index])
    return ranked


def _rank(query, hits, mode):
    return _bm25_rank(query, hits) if mode == "bm25" else rag.rank(query, hits)


def _record(hit):
    return {
        "title": hit.get("title", ""),
        "url": hit.get("url", ""),
        "snippet": hit.get("snippet", ""),
        "relevance": hit.get("relevance", 0.0),
        "date": hit.get("date", ""),
        "engines": hit.get("engines") or [hit.get("engine", "")],
    }


def _run_variant(variant, queries, here):
    results = {}
    for query in queries:
        pool = _pool_from_cache(_load_cache(here, query["id"]), variant)
        ranked = _rank(query["query"], pool, variant["rank"])
        results[query["id"]] = [_record(hit) for hit in ranked[:10]]
    return results


def main() -> None:
    """Run available benchmark variants and write their result files."""
    here = os.path.dirname(__file__)
    with open(os.path.join(here, "queries.json"), encoding="utf-8") as handle:
        queries = json.load(handle)["queries"]
    _ensure_cache(here, queries)
    runs_dir = os.path.join(here, "runs")
    os.makedirs(runs_dir, exist_ok=True)
    for variant in VARIANTS:
        results = _run_variant(variant, queries, here)
        payload = {"variant": variant["name"], "config": variant, "results": results}
        with open(
            os.path.join(runs_dir, variant["name"] + ".json"), "w", encoding="utf-8"
        ) as handle:
            json.dump(payload, handle, indent=2)
        print(f"wrote {variant['name']}: {len(results)} queries")


if __name__ == "__main__":
    main()
