import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import search_core
from fetch import fetch_clean


def _hits() -> object:
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


def _duplicate_hit() -> object:
    return {
        "title": "Alpha duplicate",
        "url": "https://example.com/a",
        "snippet": "Duplicate alpha",
        "engine": "searxng",
        "rank": 3,
        "engines": ["searxng"],
    }


@pytest.fixture
def stubs(monkeypatch) -> object:
    calls = {"search": [], "fetch": []}

    def fake_search(query, config, **options) -> object:
        calls["search"].append(
            {"query": query, "k": options["k"], "cap": options["cap"]}
        )
        rows = _hits()
        if "Alpha guide" in query:
            rows.append(_duplicate_hit())
        return rows

    def fake_rank(query, docs) -> object:
        return list(docs)

    def fake_fetch_clean(url, max_chars) -> object:
        calls["fetch"].append((url, max_chars))
        return ("content from " + url + " ") * 80

    monkeypatch.setattr(search_core.engines, "search", fake_search)
    monkeypatch.setattr(search_core.rag, "rank", fake_rank)
    monkeypatch.setattr(search_core, "fetch_clean", fake_fetch_clean)
    search_core.RESULT_URLS.clear()
    return calls


def test_quick_web_search_schema(stubs) -> object:
    response = search_core.quick_web_search("alpha", {}, num_results=2)

    assert set(response) == {"query", "results", "corrections", "quality"}
    assert [item["title"] for item in response["results"]] == [
        "Alpha guide",
        "Beta notes",
    ]
    assert all(item["confidence"] == "unknown" for item in response["results"])
    assert stubs["fetch"] == []


def test_quick_web_search_clamps_schema_limit(stubs) -> object:
    search_core.quick_web_search("alpha", {}, num_results=25)

    assert stubs["search"][0]["k"] == 20
    assert stubs["search"][0]["cap"] == 20


def test_web_search_schema_citations_and_token_bound(stubs) -> object:
    response = search_core.web_search("alpha", {}, num_results=2)

    assert set(response) == {
        "query",
        "summary",
        "citations",
        "result_ids",
        "corrections",
        "quality",
    }
    assert len(response["result_ids"]) == 2
    assert len(response["summary"].split()) <= 1000
    assert [item["title"] for item in response["citations"]] == [
        "Alpha guide",
        "Beta notes",
    ]
    assert all(item["confidence"] == "unknown" for item in response["citations"])


def test_web_search_clamps_schema_limit(stubs) -> object:
    search_core.web_search("alpha", {}, num_results=12)

    assert stubs["search"][0]["k"] == 10
    assert stubs["search"][0]["cap"] == 10


def test_get_content_resolves_result_id(stubs) -> object:
    result = search_core.web_search("alpha", {}, num_results=1)
    content = search_core.get_content(result["result_ids"][0])

    assert content["source_url"] == "https://example.com/a"
    assert content["page_content"].startswith("content from https://example.com/a")


def test_reformulate_quotes_multiword_query() -> object:
    assert search_core._reformulate("climate data", 3)[0] == '"climate data"'


def test_reformulate_adds_pdf_for_document_token() -> object:
    assert "openai annual report data filetype:pdf" in search_core._reformulate(
        "openai annual report data", 3
    )


def test_reformulate_does_not_match_document_token_substrings() -> object:
    assert all(
        "filetype:pdf" not in result
        for result in search_core._reformulate("best vector database 2026", 3)
    )


def test_reformulate_respects_limit_and_never_returns_original() -> object:
    results = search_core._reformulate("best climate data report", 2)

    assert results == [
        '"best climate data report"',
        "best climate data report filetype:pdf",
    ]
    assert "best climate data report" not in results


def test_reformulate_broadens_query() -> object:
    assert (
        search_core._reformulate("top climate data report", 3)[2]
        == "climate data report"
    )
    assert (
        search_core._reformulate("climate data report 2025", 3)[2]
        == "climate data report"
    )


_EXPECTED_DEEP_QUERIES = [
    "best climate data report",
    '"best climate data report"',
    "best climate data report filetype:pdf",
    "climate data report",
]


def test_deep_research_bounded_and_deduped(monkeypatch) -> object:
    calls = []

    def fake_web_search(query, config) -> object:
        calls.append(query)
        citation = {"title": query, "url": "https://same.example/report"}
        return {"summary": f"summary for {query}", "citations": [citation]}

    monkeypatch.setattr(search_core, "web_search", fake_web_search)
    response = search_core.deep_research("best climate data report", {}, max_rounds=4)

    assert {"corrections", "quality"} <= set(response)
    assert calls == _EXPECTED_DEEP_QUERIES
    assert [item["url"] for item in response["citations"]] == [
        "https://same.example/report"
    ]
    assert len(response["sections"]) == 4


def test_deep_research_clamps_max_rounds(monkeypatch) -> object:
    calls = []

    def fake_web_search(query, config) -> object:
        calls.append(query)
        return {"summary": query, "citations": []}

    monkeypatch.setattr(search_core, "web_search", fake_web_search)

    search_core.deep_research("alpha beta gamma report", {}, max_rounds=100)

    assert len(calls) == 6


def test_deep_research_summary_includes_each_round(monkeypatch) -> object:
    summaries = {
        "best climate data report": " ".join(["original"] * 700),
        '"best climate data report"': "quoted marker",
        "best climate data report filetype:pdf": "pdf marker",
    }

    def fake_web_search(query, config) -> object:
        return {"summary": summaries[query], "citations": []}

    monkeypatch.setattr(search_core, "web_search", fake_web_search)

    response = search_core.deep_research("best climate data report", {}, max_rounds=3)

    assert "original" in response["summary"]
    assert "quoted marker" in response["summary"]
    assert "pdf marker" in response["summary"]


def test_skill_teaches_kbs_commands() -> object:
    skill = (
        Path(__file__).resolve().parents[2]
        / "skills"
        / "knowledge-based-search"
        / "SKILL.md"
    )
    text = skill.read_text(encoding="utf-8")

    for cmd in ["kbs quick", "kbs search", "kbs get", "kbs deep", "kbs context"]:
        assert cmd in text, f"{cmd} not found in SKILL.md"


def test_fetch_clean_smoke(monkeypatch) -> object:
    class FakeResponse:
        def __enter__(self) -> object:
            return self

        def __exit__(self, *exception_info) -> object:
            return False

        def read(self, size) -> object:
            return b"<html><body><main><p>Example Domain</p></main></body></html>"

    def fake_urlopen(request, timeout) -> object:
        assert timeout == 10
        return FakeResponse()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    content = fetch_clean("https://example.com", 2000)

    assert "Example Domain" in content


def test_cap_chars_trims_without_splitting_word() -> object:
    text = "alpha beta gamma"

    capped = search_core._cap_chars(text, 12)

    assert capped == "alpha beta"
    assert len(capped) <= 12


def test_cap_chars_returns_short_input_unchanged() -> object:
    text = "alpha beta"

    assert search_core._cap_chars(text, 20) == text


def test_deep_research_caps_large_output_and_keeps_citations(monkeypatch) -> object:
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

    def fake_web_search(query, config) -> object:
        return {"summary": large_summary, "citations": citations}

    monkeypatch.setattr(search_core, "web_search", fake_web_search)

    response = search_core.deep_research("best climate data report", {}, max_rounds=1)

    assert len(response["summary"]) <= 4000
    assert all(len(section["content"]) <= 700 for section in response["sections"])
    assert len(response["citations"]) == 5
    assert len(json.dumps(response)) < 12000


def test_reformulate_pads_single_keyword_query() -> object:
    assert len(search_core._reformulate("best", 3)) == 3


def _run_cli(root, environment, *arguments):
    return subprocess.run(
        [sys.executable, str(root / "bin/kbs"), *arguments],
        cwd=root,
        env={**os.environ, **environment},
        capture_output=True,
        text=True,
        timeout=45,
        check=False,
    )


def _require_network_result(completed, label) -> None:
    if completed.returncode == 4:
        pytest.skip(f"{label} network unavailable: {completed.stderr.strip()}")
    assert completed.returncode == 0, completed.stderr


@pytest.mark.integration
def test_result_reference_survives_separate_cli_processes(tmp_path) -> None:
    if os.environ.get("KBS_OFFLINE") == "1":
        pytest.skip("KBS_OFFLINE=1")

    root = Path(__file__).resolve().parents[2]
    environment = {
        "KBS_CONFIG": json.dumps({"duckduckgo": True}),
        "KBS_STATE_FILE": str(tmp_path / "state.json"),
    }

    search = _run_cli(root, environment, "search", "python documentation", "--json")
    _require_network_result(search, "search")
    payload = json.loads(search.stdout)
    if not payload.get("citations"):
        pytest.skip("DuckDuckGo returned no results")
    assert payload.get("result_ids")

    fetched = _run_cli(root, environment, "get", payload["result_ids"][0], "--json")
    _require_network_result(fetched, "fetch")
    assert json.loads(fetched.stdout)["page_content"].strip()
