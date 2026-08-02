import importlib
import os
import stat
from pathlib import Path

state = importlib.import_module("state")
search_core = importlib.import_module("search_core")


def test_resolve_session_precedence():
    env = {"KBS_SESSION": "env-session"}

    assert state.resolve_session("explicit", env) == "explicit"
    assert state.resolve_session(None, env) == "env-session"
    assert state.resolve_session(None, {}) == "default"


def test_state_file_default_and_override(tmp_path, monkeypatch):
    override = tmp_path / "state.json"

    assert state.state_file({"KBS_STATE_FILE": str(override)}) == override

    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
    assert state.state_file({}) == (
        tmp_path / ".cache" / "knowledge-based-search" / "state.json"
    )


def test_context_memory_persists_and_clears_one_session(tmp_path):
    env = {"KBS_STATE_FILE": str(tmp_path / "state.json")}
    memory = {"seen_urls": {"https://a.example"}, "issued_queries": ["alpha"]}

    state.save_context_memory("s1", "ctx", memory, env)
    state.save_context_memory("s2", "ctx", memory, env)

    assert state.get_context_memory("s1", "ctx", env) == memory
    state.clear_session("s1", env)
    assert state.get_context_memory("s1", "ctx", env) == {
        "seen_urls": set(),
        "issued_queries": [],
    }
    assert state.get_context_memory("s2", "ctx", env) == memory


def test_seen_urls_are_capped_on_save(tmp_path):
    env = {"KBS_STATE_FILE": str(tmp_path / "state.json")}
    memory = {
        "seen_urls": {f"https://{index}.example" for index in range(80)},
        "issued_queries": [str(index) for index in range(80)],
    }

    state.save_context_memory("s1", "ctx", memory, env)
    data = state.load(env)
    entry = data["sessions"]["s1"]["ctx"]

    assert len(entry["seen_urls"]) == state.SEEN_URL_CAP
    assert len(entry["issued_queries"]) == state.SEEN_URL_CAP


def test_context_caps_keep_most_recent_values(tmp_path):
    env = {"KBS_STATE_FILE": str(tmp_path / "state.json")}
    for index in range(state.SEEN_URL_CAP + 5):
        memory = state.get_context_memory("s1", "ctx", env)
        memory["seen_urls"].add(f"https://{index}.example")
        memory["issued_queries"].append(str(index))
        state.save_context_memory("s1", "ctx", memory, env)

    entry = state.load(env)["sessions"]["s1"]["ctx"]
    assert entry["issued_queries"] == [str(index) for index in range(5, 65)]
    assert "https://0.example" not in entry["seen_urls"]
    assert "https://64.example" in entry["seen_urls"]


def test_atomic_save_uses_same_directory_replace_and_private_mode(tmp_path, monkeypatch):
    path = tmp_path / "state.json"
    env = {"KBS_STATE_FILE": str(path)}
    calls = []
    replace = state.os.replace

    def observe(source, destination):
        calls.append((Path(source), Path(destination)))
        replace(source, destination)

    monkeypatch.setattr(state.os, "replace", observe)
    state.save({"sessions": {}}, env)

    assert calls and calls[0][0].parent == path.parent
    assert calls[0][1] == path
    assert stat.S_IMODE(os.stat(path).st_mode) == 0o600


def test_result_refs_are_session_scoped_and_bounded(tmp_path):
    env = {"KBS_STATE_FILE": str(tmp_path / "state.json")}
    refs = [state.store_result_url(f"https://{index}.example", "s1", env) for index in range(55)]
    other = state.store_result_url("https://other.example", "s2", env)

    assert refs[0] == "r1" and refs[-1] == "r55"
    assert state.get_result_url("r1", "s1", env) is None
    assert state.get_result_url("r55", "s1", env) == "https://54.example"
    assert other == "r1"
    assert state.get_result_url("r1", "s2", env) == "https://other.example"


def test_quick_json_data_includes_merged_provenance(monkeypatch):
    hit = {
        "title": "Merged",
        "url": "https://merged.example",
        "snippet": "snippet",
        "engine": "searxng",
        "engines": ["searxng", "duckduckgo"],
        "date": "",
    }
    outcomes = {
        "searxng": {"status": "ok", "count": 1},
        "duckduckgo": {"status": "ok", "count": 1},
    }
    hits = search_core.engines.SearchResults([hit], outcomes)
    monkeypatch.setattr(search_core.engines, "search", lambda *args, **kwargs: hits)
    monkeypatch.setattr(search_core.rag, "rank", lambda query, rows: rows)

    data = search_core.quick_web_search("query", {}, 1)

    assert data["results"][0]["engines"] == ["searxng", "duckduckgo"]
    assert data["providers"] == outcomes


def test_in_process_result_refs_do_not_collide_between_sessions(tmp_path, monkeypatch):
    monkeypatch.setenv("KBS_STATE_FILE", str(tmp_path / "state.json"))
    monkeypatch.setattr(search_core, "fetch_clean", lambda url, limit: url)
    search_core.RESULT_URLS.clear()

    first = search_core._store_result("https://first.example", "s1")
    second = search_core._store_result("https://second.example", "s2")

    assert first == second == "r1"
    assert search_core.get_content(first, "s1")["source_url"] == "https://first.example"
    assert search_core.get_content(second, "s2")["source_url"] == "https://second.example"


def test_result_ref_survives_module_memory_reset(tmp_path, monkeypatch):
    monkeypatch.setenv("KBS_STATE_FILE", str(tmp_path / "state.json"))
    monkeypatch.setattr(search_core, "fetch_clean", lambda url, limit: "persisted page")
    search_core.RESULT_URLS.clear()
    ref = search_core._store_result("https://persisted.example/page")

    search_core.RESULT_URLS.clear()
    importlib.reload(state)

    assert search_core.get_content(ref) == {
        "source_url": "https://persisted.example/page",
        "page_content": "persisted page",
    }
