"""Provide the server import path for server tests."""

import sys
from pathlib import Path

_SERVER = str(Path(__file__).resolve().parents[1])
if _SERVER not in sys.path:
    sys.path.insert(0, _SERVER)
