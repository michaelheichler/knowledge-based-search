import json
import os
from pathlib import Path
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
        calls["search"].append({"query": query, "k": k, "cap": cap})
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
            "date": "",
            "relevance": 0.0,
        },
        {
            "title": "Beta notes",
            "url": "https://example.com/b",
            "snippet": "Beta reference material",
            "engine": "duckduckgo",
            "date": "",
            "relevance": 0.0,
        },
    ]
    assert stubs["fetch"] == []


def test_quick_web_search_clamps_schema_limit(stubs):
    mcp_server.quick_web_search("alpha", num_results=25)

    assert stubs["search"][0]["k"] == 20
    assert stubs["search"][0]["cap"] == 20


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
            "relevance": 0.0,
        },
        {
            "title": "Beta notes",
            "url": "https://example.com/b",
            "snippet": "Beta reference material",
            "source": "duckduckgo",
            "date": "",
            "relevance": 0.0,
        },
    ]


def test_web_search_clamps_schema_limit(stubs):
    mcp_server.web_search("alpha", num_results=12)

    assert stubs["search"][0]["k"] == 10
    assert stubs["search"][0]["cap"] == 10


def test_get_content_resolves_result_id(stubs):
    result = mcp_server.web_search("alpha", num_results=1)
    content = mcp_server.get_content(result["result_ids"][0])

    assert content["source_url"] == "https://example.com/a"
    assert content["page_content"].startswith("content from https://example.com/a")


def test_reformulate_quotes_multiword_query():
    assert mcp_server._reformulate("climate data", 3)[0] == '"climate data"'


def test_reformulate_adds_pdf_for_document_token():
    assert "openai annual report data filetype:pdf" in mcp_server._reformulate(
        "openai annual report data", 3
    )


def test_reformulate_does_not_match_document_token_substrings():
    assert all(
        "filetype:pdf" not in result
        for result in mcp_server._reformulate("best vector database 2026", 3)
    )


def test_reformulate_respects_limit_and_never_returns_original():
    results = mcp_server._reformulate("best climate data report", 2)

    assert results == [
        '"best climate data report"',
        "best climate data report filetype:pdf",
    ]
    assert "best climate data report" not in results


def test_reformulate_broadens_query():
    assert (
        mcp_server._reformulate("top climate data report", 3)[2]
        == "climate data report"
    )
    assert (
        mcp_server._reformulate("climate data report 2025", 3)[2]
        == "climate data report"
    )


def test_deep_research_bounded_and_deduped(monkeypatch):
    calls = []

    def fake_web_search(query):
        calls.append(query)
        return {
            "summary": f"summary for {query}",
            "citations": [
                {
                    "title": query,
                    "url": "https://same.example/report",
                    "snippet": "",
                    "source": "",
                    "date": "",
                }
            ],
        }

    monkeypatch.setattr(mcp_server, "web_search", fake_web_search)

    response = mcp_server.deep_research("best climate data report", max_rounds=4)

    assert set(response) == {"summary", "sections", "citations"}
    assert calls == [
        "best climate data report",
        '"best climate data report"',
        "best climate data report filetype:pdf",
        "climate data report",
    ]
    assert [item["url"] for item in response["citations"]] == [
        "https://same.example/report"
    ]
    assert len(response["sections"]) == 4
    assert all(
        set(section) == {"heading", "content", "sources"}
        for section in response["sections"]
    )


def test_deep_research_clamps_max_rounds(monkeypatch):
    calls = []

    def fake_web_search(query):
        calls.append(query)
        return {"summary": query, "citations": []}

    monkeypatch.setattr(mcp_server, "web_search", fake_web_search)

    mcp_server.deep_research("alpha beta gamma report", max_rounds=100)

    assert len(calls) == 6


def test_deep_research_summary_includes_each_round(monkeypatch):
    summaries = {
        "best climate data report": " ".join(["original"] * 700),
        '"best climate data report"': "quoted marker",
        "best climate data report filetype:pdf": "pdf marker",
    }

    def fake_web_search(query):
        return {"summary": summaries[query], "citations": []}

    monkeypatch.setattr(mcp_server, "web_search", fake_web_search)

    response = mcp_server.deep_research("best climate data report", max_rounds=3)

    assert "original" in response["summary"]
    assert "quoted marker" in response["summary"]
    assert "pdf marker" in response["summary"]


def test_protocol_tools_list_and_call(stubs):
    listed = mcp_server.handle_json_rpc(
        {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
    )
    called = mcp_server.handle_json_rpc(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "quick_web_search",
                "arguments": {"query": "alpha", "num_results": 1},
            },
        }
    )

    assert [tool["name"] for tool in listed["result"]["tools"]] == [
        "quick_web_search",
        "web_search",
        "get_content",
        "deep_research",
        "deep_context_aware_search",
    ]
    payload = json.loads(called["result"]["content"][0]["text"])
    assert payload["results"][0]["url"] == "https://example.com/a"


def test_skill_teaches_registered_tools():
    skill = (
        Path(__file__).resolve().parents[2]
        / "skills"
        / "knowledge-based-search"
        / "SKILL.md"
    )
    text = skill.read_text(encoding="utf-8")
    tool_names = [tool["name"] for tool in mcp_server.TOOL_SCHEMAS]

    for tool_name in tool_names:
        assert f"`{tool_name}" in text or tool_name in text


def test_plan_teaches_registered_tools():
    plan = Path(__file__).resolve().parents[2] / "tasks" / "plan.md"
    text = plan.read_text(encoding="utf-8")
    tool_names = [tool["name"] for tool in mcp_server.TOOL_SCHEMAS]

    assert "five tools" in text
    for tool_name in tool_names:
        assert tool_name in text


def test_deep_research_description_warns_expensive():
    description = next(
        tool["description"]
        for tool in mcp_server.TOOL_SCHEMAS
        if tool["name"] == "deep_research"
    )

    assert "Expensive" in description


def test_fatal_error_response_uses_json_rpc_envelope():
    response = mcp_server._fatal_error_response(RuntimeError("boom"))

    assert response == {
        "jsonrpc": "2.0",
        "id": None,
        "error": {"code": -32603, "message": "boom"},
    }


def test_fetch_clean_smoke(monkeypatch):
    from fetch import fetch_clean

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self, size):
            return b"<html><body><main><p>Example Domain</p></main></body></html>"

    def fake_urlopen(request, timeout):
        assert timeout == 10
        return FakeResponse()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    content = fetch_clean("https://example.com", 2000)

    assert "Example Domain" in content


def test_cap_chars_trims_without_splitting_word():
    text = "alpha beta gamma"

    capped = mcp_server._cap_chars(text, 12)

    assert capped == "alpha beta"
    assert len(capped) <= 12


def test_cap_chars_returns_short_input_unchanged():
    text = "alpha beta"

    assert mcp_server._cap_chars(text, 20) == text


def test_deep_research_caps_large_output_and_keeps_citations(monkeypatch):
    citations = [
        {
            "title": f"Title {index}",
            "url": f"https://example.com/{index}",
            "snippet": "",
            "source": "",
            "date": "",
        }
        for index in range(5)
    ]
    large_summary = " ".join(["alpha"] * 5000)

    def fake_web_search(query):
        return {"summary": large_summary, "citations": citations}

    monkeypatch.setattr(mcp_server, "web_search", fake_web_search)

    response = mcp_server.deep_research("best climate data report", max_rounds=1)

    assert len(response["summary"]) <= 4000
    assert all(len(section["content"]) <= 700 for section in response["sections"])
    assert len(response["citations"]) == 5
    assert len(json.dumps(response)) < 12000


def test_reformulate_pads_single_keyword_query():
    assert len(mcp_server._reformulate("best", 3)) == 3
