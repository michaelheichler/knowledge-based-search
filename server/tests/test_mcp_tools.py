import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import mcp_server


def _hits():
    return [
        {
            "title": "Alpha guide",
            "url": "https://example.com/a",
            "snippet": "Alpha overview and setup",
            "engine": "searxng",
            "rank": 1,
            "engines": ["searxng"],
        },
        {
            "title": "Beta notes",
            "url": "https://example.com/b",
            "snippet": "Beta reference material",
            "engine": "duckduckgo",
            "rank": 2,
            "engines": ["duckduckgo"],
        },
    ]


@pytest.fixture
def stubs(monkeypatch):
    calls = {"search": [], "fetch": []}

    def fake_search(query, config, k, cap):
        calls["search"].append(query)
        rows = _hits()
        if "Alpha guide" in query:
            rows = rows + [
                {
                    "title": "Alpha duplicate",
                    "url": "https://example.com/a",
                    "snippet": "Duplicate alpha",
                    "engine": "searxng",
                    "rank": 3,
                    "engines": ["searxng"],
                }
            ]
        return rows

    def fake_rank(query, docs):
        return list(docs)

    def fake_fetch_clean(url, max_chars):
        calls["fetch"].append((url, max_chars))
        return ("content from " + url + " ") * 80

    monkeypatch.setattr(mcp_server.engines, "search", fake_search)
    monkeypatch.setattr(mcp_server.rag, "rank", fake_rank)
    monkeypatch.setattr(mcp_server, "fetch_clean", fake_fetch_clean)
    mcp_server.RESULT_URLS.clear()
    return calls


def test_quick_web_search_schema(stubs):
    response = mcp_server.quick_web_search("alpha", num_results=2)

    assert set(response) == {"results"}
    assert response["results"] == [
        {
            "title": "Alpha guide",
            "url": "https://example.com/a",
            "snippet": "Alpha overview and setup",
            "engine": "searxng",
        },
        {
            "title": "Beta notes",
            "url": "https://example.com/b",
            "snippet": "Beta reference material",
            "engine": "duckduckgo",
        },
    ]
    assert stubs["fetch"] == []


def test_web_search_schema_citations_and_token_bound(stubs):
    response = mcp_server.web_search("alpha", num_results=2)

    assert set(response) == {"summary", "citations", "result_ids"}
    assert len(response["result_ids"]) == 2
    assert len(response["summary"].split()) <= 1000
    assert response["citations"] == [
        {
            "title": "Alpha guide",
            "url": "https://example.com/a",
            "snippet": "Alpha overview and setup",
            "source": "searxng",
            "date": "",
        },
        {
            "title": "Beta notes",
            "url": "https://example.com/b",
            "snippet": "Beta reference material",
            "source": "duckduckgo",
            "date": "",
        },
    ]


def test_get_content_resolves_result_id(stubs):
    result = mcp_server.web_search("alpha", num_results=1)
    content = mcp_server.get_content(result["result_ids"][0])

    assert content["source_url"] == "https://example.com/a"
    assert content["page_content"].startswith("content from https://example.com/a")


def test_deep_research_bounded_and_deduped(stubs):
    response = mcp_server.deep_research("alpha", max_rounds=2)

    assert set(response) == {"summary", "sections", "citations"}
    assert stubs["search"] == ["alpha", "Alpha guide"]
    assert [item["url"] for item in response["citations"]] == [
        "https://example.com/a",
        "https://example.com/b",
    ]
    assert len(response["sections"]) == 2
    assert all(set(section) == {"heading", "content", "sources"} for section in response["sections"])


def test_protocol_tools_list_and_call(stubs):
    listed = mcp_server.handle_json_rpc({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    called = mcp_server.handle_json_rpc(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "quick_web_search", "arguments": {"query": "alpha", "num_results": 1}},
        }
    )

    assert [tool["name"] for tool in listed["result"]["tools"]] == [
        "quick_web_search",
        "web_search",
        "get_content",
        "deep_research",
    ]
    payload = json.loads(called["result"]["content"][0]["text"])
    assert payload["results"][0]["url"] == "https://example.com/a"


@pytest.mark.skipif(not os.environ.get("KBS_LIVE"), reason="set KBS_LIVE=1 for live network smoke")
def test_live_fetch_clean_smoke():
    from fetch import fetch_clean

    content = fetch_clean("https://example.com", 2000)

    assert "Example Domain" in content
