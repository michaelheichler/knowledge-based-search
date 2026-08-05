"""MCP client for trusted library passages outside provider fan-out."""

import json
import urllib.parse
import urllib.request
from collections.abc import Callable
from typing import cast

_TIMEOUT = 12.0


def _mcp_post(url, token, payload, session_id=None, timeout=_TIMEOUT) -> tuple[str, dict]:
    """Retain MCP response headers because initialize returns the session there."""
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Authorization": f"Bearer {token}",
    }
    if session_id:
        headers["Mcp-Session-Id"] = session_id
    request = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"), headers=headers
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", "replace"), dict(response.headers)


def _mcp_json(body) -> dict:
    """Accept plain JSON because some streamable-HTTP servers skip SSE."""
    body = body.lstrip()
    if body.startswith("{"):
        return json.loads(body)
    for line in body.splitlines():
        if line.startswith("data: "):
            return json.loads(line[6:])
    raise ValueError("MCP response did not contain a JSON data event")


def _mcp_session(url, token, timeout, post) -> str | None:
    """Session invariant: streamable HTTP requires one session for later calls."""
    initialize = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "kbs", "version": "0.2"},
        },
    }
    _, response_headers = post(url, token, initialize, timeout=timeout)
    session_id = next(
        (value for key, value in response_headers.items() if key.lower() == "mcp-session-id"),
        None,
    )
    post(
        url,
        token,
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        session_id=session_id,
        timeout=timeout,
    )
    return session_id


def _mcp_call(url, token, name, arguments, session_id, timeout, post) -> str:
    """MCP invariant: every tool request carries the negotiated session."""
    body, _ = post(
        url,
        token,
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        },
        session_id=session_id,
        timeout=timeout,
    )
    return body


def _mcp_tool(
    name,
    arguments,
    timeout=_TIMEOUT,
    config=None,
    post: Callable[..., tuple[str, dict]] | None = None,
    parser: Callable[[str], dict] | None = None,
) -> dict:
    """Protocol invariant: MCP session setup stays centralized."""
    if post is None:
        post = _mcp_post
    if parser is None:
        parser = _mcp_json
    config = cast(dict[str, str], config)
    url = config["library_mcp_url"]
    token = config["library_mcp_token"]
    session_id = _mcp_session(url, token, timeout, post)
    body = _mcp_call(url, token, name, arguments, session_id, timeout, post)
    data = parser(body)
    return json.loads(data["result"]["content"][0]["text"])


def _document_tool(
    name,
    arguments,
    timeout=_TIMEOUT,
    config=None,
    post: Callable[..., tuple[str, dict]] | None = None,
    parser: Callable[[str], dict] | None = None,
) -> dict:
    """Fallback invariant: deepening failures never replace existing snippets."""
    try:
        payload = _mcp_tool(name, arguments, timeout, config, post, parser)
    except (IndexError, KeyError, OSError, RuntimeError, TypeError, ValueError):
        return {}
    document = payload.get(name.removeprefix("get_"))
    if isinstance(document, dict):
        return document
    return payload if isinstance(payload, dict) else {}


def _library_hits(payload, k, result_fn) -> list:
    """Result invariant: search snippets remain capped at their established boundary."""
    return [
        result_fn(
            f"{passage['book_title']}: {passage['chapter_title']}",
            f"library://{passage['book_id']}?chunk={passage['chunk_id']}",
            passage["text"][:300],
            "library",
            rank,
        )
        for rank, passage in enumerate(payload.get("passages", [])[:k], 1)
    ]


def library(
    query,
    k=10,
    timeout=_TIMEOUT,
    config=None,
    post: Callable[..., tuple[str, dict]] | None = None,
    parser: Callable[[str], dict] | None = None,
    result_fn: Callable[..., dict] | None = None,
) -> list:
    """Provider pacing excludes this trusted local source by design."""
    if post is None:
        post = _mcp_post
    if parser is None:
        parser = _mcp_json
    if result_fn is None:
        import engines

        result_fn = engines.result
    payload = _mcp_tool(
        "search_library", {"query": query, "k": k}, timeout, config, post, parser
    )
    return _library_hits(payload, k, result_fn)


def get_chapter(
    book_id,
    chapter_id,
    timeout=_TIMEOUT,
    config=None,
    post: Callable[..., tuple[str, dict]] | None = None,
    parser: Callable[[str], dict] | None = None,
) -> dict:
    """Depth invariant: integrity checks require full chapter text."""
    return _document_tool(
        "get_chapter", {"book_id": book_id, "chapter_id": chapter_id},
        timeout, config, post, parser,
    )


def get_passage(
    book_id,
    chunk_id,
    timeout=_TIMEOUT,
    config=None,
    post: Callable[..., tuple[str, dict]] | None = None,
    parser: Callable[[str], dict] | None = None,
) -> dict:
    """Depth invariant: integrity checks require the full attributed passage."""
    del book_id
    return _document_tool(
        "get_passage", {"passage_id": chunk_id}, timeout, config, post, parser
    )


def get_passage_from_url(
    url,
    timeout=_TIMEOUT,
    config=None,
    post: Callable[..., tuple[str, dict]] | None = None,
    parser: Callable[[str], dict] | None = None,
) -> dict:
    """Identity invariant: synthetic URLs retain the attributed chunk."""
    parsed = urllib.parse.urlsplit(url or "")
    if parsed.scheme != "library" or not parsed.netloc:
        return {}
    chunks = urllib.parse.parse_qs(parsed.query).get("chunk", [])
    if not chunks or not chunks[0]:
        return {}
    book_id = urllib.parse.unquote(parsed.netloc)
    if config is None and post is None and parser is None and timeout == _TIMEOUT:
        return get_passage(book_id, chunks[0])
    return get_passage(
        book_id,
        chunks[0],
        timeout=timeout,
        config=config,
        post=post,
        parser=parser,
    )
