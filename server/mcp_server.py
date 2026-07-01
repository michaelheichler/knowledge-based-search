import importlib.util
import json
import os
import re
import sys
import traceback

import engines
import rag
from fetch import fetch_clean

DEFAULT_CONFIG = {"searxng_url": "https://endianness.de", "duckduckgo": True}
RESULT_URLS = {}
CONTEXT_MEMORY = {}
_SUMMARY_MAX_WORDS = 1000
_SUMMARY_MAX_CHARS = 4000
_SECTION_MAX_CHARS = 700
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


def _bounded_int(value, lower, upper):
    return max(lower, min(upper, int(value)))


TOOL_SCHEMAS = [
    {
        "name": "quick_web_search",
        "description": "Load the knowledge-based-search skill, then search the web and rank snippets without fetching pages.",
        "inputSchema": {
            "type": "object",
            "required": ["query"],
            "properties": {
                "query": {"type": "string"},
                "num_results": {
                    "type": "integer",
                    "default": 8,
                    "minimum": 1,
                    "maximum": 20,
                },
            },
        },
    },
    {
        "name": "web_search",
        "description": "Load the knowledge-based-search skill, then search, fetch a smaller default page set, rank chunks, and return a short sourced summary.",
        "inputSchema": {
            "type": "object",
            "required": ["query"],
            "properties": {
                "query": {"type": "string"},
                "num_results": {
                    "type": "integer",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 10,
                },
            },
        },
    },
    {
        "name": "get_content",
        "description": "Load the knowledge-based-search skill, then fetch cleaned page content by result id or URL.",
        "inputSchema": {
            "type": "object",
            "required": ["ref"],
            "properties": {"ref": {"type": "string"}},
        },
    },
    {
        "name": "deep_research",
        "description": "Load the knowledge-based-search skill, then run bounded multi-round search. Expensive: each round fetches and ranks. Prefer web_search for one-shot questions.",
        "inputSchema": {
            "type": "object",
            "required": ["query"],
            "properties": {
                "query": {"type": "string"},
                "max_rounds": {
                    "type": "integer",
                    "default": 3,
                    "minimum": 1,
                    "maximum": 6,
                },
            },
        },
    },
    {
        "name": "deep_context_aware_search",
        "description": "Load the knowledge-based-search skill, then search with context-aware ranking and session memory. Returns up to per_engine results per engine.",
        "inputSchema": {
            "type": "object",
            "required": ["query"],
            "properties": {
                "query": {"type": "string"},
                "context": {"type": "string", "default": ""},
                "max_rounds": {
                    "type": "integer",
                    "default": 3,
                    "minimum": 1,
                    "maximum": 6,
                },
                "per_engine": {
                    "type": "integer",
                    "default": 20,
                    "minimum": 1,
                    "maximum": 20,
                },
                "fetch_top_k": {
                    "type": "integer",
                    "default": 5,
                    "minimum": 0,
                    "maximum": 20,
                },
            },
        },
    },
]


def load_config():
    config = dict(DEFAULT_CONFIG)
    raw = os.environ.get("KBS_CONFIG")
    data = (
        _read_config(raw)
        if raw
        else _read_config(os.path.join(os.path.dirname(__file__), "config.json"))
    )
    if isinstance(data, dict):
        config.update(data)
    return config


def quick_web_search(query: str, num_results: int = 8) -> dict:
    num_results = _bounded_int(num_results, 1, 20)
    hits = engines.search(query, load_config(), k=num_results, cap=num_results)
    ranked = rag.rank(query, hits)
    return {"results": [_brief_result(hit) for hit in ranked[:num_results]]}


def web_search(query: str, num_results: int = 5) -> dict:
    num_results = _bounded_int(num_results, 1, 10)
    hits = engines.search(query, load_config(), k=num_results, cap=num_results)
    ranked_hits = rag.rank(query, hits)[:num_results]
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
    ranked_chunks = rag.rank(query, chunks) if chunks else []
    summary = _summary(ranked_chunks)
    return {
        "summary": _cap_chars(summary, _SUMMARY_MAX_CHARS),
        "citations": citations,
        "result_ids": result_ids,
    }


def get_content(ref: str) -> dict:
    url = RESULT_URLS.get(ref, ref)
    return {"source_url": url, "page_content": _try_fetch(url, 32000)}


def deep_research(query: str, max_rounds: int = 3) -> dict:
    max_rounds = max(1, min(6, int(max_rounds)))
    searches = [web_search(query)]
    queries = [query]
    for sub_query in _reformulate(query, max_rounds - 1):
        search = web_search(sub_query)
        searches.append(search)
        queries.append(sub_query)
    citations = _dedupe_citations(searches)
    sections = [
        {
            "heading": queries[index],
            "content": _cap_chars(item["summary"], _SECTION_MAX_CHARS),
            "sources": item["citations"],
        }
        for index, item in enumerate(searches)
    ]
    summary = _summary_text([item["summary"] for item in searches])
    return {
        "summary": _cap_chars(summary, _SUMMARY_MAX_CHARS),
        "sections": sections,
        "citations": citations,
    }


def deep_context_aware_search(
    query: str,
    context: str = "",
    max_rounds: int = 3,
    per_engine: int = 20,
    fetch_top_k: int = 5,
) -> dict:
    max_rounds = max(1, min(6, int(max_rounds)))
    per_engine = max(1, min(20, int(per_engine)))
    fetch_top_k = max(0, min(20, int(fetch_top_k)))
    mem = CONTEXT_MEMORY.setdefault(
        context.strip() or query.strip(), {"seen_urls": set(), "issued_queries": []}
    )
    rank_query = query if not context.strip() else (query + " " + context)
    pool = _gather_pool(query, load_config(), per_engine, max_rounds, mem)
    kept, already_seen_suppressed = _suppress_seen(
        rag.rank(rank_query, pool), mem["seen_urls"]
    )
    labeled = [_label(hit) for hit in kept]
    for hit in labeled:
        mem["seen_urls"].add(engines.norm_url(hit["url"]))
    summary, citations, result_ids = "", [], []
    if fetch_top_k > 0:
        summary, citations, result_ids = _context_fetch(
            labeled, rank_query, fetch_top_k
        )
    return {
        "query": query,
        "context": context,
        "results": labeled,
        "already_seen_suppressed": already_seen_suppressed,
        "summary": _cap_chars(summary, 1800),
        "citations": citations,
        "result_ids": result_ids,
    }


def _merge_pool(pool, new_hits):
    seen = {engines.norm_url(hit["url"]) for hit in pool}
    for hit in new_hits:
        key = engines.norm_url(hit["url"])
        if key not in seen:
            pool.append(hit)
            seen.add(key)
    return pool


def _gather_pool(query, config, per_engine, max_rounds, mem):
    pool = engines.search(query, config, k=per_engine, cap=per_engine * 6)
    if query not in mem["issued_queries"]:
        mem["issued_queries"].append(query)
    for sub_query in _reformulate(query, max_rounds - 1):
        if sub_query in mem["issued_queries"]:
            continue
        mem["issued_queries"].append(sub_query)
        _merge_pool(
            pool, engines.search(sub_query, config, k=per_engine, cap=per_engine * 6)
        )
    return pool


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
        "engines": hit.get("engines") or [hit.get("engine", "")],
        "relevance": hit.get("relevance", 0.0),
        "date": hit.get("date", ""),
    }


def _context_fetch(labeled, rank_query, fetch_top_k):
    summary = ""
    citations = []
    result_ids = []
    for hit in labeled[:fetch_top_k]:
        url = hit.get("url", "")
        if not url:
            continue
        content = _try_fetch(url, 32000)
        citations.append({**_citation(hit), "source": (hit.get("engines") or [""])[0]})
        result_ids.append(_store_result(url))
        chunks = _chunks(hit, content)
        summary += " " + _summary(rag.rank(rank_query, chunks) if chunks else [])
    return summary.strip(), citations, result_ids


def handle_json_rpc(request):
    req_id = request.get("id")
    try:
        if request.get("method") == "tools/list":
            return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOL_SCHEMAS}}
        if request.get("method") == "tools/call":
            params = request.get("params") or {}
            result = _call_tool(params.get("name"), params.get("arguments") or {})
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"content": [{"type": "text", "text": json.dumps(result)}]},
            }
        raise ValueError("Unsupported method")
    except Exception as exc:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32000, "message": str(exc)},
        }


def run_json_rpc_stdio():
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            request = json.loads(line)
            response = handle_json_rpc(request)
        except Exception as exc:
            response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": str(exc)},
            }
        print(json.dumps(response), flush=True)


def _fatal_error_response(exc):
    return {
        "jsonrpc": "2.0",
        "id": None,
        "error": {"code": -32603, "message": str(exc)},
    }


def mcp_path():
    return "sdk" if importlib.util.find_spec("mcp.server.fastmcp") else "json-rpc"


def main():
    if mcp_path() == "sdk":
        return _run_sdk()
    run_json_rpc_stdio()
    return None


def _read_config(value):
    try:
        if value and value.strip().startswith("{"):
            return json.loads(value)
        if value and os.path.exists(value):
            with open(value, "r", encoding="utf-8") as handle:
                return json.load(handle)
    except (OSError, ValueError):
        return None
    return None


def _brief_result(hit):
    result = {
        key: hit.get(key, "") for key in ("title", "url", "snippet", "engine", "date")
    }
    result["relevance"] = hit.get("relevance", 0.0)
    return result


def _citation(hit):
    return {
        "title": hit.get("title", ""),
        "url": hit.get("url", ""),
        "snippet": hit.get("snippet", ""),
        "source": hit.get("engine", ""),
        "date": hit.get("date", ""),
        "relevance": hit.get("relevance", 0.0),
    }


def _store_result(url):
    ref = f"r{len(RESULT_URLS) + 1}"
    RESULT_URLS[ref] = url
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
    limit = max(0, int(limit))
    original = query.strip()
    if not limit or not original:
        return []
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
    if any(word.lower() in removable for word in words):
        candidates.append(
            " ".join(word for word in words if word.lower() not in removable)
        )
    else:
        candidates.append(" ".join(words[:3]))
    candidates.extend(
        [
            f"{original} sources",
            f"{original} evidence",
            f"{original} official",
            f"{original} analysis",
            f"{original} comparison",
        ]
    )
    results = []
    for candidate in candidates:
        if candidate and candidate != original and candidate not in results:
            results.append(candidate)
        if len(results) >= limit:
            break
    return results


def _dedupe_citations(searches):
    seen = set()
    citations = []
    for search in searches:
        for citation in search.get("citations", []):
            url = citation.get("url", "")
            key = engines.norm_url(url) if url else ""
            if key and key not in seen:
                seen.add(key)
                citations.append(citation)
    return citations


def _call_tool(name, arguments):
    tools = {
        "quick_web_search": quick_web_search,
        "web_search": web_search,
        "get_content": get_content,
        "deep_research": deep_research,
        "deep_context_aware_search": deep_context_aware_search,
    }
    if name not in tools:
        raise ValueError("Unknown tool")
    return tools[name](**arguments)


def _run_sdk():
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        run_json_rpc_stdio()
        return None
    server = FastMCP("knowledge-based-search")

    descriptions = {tool["name"]: tool["description"] for tool in TOOL_SCHEMAS}
    server.tool(description=descriptions["quick_web_search"])(quick_web_search)
    server.tool(description=descriptions["web_search"])(web_search)
    server.tool(description=descriptions["get_content"])(get_content)
    server.tool(description=descriptions["deep_research"])(deep_research)
    server.tool(description=descriptions["deep_context_aware_search"])(
        deep_context_aware_search
    )
    server.run()
    return None


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        print(json.dumps(_fatal_error_response(exc)), flush=True)
        traceback.print_exc(file=sys.stderr)
        raise
