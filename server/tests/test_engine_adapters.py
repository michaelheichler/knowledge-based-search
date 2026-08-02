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
