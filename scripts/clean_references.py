#!/usr/bin/env python3
"""Drop empty-intensifier 'very' and delete skip-stub files so the reference library holds only real notes."""
import os
import re

ROOT = "/Users/michael/dev/skills/knowledge-based-search/skills/knowledge-based-search/references"
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
    for dirpath, _, names in os.walk(ROOT):
        for name in names:
            if not name.endswith(".md"):
                continue
            path = os.path.join(dirpath, name)
            text = open(path, encoding="utf-8").read()
            if "skipped: no tradecraft" in text:
                os.remove(path)
                deleted += 1
                continue
            cleaned = _clean(text)
            if cleaned != text:
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(cleaned)
                edited += 1
    print(f"deleted skip stubs: {deleted}")
    print(f"files de-intensified: {edited}")


if __name__ == "__main__":
    run()
