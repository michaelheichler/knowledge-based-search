"""Canned responses keep engine adapter tests independent of provider networks."""

import json

import engines


def test_mwmbl_parses_rich_text_segments(monkeypatch) -> None:
    """Mwmbl rich-text fragments must retain their original order."""
    payload = [
        {
            "url": "https://example.com/mwmbl",
            "title": [
                {"value": "Search ", "is_bold": False},
                {"value": "result", "is_bold": True},
            ],
            "extract": [{"value": "Useful "}, {"value": "extract"}],
        }
    ]
    monkeypatch.setattr(engines, "_get", lambda *_args, **_kwargs: json.dumps(payload))

    hits = engines.mwmbl("search terms", k=1)

    assert hits == [
        {
            "title": "Search result",
            "url": "https://example.com/mwmbl",
            "snippet": "Useful extract",
            "engine": "mwmbl",
            "rank": 1,
            "date": "",
        }
    ]


def test_wikipedia_builds_article_url_and_cleans_snippet(monkeypatch) -> None:
    """Wikipedia titles must become quoted article URLs and snippets must be plain text."""
    payload = {
        "query": {
            "search": [
                {
                    "title": "C++ / CLI",
                    "snippet": '<span class="searchmatch">Programming</span> language',
                }
            ]
        }
    }
    monkeypatch.setattr(engines, "_get", lambda *_args, **_kwargs: json.dumps(payload))

    hits = engines.wikipedia("C++ CLI", k=1)

    assert hits[0]["url"] == "https://en.wikipedia.org/wiki/C%2B%2B_%2F_CLI"
    assert hits[0]["snippet"] == "Programming language"
    assert hits[0]["engine"] == "wikipedia"


_TAVILY_PAYLOAD = {
    "results": [
        {
            "title": "Tavily result",
            "url": "https://example.com/tavily",
            "content": "Tavily content",
        }
    ]
}


def test_tavily_posts_key_and_parses_results(monkeypatch) -> None:
    """Tavily requires its key in the JSON request body rather than a query string."""
    calls = {}

    def fake_get(*args, **kwargs) -> str:
        """Because the request shape is contractual, retain it for assertions."""
        calls.update(args=args, kwargs=kwargs)
        return json.dumps(_TAVILY_PAYLOAD)

    monkeypatch.setattr(engines, "_get", fake_get)
    hits = engines.tavily("query", k=3, config={"tavily_api_key": "secret"})

    assert calls["args"][:2] == ("https://api.tavily.com/search", engines._TIMEOUT)
    assert json.loads(calls["kwargs"]["data"]) == {
        "api_key": "secret",
        "query": "query",
        "max_results": 3,
    }
    assert calls["kwargs"]["headers"] == {"Content-Type": "application/json"}
    assert hits[0]["snippet"] == "Tavily content"
    assert hits[0]["engine"] == "tavily"


def test_tavily_tasks_require_api_key() -> None:
    """A missing Tavily key must prevent any Tavily task from being scheduled."""
    config = {"duckduckgo": False, "mwmbl": False, "wikipedia": False}
    assert "tavily" not in engines._build_tasks("query", config, 1)

    config["tavily_api_key"] = "secret"
    assert "tavily" in engines._build_tasks("query", config, 1)


_ARXIV_ATOM = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
<entry>
<id>http://arxiv.org/abs/2001.00001v1</id>
<title>  A Title
    With A Newline </title>
<summary>An abstract.</summary>
<published>2000-11-15T16:19:15Z</published>
</entry>
</feed>
"""


def test_arxiv_parses_atom_entries(monkeypatch) -> None:
    """arXiv titles wrap across lines in the raw Atom XML and must collapse to one line."""
    monkeypatch.setattr(engines, "_get", lambda *_args, **_kwargs: _ARXIV_ATOM)

    hits = engines.arxiv("electron", k=1)

    assert hits == [
        {
            "title": "A Title With A Newline",
            "url": "http://arxiv.org/abs/2001.00001v1",
            "snippet": "An abstract.",
            "engine": "arxiv",
            "rank": 1,
            "date": "2000-11-15",
        }
    ]


_ARXIV_CATEGORIZED_ATOM = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
<entry>
<id>http://arxiv.org/abs/2001.00002v1</id>
<title>Categorized Paper</title>
<summary>Abstract.</summary>
<published>2000-11-15T16:19:15Z</published>
<category term="stat.ML" scheme="http://arxiv.org/schemas/atom"/>
<category term="cs.LG" scheme="http://arxiv.org/schemas/atom"/>
</entry>
</feed>
"""


def test_arxiv_captures_all_native_categories(monkeypatch) -> None:
    """Every Atom category term should survive as a hit category."""
    monkeypatch.setattr(engines, "_get", lambda *_args, **_kwargs: _ARXIV_CATEGORIZED_ATOM)

    hits = engines.arxiv("electron", k=1)

    assert hits[0]["categories"] == ["stat.ML", "cs.LG"]


_PUBMED_ESEARCH = json.dumps({"esearchresult": {"idlist": ["111"]}})

_PUBMED_EFETCH = """<PubmedArticleSet>
<PubmedArticle>
<MedlineCitation>
<PMID>111</PMID>
<MeshHeadingList>
<MeshHeading><DescriptorName>Chronic Disease</DescriptorName></MeshHeading>
<MeshHeading><DescriptorName>Diabetes Mellitus</DescriptorName></MeshHeading>
</MeshHeadingList>
</MedlineCitation>
</PubmedArticle>
</PubmedArticleSet>
"""


_SEMANTICSCHOLAR_PAYLOAD = json.dumps(
    {
        "data": [
            {
                "title": "A Paper",
                "url": "https://www.semanticscholar.org/paper/x",
                "abstract": "Paper abstract",
                "year": 2021,
                "citationCount": 42,
                "fieldsOfStudy": ["Computer Science", "Medicine"],
            }
        ]
    }
)


_CROSSREF_UNCATEGORIZED = json.dumps(
    {
        "message": {
            "items": [
                {
                    "title": ["An Uncategorized Work"],
                    "URL": "https://doi.org/10.1/uncategorized",
                    "subject": [],
                },
                {
                    "title": ["An Absent Category Work"],
                    "URL": "https://doi.org/10.1/absent",
                },
            ]
        }
    }
)
_PUBMED_ESUMMARY = json.dumps(
    {"result": {"111": {"title": "A Pubmed Title", "source": "J Test", "pubdate": "2024 Jan 15"}}}
)


def test_pubmed_two_call_flow(monkeypatch) -> None:
    """PubMed needs esearch for PMIDs then esummary for metadata, in that order."""
    calls = []

    def fake_get(*args, **_kwargs) -> str:
        calls.append(args[0])
        return _PUBMED_ESEARCH if len(calls) == 1 else _PUBMED_ESUMMARY

    monkeypatch.setattr(engines, "_get", fake_get)
    hits = engines.pubmed("cancer", k=1)

    assert "esearch.fcgi" in calls[0] and "retmax" in calls[0]
    assert "esummary.fcgi" in calls[1] and "111" in calls[1]
    assert hits[0]["url"] == "https://pubmed.ncbi.nlm.nih.gov/111/"
    assert hits[0]["date"] == "2024-01-15"


def test_pubmed_maps_mesh_headings_to_categories(monkeypatch) -> None:
    """The batched efetch response contributes descriptor names to each hit."""
    calls = []
    responses = [_PUBMED_ESEARCH, _PUBMED_ESUMMARY, _PUBMED_EFETCH]

    def fake_get(url, *_args, **_kwargs) -> str:
        calls.append(url)
        return responses.pop(0)

    monkeypatch.setattr(engines, "_get", fake_get)
    monkeypatch.setattr(engines, "_reserve_slot", lambda *_args: 0.0)

    hits = engines.pubmed("cancer", k=1)

    assert "efetch.fcgi" in calls[2]
    assert hits[0]["categories"] == ["Chronic Disease", "Diabetes Mellitus"]


def test_pubmed_zero_mesh_headings_is_uncategorized(monkeypatch) -> None:
    """Records without an indexed MeshHeadingList remain usable hits."""
    responses = [_PUBMED_ESEARCH, _PUBMED_ESUMMARY, "<PubmedArticleSet/>"]

    def fake_get(*_args, **_kwargs) -> str:
        return responses.pop(0)

    monkeypatch.setattr(engines, "_get", fake_get)
    monkeypatch.setattr(engines, "_reserve_slot", lambda *_args: 0.0)

    hits = engines.pubmed("cancer", k=1)

    assert "categories" not in hits[0]


def test_pubmed_mesh_failure_is_uncategorized(monkeypatch) -> None:
    """An efetch failure should not discard summary hits."""
    calls = []

    def fake_get(url, *_args, **_kwargs) -> str:
        calls.append(url)
        if len(calls) == 3:
            raise OSError("efetch unavailable")
        return _PUBMED_ESEARCH if len(calls) == 1 else _PUBMED_ESUMMARY

    monkeypatch.setattr(engines, "_get", fake_get)
    monkeypatch.setattr(engines, "_reserve_slot", lambda *_args: 0.0)

    hits = engines.pubmed("cancer", k=1)

    assert len(hits) == 1
    assert "categories" not in hits[0]


def test_pubmed_empty_idlist_skips_esummary(monkeypatch) -> None:
    """An empty esearch result must not trigger a wasted esummary round trip."""
    calls = []

    def fake_get(*args, **_kwargs) -> str:
        calls.append(args[0])
        return json.dumps({"esearchresult": {"idlist": []}})

    monkeypatch.setattr(engines, "_get", fake_get)
    hits = engines.pubmed("no results query", k=1)

    assert hits == []
    assert len(calls) == 1


def test_semanticscholar_maps_citation_count(monkeypatch) -> None:
    """Semantic Scholar exposes citationCount directly; it must survive as an int."""
    monkeypatch.setattr(engines, "_get", lambda *_a, **_k: _SEMANTICSCHOLAR_PAYLOAD)

    hits = engines.semanticscholar("quantum computing", k=1)

    assert hits[0]["citation_count"] == 42
    assert isinstance(hits[0]["citation_count"], int)
    assert hits[0]["date"] == "2021-01-01"
    assert hits[0]["categories"] == ["Computer Science", "Medicine"]


def test_semanticscholar_missing_fields_of_study_is_uncategorized(monkeypatch) -> None:
    """A null native field should leave the hit uncategorized without an error."""
    payload = _SEMANTICSCHOLAR_PAYLOAD.replace(
        '["Computer Science", "Medicine"]', "null"
    )
    monkeypatch.setattr(engines, "_get", lambda *_a, **_k: payload)

    hits = engines.semanticscholar("quantum computing", k=1)

    assert "categories" not in hits[0]


_CROSSREF_PAYLOAD = json.dumps(
    {
        "message": {
            "items": [
                {
                    "title": ["A Crossref Work"],
                    "URL": "https://doi.org/10.1/x",
                    "author": [{"family": "Doe"}],
                    "container-title": ["Journal Of Tests"],
                    "issued": {"date-parts": [[2019]]},
                    "is-referenced-by-count": 7,
                },
                {"URL": "https://doi.org/10.1/y", "is-referenced-by-count": 3},
            ]
        }
    }
)


def test_crossref_parses_date_parts_and_citations(monkeypatch) -> None:
    """date-parts is a nested structure, not free text, and a titleless record must be skipped."""
    monkeypatch.setattr(engines, "_get", lambda *_a, **_k: _CROSSREF_PAYLOAD)

    hits = engines.crossref("machine learning", k=5)

    assert len(hits) == 1
    assert hits[0]["date"] == "2019-01-01"
    assert hits[0]["citation_count"] == 7


def test_crossref_empty_or_absent_subject_is_uncategorized(monkeypatch) -> None:
    """Sparse CrossRef subject metadata should remain a normal uncategorized result."""
    monkeypatch.setattr(engines, "_get", lambda *_a, **_k: _CROSSREF_UNCATEGORIZED)

    hits = engines.crossref("machine learning", k=2)

    assert len(hits) == 2
    assert all("categories" not in hit for hit in hits)


def test_providers_filter_selects_scientific_only() -> None:
    """The providers frozenset narrows to exactly the named platforms."""
    tasks = engines._build_tasks("q", {}, 5, providers=frozenset({"arxiv", "pubmed"}))
    assert set(tasks) == {"arxiv", "pubmed"}

    tasks = engines._build_tasks(
        "q", {"bing": False}, 5, providers=frozenset({"bing", "arxiv"})
    )
    assert "bing" not in tasks
    assert "arxiv" in tasks


def _queue_mcp_responses(monkeypatch, responses) -> list:
    calls = []

    def fake_post(*args, **kwargs) -> tuple:
        calls.append(
            (*args, kwargs.get("session_id"), kwargs.get("timeout", engines._TIMEOUT))
        )
        return responses.pop(0)

    monkeypatch.setattr(engines, "_mcp_post", fake_post)
    return calls


def test_library_handshake_sequence_and_auth(monkeypatch) -> None:
    """MCP requires initialization and the returned session on later messages."""
    responses = [
        (json.dumps({"jsonrpc": "2.0", "id": 1}), {"mcp-session-id": "abc"}),
        ("", {}),
        ("data: " + json.dumps({"jsonrpc": "2.0", "result": {"content": [{"text": json.dumps({"passages": []})}]}}), {}),
    ]
    calls = _queue_mcp_responses(monkeypatch, responses)
    engines.library(
        "defensive design", k=3, timeout=4,
        config={"library_mcp_url": "http://library/mcp", "library_mcp_token": "secret"},
    )
    assert [call[2]["method"] for call in calls] == ["initialize", "notifications/initialized", "tools/call"]
    assert all(call[1] == "secret" for call in calls)
    assert [call[3] for call in calls] == [None, "abc", "abc"]
    assert calls[0][2]["params"]["protocolVersion"] == "2025-03-26"
    assert calls[2][2]["params"] == {"name": "search_library", "arguments": {"query": "defensive design", "k": 3}}


def _library_sse_response() -> str:
    payload = {
        "passages": [
            {"chunk_id": "sentient-design-1", "book_id": "sentient-design", "book_title": "The Sentient Design", "chapter_title": "Defensive Design", "text": "x" * 301, "confidence": "high"},
            {"chunk_id": "sentient-design-2", "book_id": "sentient-design", "book_title": "The Sentient Design", "chapter_title": "Design Rules", "text": "A shorter passage."},
        ]
    }
    body = {"jsonrpc": "2.0", "result": {"content": [{"text": json.dumps(payload)}]}}
    return "event: message\n" + f"data: {json.dumps(body)}\n"


def test_library_parses_sse_passages(monkeypatch) -> None:
    """SSE passages become capped, confidence-free library hits."""
    responses = [("{}", {"MCP-SESSION-ID": "abc"}), ("", {}), (_library_sse_response(), {})]
    _queue_mcp_responses(monkeypatch, responses)
    hits = engines.library(
        "design", k=2,
        config={"library_mcp_url": "http://library/mcp", "library_mcp_token": "secret"},
    )
    assert len(hits) == 2
    assert [hit["url"] for hit in hits] == ["library://sentient-design?chunk=sentient-design-1", "library://sentient-design?chunk=sentient-design-2"]
    assert all(hit["engine"] == "library" for hit in hits)
    assert len(hits[0]["snippet"]) == 300
    assert "confidence" not in hits[0]



def test_library_urls_survive_merge_dedup() -> None:
    """Distinct library chunks must remain distinct after URL normalization."""
    hits = [
        engines.result("One", "library://book?chunk=one", "first", "library", 1),
        engines.result("Two", "library://book?chunk=two", "second", "library", 2),
    ]

    merged = engines.merge([hits])

    assert len(merged) == 2
    assert engines.norm_url(hits[0]["url"]) != engines.norm_url(hits[1]["url"])


def test_library_never_in_task_fanout() -> None:
    """The private library call must not enter paced provider task fan-out."""
    tasks = engines._build_tasks(
        "q",
        {"library_mcp_url": "http://x", "library_mcp_token": "t"},
        5,
        providers=frozenset({"library"}),
    )

    assert "library" not in tasks
