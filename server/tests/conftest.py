"""Provide the server import path for server tests."""

import sys
from pathlib import Path

import pytest

_SERVER = str(Path(__file__).resolve().parents[1])
if _SERVER not in sys.path:
    sys.path.insert(0, _SERVER)


@pytest.fixture(autouse=True)
def isolated_engine_state(monkeypatch, tmp_path) -> None:
    """Because provider state is durable, tests must not share or alter user state."""
    monkeypatch.setenv("KBS_ENGINE_STATE", str(tmp_path / "engine_state.json"))
