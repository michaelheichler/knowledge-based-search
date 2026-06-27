import importlib.util
import json
import os
import sys
import traceback

import engines
import rag
from fetch import fetch_clean

DEFAULT_CONFIG = {"searxng_url": "https://endianness.de", "duckduckgo": True}
RESULT_URLS = {}
_SUMMARY_MAX_WORDS = 1000
_SUMMARY_MIN_WORDS = 500


TOOL_SCHEMAS = [
    {
        "name": "quick_web_search",
        "description": "Search the web and rank snippets without fetching pages.",
        "inputSchema": {
            "type": "object",
            "required": ["query"],
            "properties": {
                "query": {"type": "string"},
                "num_results": {"type": "integer", "default": 8, "minimum": 1, "maximum": 20},
            },
        },
    },
    {
        "name": "web_search",
        "description": "Search, fetch pages, rank chunks, and return a short sourced summary.",
        "inputSchema": {
            "type": "object",
            "required": ["query"],
            "properties": {
                "query": {"type": "string"},
                "num_results": {"type": "integer", "default": 5, "minimum": 1, "maximum": 10},
            },
        },
    },
    {
        "name": "get_content",
        "description": "Fetch cleaned page content by result id or URL.",
        "inputSchema": {
            "type": "object",
            "required": ["ref"],
            "properties": {"ref": {"type": "string"}},
        },
    },
    {
        "name": "deep_research",
        "description": "Expensive web search loop. True multi-step reasoning is the calling agent job.",
        "inputSchema": {
            "type": "object",
            "required": ["query"],
            "properties": {
                "query": {"type": "string"},
                "max_rounds": {"type": "integer", "default": 3, "minimum": 1, "maximum": 6},
            },
        },
    },
]


def load_config():
    config = dict(DEFAULT_CONFIG)
    raw = os.environ.get("KBS_CONFIG")
    data = _read_config(raw) if raw else _read_config(os.path.join(os.path.dirname(__file__), "config.json"))
    if isinstance(data, dict):
        config.update(data)
    return config


def quick_web_search(query: str, num_results: int = 8) -> dict:
    hits = engines.search(query, load_config(), k=num_results, cap=num_results)
    ranked = rag.rank(query, hits)
    return {"results": [_brief_result(hit) for hit in ranked[:num_results]]}


def web_search(query: str, num_results: int = 5) -> dict:
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
    return {
        "summary": _summary(ranked_chunks),
        "citations": citations,
        "result_ids": result_ids,
    }


def get_content(ref: str) -> dict:
    url = RESULT_URLS.get(ref, ref)
    return {"source_url": url, "page_content": _try_fetch(url, 32000)}


def deep_research(query: str, max_rounds: int = 3) -> dict:
    max_rounds = max(1, int(max_rounds))
    searches = [web_search(query)]
    sub_queries = _sub_queries(searches[0], max_rounds - 1)
    for sub_query in sub_queries:
        searches.append(web_search(sub_query))
    citations = _dedupe_citations(searches)
    sections = [
        {"heading": query if index == 0 else sub_queries[index - 1], "content": item["summary"], "sources": item["citations"]}
        for index, item in enumerate(searches)
    ]
    return {"summary": _summary_text([item["summary"] for item in searches]), "sections": sections, "citations": citations}


def handle_json_rpc(request):
    req_id = request.get("id")
    try:
        if request.get("method") == "tools/list":
            return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOL_SCHEMAS}}
        if request.get("method") == "tools/call":
            params = request.get("params") or {}
            result = _call_tool(params.get("name"), params.get("arguments") or {})
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(result)}]}}
        raise ValueError("Unsupported method")
    except Exception as exc:
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32000, "message": str(exc)}}


def run_json_rpc_stdio():
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            request = json.loads(line)
            response = handle_json_rpc(request)
        except Exception as exc:
            response = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(exc)}}
        print(json.dumps(response), flush=True)


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
    return {key: hit.get(key, "") for key in ("title", "url", "snippet", "engine")}


def _citation(hit):
    return {
        "title": hit.get("title", ""),
        "url": hit.get("url", ""),
        "snippet": hit.get("snippet", ""),
        "source": hit.get("engine", ""),
        "date": hit.get("date", ""),
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
        text = " ".join(words[start:start + words_per_chunk])
        if text:
            chunks.append({"title": hit.get("title", ""), "url": hit.get("url", ""), "snippet": text, "engine": hit.get("engine", "")})
    return chunks[:4]


def _summary(chunks):
    parts = []
    for chunk in chunks:
        parts.extend(str(chunk.get("snippet", "")).split())
        if len(parts) >= _SUMMARY_MAX_WORDS:
            break
    return " ".join(parts[:_SUMMARY_MAX_WORDS])


def _summary_text(items):
    words = []
    for item in items:
        words.extend(str(item).split())
        if len(words) >= _SUMMARY_MIN_WORDS:
            break
    return " ".join(words[:_SUMMARY_MAX_WORDS])


def _sub_queries(search, limit):
    titles = []
    for citation in search.get("citations", []):
        title = citation.get("title", "").strip()
        if title and title not in titles:
            titles.append(title)
    return titles[:limit]


def _dedupe_citations(searches):
    seen = set()
    citations = []
    for search in searches:
        for citation in search.get("citations", []):
            url = citation.get("url", "")
            if url and url not in seen:
                seen.add(url)
                citations.append(citation)
    return citations


def _call_tool(name, arguments):
    tools = {
        "quick_web_search": quick_web_search,
        "web_search": web_search,
        "get_content": get_content,
        "deep_research": deep_research,
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
    server.run()
    return None


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    except Exception:
        traceback.print_exc(file=sys.stderr)
        raise
