"""Exercise library MCP depth wrappers without contacting the provider."""

import json

import library_engine

_CONFIG = {"library_mcp_url": "http://library/mcp", "library_mcp_token": "secret"}


def _rpc_payload(payload: dict) -> str:
    """MCP envelope invariant: canned responses follow the client boundary."""
    return json.dumps(
        {"jsonrpc": "2.0", "result": {"content": [{"text": json.dumps(payload)}]}}
    )


def _post_script(responses, calls):
    """Handshake invariant: tests record every request without network access."""
    def post(url, token, payload, **kwargs):
        calls.append((url, token, payload, kwargs))
        return responses.pop(0)

    return post


def test_get_passage_preserves_full_text_and_tool_arguments() -> None:
    """Depth invariant: an integrity check must see the complete passage."""
    passage = {"book_id": "book", "chunk_id": "chunk", "text": "x" * 301, "author": "A"}
    calls = []
    responses = [
        ("{}", {"MCP-SESSION-ID": "session"}),
        ("", {}),
        (_rpc_payload({"passage": passage}), {}),
    ]

    result = library_engine.get_passage(
        "book", "chunk", config=_CONFIG, post=_post_script(responses, calls)
    )

    assert result == passage
    assert len(result["text"]) == 301
    assert calls[2][2]["params"] == {
        "name": "get_passage",
        "arguments": {"passage_id": "chunk"},
    }
    assert calls[2][3]["session_id"] == "session"


def test_get_chapter_uses_book_and_chapter_arguments() -> None:
    """Argument invariant: chapter retrieval keeps both source identifiers."""
    chapter = {"book_id": "book", "chapter_id": "chapter", "text": "chapter text"}
    calls = []
    responses = [
        ("{}", {"mcp-session-id": "session"}),
        ("", {}),
        (_rpc_payload({"chapter": chapter}), {}),
    ]

    result = library_engine.get_chapter(
        "book", "chapter", config=_CONFIG, post=_post_script(responses, calls)
    )

    assert result == chapter
    assert calls[2][2]["params"] == {
        "name": "get_chapter",
        "arguments": {"book_id": "book", "chapter_id": "chapter"},
    }


def test_get_passage_absorbs_provider_failure() -> None:
    """Failure invariant: optional deepening must never block synthesis."""
    def failing_post(*_args, **_kwargs):
        raise RuntimeError("provider unavailable")

    assert library_engine.get_passage(
        "book", "chunk", config=_CONFIG, post=failing_post
    ) == {}


def test_get_passage_from_url_parses_synthetic_identifier(monkeypatch) -> None:
    """Identity invariant: URL parsing must preserve the attributed chunk."""
    calls = []

    def fake_get_passage(book_id, chunk_id, **_kwargs):
        calls.append((book_id, chunk_id))
        return {"text": "full passage"}

    monkeypatch.setattr(library_engine, "get_passage", fake_get_passage)

    assert library_engine.get_passage_from_url(
        "library://book%20id?chunk=chunk%2F1"
    ) == {"text": "full passage"}
    assert calls == [("book id", "chunk/1")]
    assert library_engine.get_passage_from_url("library://book") == {}
    assert library_engine.get_passage_from_url("https://book?chunk=chunk") == {}
