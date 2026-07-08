#!/usr/bin/env python3
# ruff: noqa
"""Clean generated reference notes in place."""

import re
from pathlib import Path

ROOT = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "knowledge-based-search"
    / "references"
)
_SUBS = [
    (re.compile(r"\b(?:very|extremely|really|quite)\s+", re.IGNORECASE), ""),
    (re.compile(r"\bin order to\b", re.IGNORECASE), "to"),
    (re.compile(r"\butilized\b", re.IGNORECASE), "used"),
    (re.compile(r"\butilize\b", re.IGNORECASE), "use"),
]


def _clean(text):
    for pattern, repl in _SUBS:
        text = pattern.sub(repl, text)
    return text


def run():
    deleted = 0
    edited = 0
    for path in ROOT.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        if "skipped: no tradecraft" in text:
            path.unlink()
            deleted += 1
            continue
        cleaned = _clean(text)
        if cleaned != text:
            path.write_text(cleaned, encoding="utf-8")
            edited += 1
    print(f"deleted skip stubs: {deleted}")
    print(f"files de-intensified: {edited}")


if __name__ == "__main__":
    run()
