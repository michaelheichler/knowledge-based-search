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


_PUBMED_ESEARCH = json.dumps({"esearchresult": {"idlist": ["111"]}})
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


_SEMANTICSCHOLAR_PAYLOAD = json.dumps(
    {
        "data": [
            {
                "title": "A Paper",
                "url": "https://www.semanticscholar.org/paper/x",
                "abstract": "Paper abstract",
                "year": 2021,
                "citationCount": 42,
            }
        ]
    }
)


def test_semanticscholar_maps_citation_count(monkeypatch) -> None:
    """Semantic Scholar exposes citationCount directly; it must survive as an int."""
    monkeypatch.setattr(engines, "_get", lambda *_a, **_k: _SEMANTICSCHOLAR_PAYLOAD)

    hits = engines.semanticscholar("quantum computing", k=1)

    assert hits[0]["citation_count"] == 42
    assert isinstance(hits[0]["citation_count"], int)
    assert hits[0]["date"] == "2021-01-01"


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


def test_providers_filter_selects_scientific_only() -> None:
    """The providers frozenset narrows to exactly the named platforms."""
    tasks = engines._build_tasks("q", {}, 5, providers=frozenset({"arxiv", "pubmed"}))
    assert set(tasks) == {"arxiv", "pubmed"}

    tasks = engines._build_tasks(
        "q", {"bing": False}, 5, providers=frozenset({"bing", "arxiv"})
    )
    assert "bing" not in tasks
    assert "arxiv" in tasks
