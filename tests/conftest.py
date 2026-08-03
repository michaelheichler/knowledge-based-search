"""Provide shared import paths and isolated provider state for repository tests."""

import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
for _directory in (_ROOT / "server", _ROOT / "hooks"):
    _path = str(_directory)
    if _path not in sys.path:
        sys.path.insert(0, _path)

import engines


@pytest.fixture(autouse=True)
def _reset_provider_state(monkeypatch, tmp_path):
    """Keep cache and persisted cooldown state from crossing test boundaries."""
    monkeypatch.setenv("KBS_ENGINE_STATE", str(tmp_path / "engine_state.json"))
    with engines._pace_lock:
        engines._query_cache.clear()
    yield
    with engines._pace_lock:
        engines._query_cache.clear()
