#!/usr/bin/env python3
"""Match a user prompt against the shared trigger vocabulary and return a firm search nudge."""
import json
import os
import re

_TRIGGERS_PATH = os.path.join(os.path.dirname(__file__), "triggers.json")
_ROUTE_PRIORITY = ("deep", "research", "recency")


def load_triggers(path=_TRIGGERS_PATH):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _hit(prompt, spec):
    low = prompt.lower()
    if any(word in low for word in spec.get("words", [])):
        return True
    return any(re.search(pat, prompt, re.IGNORECASE) for pat in spec.get("patterns", []))


def nudge_for(prompt, triggers=None):
    """Return a directive nudge string, or None when no trigger fires or local scope wins."""
    triggers = triggers or load_triggers()
    if not prompt or _hit(prompt, triggers["negative_context"]):
        return None
    categories = triggers["categories"]
    parts = []
    for key in _ROUTE_PRIORITY:
        spec = categories[key]
        if _hit(prompt, spec):
            parts.append(f"Load the knowledge-based-search skill, then use {spec['route']} because {spec['reason']}.")
            break
    if not parts:
        return None
    if _hit(prompt, triggers["library_first"]):
        parts.append("Check the book library (mcp__library) and the knowledge-based-search references too.")
    parts.append("Cite every claim that came from a search.")
    return " ".join(parts)


def demo():
    triggers = load_triggers()
    assert nudge_for("what is the latest version of pydantic", triggers).startswith("Load the knowledge-based-search skill, then use quick_web_search")
    assert "deep_research" in nudge_for("do a deep dive on this company", triggers)
    research = nudge_for("research the current state of vector databases", triggers)
    assert research and "web_search" in research, research
    assert nudge_for("refactor the function above in my code", triggers) is None
    assert nudge_for("write a haiku about autumn", triggers) is None
    method = nudge_for("research how to fact-check a viral video", triggers)
    assert "mcp__library" in method, method
    print("demo ok")


if __name__ == "__main__":
    demo()
