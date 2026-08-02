"""Provide shared import paths for repository tests."""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
for _directory in (_ROOT / "server", _ROOT / "hooks"):
    _path = str(_directory)
    if _path not in sys.path:
        sys.path.insert(0, _path)
