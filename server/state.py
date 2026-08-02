"""Persist KBS session state safely across CLI processes."""

import contextlib
import fcntl
import json
import os
import tempfile
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

DEFAULT_SESSION = "default"
# ponytail: 60 entries bounds context growth, raise it if long sessions lose useful history
SEEN_URL_CAP = 60
# ponytail: 50 references bounds state growth, raise it if callers retain older result IDs
RESULT_REF_CAP = 50


def resolve_session(session: str | None = None, env: dict | None = None) -> str:
    """Resolve an explicit or environment session to a stable identifier."""
    source = os.environ if env is None else env
    value = session or source.get("KBS_SESSION") or DEFAULT_SESSION
    return str(value).strip() or DEFAULT_SESSION


def state_file(env: dict | None = None) -> Path:
    """Return the configured state file path."""
    source = os.environ if env is None else env
    override = source.get("KBS_STATE_FILE")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".cache" / "knowledge-based-search" / "state.json"


def _empty_state() -> dict:
    return {"sessions": {}, "result_refs": {}}


def _load_path(path: Path) -> dict:
    """Corrupt or absent data becomes empty because search must survive state loss."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return _empty_state()
    except (OSError, json.JSONDecodeError):
        return _empty_state()
    return data if isinstance(data, dict) else _empty_state()


def load(env: dict | None = None) -> dict:
    """Load the latest atomically published state document."""
    return _load_path(state_file(env))


@contextlib.contextmanager
def _exclusive_lock(path: Path) -> Iterator[None]:
    """One sidecar lock is required because every process shares this transaction boundary."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_name(path.name + ".lock")
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
    os.chmod(lock_path, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def _save_path(path: Path, data: dict) -> None:
    """Atomic mode 0600 replacement is required because session state must stay complete and private."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        payload = json.dumps(data, sort_keys=True).encode("utf-8")
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    except Exception:
        with contextlib.suppress(OSError):
            os.close(fd)
        with contextlib.suppress(OSError):
            os.unlink(temporary)
        raise


def save(data: dict, env: dict | None = None) -> None:
    """Publish a complete state document under the transaction lock."""
    path = state_file(env)
    with _exclusive_lock(path):
        _save_path(path, data)


def _update(mutator: Callable[[dict], Any], env: dict | None = None) -> Any:
    """The lock spans reading and replacement because splitting them loses concurrent updates."""
    path = state_file(env)
    with _exclusive_lock(path):
        data = _load_path(path)
        result = mutator(data)
        _save_path(path, data)
        return result


def _entry(data: dict, session: str, key: str) -> dict:
    sessions = data.setdefault("sessions", {})
    keys = sessions.setdefault(session, {})
    return keys.setdefault(key, {"seen_urls": [], "issued_queries": []})


def get_context_memory(session: str | None = None, key: str = "", env: dict | None = None) -> dict:
    """Load context history for one session and memory key."""
    session_id = resolve_session(session, env)
    entry = _entry(load(env), session_id, key)
    return {
        "seen_urls": set(entry.get("seen_urls", [])),
        "issued_queries": list(entry.get("issued_queries", [])),
    }


def _recent(values, cap: int) -> list:
    """Insertion order defines recency because lexical sorting would retain stale values."""
    ordered = list(dict.fromkeys(values))
    return ordered[-cap:]


def save_context_memory(session: str | None, key: str, memory: dict, env: dict | None = None) -> None:
    """Merge and persist the newest bounded context history."""
    session_id = resolve_session(session, env)

    def mutate(data: dict) -> None:
        entry = _entry(data, session_id, key)
        old_seen = list(entry.get("seen_urls", []))
        incoming_seen = list(memory.get("seen_urls", []))
        additions = [url for url in incoming_seen if url not in old_seen]
        entry["seen_urls"] = _recent(old_seen + additions, SEEN_URL_CAP)
        old_queries = list(entry.get("issued_queries", []))
        incoming_queries = list(memory.get("issued_queries", []))
        query_additions = [item for item in incoming_queries if item not in old_queries]
        entry["issued_queries"] = _recent(old_queries + query_additions, SEEN_URL_CAP)

    _update(mutate, env)


def store_result_url(url: str, session: str | None = None, env: dict | None = None) -> str:
    """References stay scoped because sessions can reuse the same short identifiers."""
    session_id = resolve_session(session, env)

    def mutate(data: dict) -> str:
        sessions = data.setdefault("result_refs", {})
        refs = sessions.setdefault(session_id, {"next_id": 1, "items": []})
        ref = f"r{int(refs.get('next_id', 1))}"
        refs["next_id"] = int(refs.get("next_id", 1)) + 1
        refs["items"] = (list(refs.get("items", [])) + [[ref, url]])[-RESULT_REF_CAP:]
        return ref

    return _update(mutate, env)


def get_result_url(ref: str, session: str | None = None, env: dict | None = None) -> str | None:
    """Resolve a persisted result reference for one session."""
    session_id = resolve_session(session, env)
    refs = load(env).get("result_refs", {}).get(session_id, {})
    return dict(refs.get("items", [])).get(ref)


def clear_session(session: str | None = None, env: dict | None = None) -> None:
    """Remove context and result references for one session."""
    session_id = resolve_session(session, env)

    def mutate(data: dict) -> None:
        data.setdefault("sessions", {}).pop(session_id, None)
        data.setdefault("result_refs", {}).pop(session_id, None)

    _update(mutate, env)
