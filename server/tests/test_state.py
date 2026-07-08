import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
state = importlib.import_module("state")


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
