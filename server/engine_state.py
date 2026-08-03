"""Persist provider pacing and cooldown state across CLI invocations."""

import contextlib
import fcntl
import json
import os
import pathlib
import tempfile
from collections.abc import Iterator


PUBMED_EFETCH = "pubmed-efetch"


def _path() -> pathlib.Path:
    """Because overrides may change between calls, resolve the path each time."""
    override = os.environ.get("KBS_ENGINE_STATE")
    return (
        pathlib.Path(override).expanduser()
        if override
        else pathlib.Path.home() / ".cache" / "kbs" / "engine_state.json"
    )


def _load(path: pathlib.Path) -> dict:
    """Because local state is disposable, replace unreadable data with an empty map."""
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return {"providers": {}}
    if not isinstance(state, dict) or not isinstance(state.get("providers"), dict):
        return {"providers": {}}
    return state


def _write(path: pathlib.Path, state: dict) -> None:
    """Because readers run concurrently, publish only complete JSON documents."""
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=f"{path.name}.", suffix=".tmp"
    )
    temporary_path = pathlib.Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(state, handle, sort_keys=True)
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


@contextlib.contextmanager
def _locked_state() -> Iterator[tuple[pathlib.Path, dict]]:
    """Because replacement changes the state inode, lock a stable sibling file."""
    path = _path()
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_name(f"{path.name}.lock")
    with lock_path.open("a", encoding="utf-8") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        state = _load(path)
        yield path, state


def reserve_slot(provider: str, now: float, interval: float) -> float:
    """Reserve a future provider slot across concurrent CLI invocations."""
    with _locked_state() as (path, state):
        provider_state = state["providers"].get(provider)
        if not isinstance(provider_state, dict):
            provider_state = {}
            state["providers"][provider] = provider_state
        previous = provider_state.get("last_call", 0.0)
        if not isinstance(previous, (int, float)):
            previous = 0.0
        start = max(now, previous + interval)
        provider_state["last_call"] = start
        _write(path, state)
    return start


def block_provider(provider: str, blocked_until: float) -> None:
    """Persist a cooldown so new CLI processes do not prolong provider blocks."""
    with _locked_state() as (path, state):
        provider_state = state["providers"].get(provider)
        if not isinstance(provider_state, dict):
            provider_state = {}
            state["providers"][provider] = provider_state
        provider_state["blocked_until"] = blocked_until
        _write(path, state)


def cooling_down(providers, now: float) -> set[str]:
    """Find shared cooldowns so skipped providers remain visible to callers."""
    state = _load(_path())
    cooling = set()
    for provider in providers:
        provider_state = state["providers"].get(provider, {})
        if not isinstance(provider_state, dict):
            continue
        blocked_until = provider_state.get("blocked_until", 0.0)
        if isinstance(blocked_until, (int, float)) and blocked_until > now:
            cooling.add(provider)
    return cooling
