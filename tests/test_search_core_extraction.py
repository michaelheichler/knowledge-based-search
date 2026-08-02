import importlib
from pathlib import Path

import pytest

search_core = importlib.import_module("search_core")


def test_search_core_uses_supplied_config(monkeypatch) -> None:
    calls = []
    hit = {
        "title": "Alpha guide",
        "url": "https://example.com/alpha",
        "snippet": "Alpha snippet",
        "engine": "searxng",
    }

    def fake_search(query, config, **options) -> list:
        calls.append((query, config, options["k"], options["cap"]))
        return [hit]

    monkeypatch.setattr(search_core.engines, "search", fake_search)
    monkeypatch.setattr(search_core.rag, "rank", lambda query, docs: list(docs))
    config = {"searxng_url": "https://search.example"}

    response = search_core.quick_web_search("alpha", config, num_results=1)

    assert response["results"][0]["title"] == "Alpha guide"
    assert response["corrections"] == []
    assert calls == [("alpha", config, 1, 1)]


def test_invalid_integer_inputs_still_raise() -> None:
    with pytest.raises(ValueError):
        search_core.quick_web_search("alpha", {}, num_results="bad")
    with pytest.raises(ValueError):
        search_core._reformulate("alpha", "bad")


def test_mcp_adapter_is_deleted() -> None:
    adapter = Path("server") / ("mcp" + "_server.py")
    assert not adapter.exists()


def test_core_extraction_static_boundaries() -> None:
    core_text = Path("server/search_core.py").read_text(encoding="utf-8")

    assert "StateBackend" not in core_text
    assert "TOOL_SCHEMAS" not in core_text
    assert "handle_json_rpc" not in core_text
    assert "FastMCP" not in core_text
