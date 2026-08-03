"""MCP client for trusted library passages outside provider fan-out."""

import json
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


def library(
    query,
    k=10,
    timeout=_TIMEOUT,
    config=None,
    post: Callable[..., tuple[str, dict]] | None = None,
    parser: Callable[[str], dict] | None = None,
    result_fn: Callable[..., dict] | None = None,
) -> list:
    """Keep trusted library passages outside the paced network fan-out."""
    if post is None:
        post = _mcp_post
    if parser is None:
        parser = _mcp_json
    if result_fn is None:
        import engines

        result_fn = engines.result
    config = cast(dict[str, str], config)
    url = config["library_mcp_url"]
    token = config["library_mcp_token"]
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
    body, response_headers = post(url, token, initialize, timeout=timeout)
    headers = {key.lower(): value for key, value in response_headers.items()}
    session_id = headers.get("mcp-session-id")
    post(
        url,
        token,
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        session_id=session_id,
        timeout=timeout,
    )
    body, _ = post(
        url,
        token,
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "search_library",
                "arguments": {"query": query, "k": k},
            },
        },
        session_id=session_id,
        timeout=timeout,
    )
    data = parser(body)
    payload = json.loads(data["result"]["content"][0]["text"])
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
