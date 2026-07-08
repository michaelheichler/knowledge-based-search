import importlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "server"))

search_core = importlib.import_module("search_core")


def test_search_core_uses_supplied_config(monkeypatch):
    calls = []

    def fake_search(query, config, k, cap):
        calls.append((query, config, k, cap))
        return [
            {
                "title": "Alpha guide",
                "url": "https://example.com/alpha",
                "snippet": "Alpha snippet",
                "engine": "searxng",
                "date": "2026-01-02",
                "relevance": 0.8,
            }
        ]

    monkeypatch.setattr(search_core.engines, "search", fake_search)
    monkeypatch.setattr(search_core.rag, "rank", lambda query, docs: list(docs))

    assert search_core.quick_web_search(
        "alpha", {"searxng_url": "https://search.example"}, num_results=1
    ) == {
        "results": [
            {
                "title": "Alpha guide",
                "url": "https://example.com/alpha",
                "snippet": "Alpha snippet",
                "engine": "searxng",
                "date": "2026-01-02",
                "relevance": 0.8,
            }
        ]
    }
    expected_calls = [("alpha", {"searxng_url": "https://search.example"}, 1, 1)]
    assert calls == expected_calls


def test_invalid_integer_inputs_still_raise():
    with pytest.raises(ValueError):
        search_core.quick_web_search("alpha", {}, num_results="bad")
    with pytest.raises(ValueError):
        search_core._reformulate("alpha", "bad")


def test_mcp_adapter_is_deleted():
    adapter = Path("server") / ("mcp" + "_server.py")
    assert not adapter.exists()


def test_core_extraction_static_boundaries():
    core_text = Path("server/search_core.py").read_text(encoding="utf-8")

    assert "StateBackend" not in core_text
    assert "TOOL_SCHEMAS" not in core_text
    assert "handle_json_rpc" not in core_text
    assert "FastMCP" not in core_text
