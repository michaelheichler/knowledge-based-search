import json
import os
from pathlib import Path

DEFAULT_SESSION = "default"
SEEN_URL_CAP = 60


def resolve_session(session: str | None = None, env: dict | None = None) -> str:
    source = os.environ if env is None else env
    value = session or source.get("KBS_SESSION") or DEFAULT_SESSION
    return str(value).strip() or DEFAULT_SESSION


def state_file(env: dict | None = None) -> Path:
    source = os.environ if env is None else env
    override = source.get("KBS_STATE_FILE")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".cache" / "knowledge-based-search" / "state.json"


def load(env: dict | None = None) -> dict:
    path = state_file(env)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"sessions": {}}
    except (OSError, json.JSONDecodeError):
        return {"sessions": {}}


def save(data: dict, env: dict | None = None) -> None:
    path = state_file(env)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, sort_keys=True), encoding="utf-8")


def _entry(data: dict, session: str, key: str) -> dict:
    sessions = data.setdefault("sessions", {})
    keys = sessions.setdefault(session, {})
    return keys.setdefault(key, {"seen_urls": [], "issued_queries": []})


def get_context_memory(
    session: str | None = None, key: str = "", env: dict | None = None
) -> dict:
    session_id = resolve_session(session, env)
    data = load(env)
    entry = _entry(data, session_id, key)
    return {
        "seen_urls": set(entry.get("seen_urls", [])),
        "issued_queries": list(entry.get("issued_queries", [])),
    }


def save_context_memory(
    session: str | None, key: str, memory: dict, env: dict | None = None
) -> None:
    session_id = resolve_session(session, env)
    data = load(env)
    entry = _entry(data, session_id, key)
    entry["seen_urls"] = sorted(memory.get("seen_urls", set()))[:SEEN_URL_CAP]
    entry["issued_queries"] = list(memory.get("issued_queries", []))[:SEEN_URL_CAP]
    save(data, env)


def clear_session(session: str | None = None, env: dict | None = None) -> None:
    session_id = resolve_session(session, env)
    data = load(env)
    data.setdefault("sessions", {}).pop(session_id, None)
    save(data, env)
