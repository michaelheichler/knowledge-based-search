import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import search_core
from fetch import fetch_clean


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
            rows = [
                *rows,
                {
                    "title": "Alpha duplicate",
                    "url": "https://example.com/a",
                    "snippet": "Duplicate alpha",
                    "engine": "searxng",
                    "rank": 3,
                    "engines": ["searxng"],
                },
            ]
        return rows

    def fake_rank(query, docs):
        return list(docs)

    def fake_fetch_clean(url, max_chars):
        calls["fetch"].append((url, max_chars))
        return ("content from " + url + " ") * 80

    monkeypatch.setattr(search_core.engines, "search", fake_search)
    monkeypatch.setattr(search_core.rag, "rank", fake_rank)
    monkeypatch.setattr(search_core, "fetch_clean", fake_fetch_clean)
    search_core.RESULT_URLS.clear()
    return calls


def test_quick_web_search_schema(stubs):
    response = search_core.quick_web_search("alpha", {}, num_results=2)

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
    search_core.quick_web_search("alpha", {}, num_results=25)

    assert stubs["search"][0]["k"] == 20
    assert stubs["search"][0]["cap"] == 20


def test_web_search_schema_citations_and_token_bound(stubs):
    response = search_core.web_search("alpha", {}, num_results=2)

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
    search_core.web_search("alpha", {}, num_results=12)

    assert stubs["search"][0]["k"] == 10
    assert stubs["search"][0]["cap"] == 10


def test_get_content_resolves_result_id(stubs):
    result = search_core.web_search("alpha", {}, num_results=1)
    content = search_core.get_content(result["result_ids"][0])

    assert content["source_url"] == "https://example.com/a"
    assert content["page_content"].startswith("content from https://example.com/a")


def test_reformulate_quotes_multiword_query():
    assert search_core._reformulate("climate data", 3)[0] == '"climate data"'


def test_reformulate_adds_pdf_for_document_token():
    assert "openai annual report data filetype:pdf" in search_core._reformulate(
        "openai annual report data", 3
    )


def test_reformulate_does_not_match_document_token_substrings():
    assert all(
        "filetype:pdf" not in result
        for result in search_core._reformulate("best vector database 2026", 3)
    )


def test_reformulate_respects_limit_and_never_returns_original():
    results = search_core._reformulate("best climate data report", 2)

    assert results == [
        '"best climate data report"',
        "best climate data report filetype:pdf",
    ]
    assert "best climate data report" not in results


def test_reformulate_broadens_query():
    assert (
        search_core._reformulate("top climate data report", 3)[2]
        == "climate data report"
    )
    assert (
        search_core._reformulate("climate data report 2025", 3)[2]
        == "climate data report"
    )


def test_deep_research_bounded_and_deduped(monkeypatch):
    calls = []

    def fake_web_search(query, config):
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

    monkeypatch.setattr(search_core, "web_search", fake_web_search)

    response = search_core.deep_research("best climate data report", {}, max_rounds=4)

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

    def fake_web_search(query, config):
        calls.append(query)
        return {"summary": query, "citations": []}

    monkeypatch.setattr(search_core, "web_search", fake_web_search)

    search_core.deep_research("alpha beta gamma report", {}, max_rounds=100)

    assert len(calls) == 6


def test_deep_research_summary_includes_each_round(monkeypatch):
    summaries = {
        "best climate data report": " ".join(["original"] * 700),
        '"best climate data report"': "quoted marker",
        "best climate data report filetype:pdf": "pdf marker",
    }

    def fake_web_search(query, config):
        return {"summary": summaries[query], "citations": []}

    monkeypatch.setattr(search_core, "web_search", fake_web_search)

    response = search_core.deep_research("best climate data report", {}, max_rounds=3)

    assert "original" in response["summary"]
    assert "quoted marker" in response["summary"]
    assert "pdf marker" in response["summary"]


def test_skill_teaches_kbs_commands():
    skill = (
        Path(__file__).resolve().parents[2]
        / "skills"
        / "knowledge-based-search"
        / "SKILL.md"
    )
    text = skill.read_text(encoding="utf-8")

    for cmd in ["kbs quick", "kbs search", "kbs get", "kbs deep", "kbs context"]:
        assert cmd in text, f"{cmd} not found in SKILL.md"


def test_fetch_clean_smoke(monkeypatch):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exception_type, exception_value, traceback):
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

    capped = search_core._cap_chars(text, 12)

    assert capped == "alpha beta"
    assert len(capped) <= 12


def test_cap_chars_returns_short_input_unchanged():
    text = "alpha beta"

    assert search_core._cap_chars(text, 20) == text


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

    def fake_web_search(query, config):
        return {"summary": large_summary, "citations": citations}

    monkeypatch.setattr(search_core, "web_search", fake_web_search)

    response = search_core.deep_research("best climate data report", {}, max_rounds=1)

    assert len(response["summary"]) <= 4000
    assert all(len(section["content"]) <= 700 for section in response["sections"])
    assert len(response["citations"]) == 5
    assert len(json.dumps(response)) < 12000


def test_reformulate_pads_single_keyword_query():
    assert len(search_core._reformulate("best", 3)) == 3
