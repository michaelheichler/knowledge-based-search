#!/usr/bin/env python3
"""Standalone checks for the prompt trigger detector."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hooks"))
from detector import load_triggers, nudge_for

TRIGGERS = load_triggers()


def test_recency_routes_quick():
    assert nudge_for("what is the latest version of pydantic", TRIGGERS).startswith("Use quick_web_search")


def test_year_pattern_fires():
    assert nudge_for("what changed in python in 2026", TRIGGERS) is not None


def test_deep_routes_deep_research():
    assert "deep_research" in nudge_for("do a deep dive on this company", TRIGGERS)


def test_research_routes_web_search():
    result = nudge_for("research the current state of vector databases", TRIGGERS)
    assert result and "web_search" in result


def test_local_scope_suppresses():
    assert nudge_for("refactor the function above in my code", TRIGGERS) is None


def test_plain_prompt_no_nudge():
    assert nudge_for("write a haiku about autumn", TRIGGERS) is None


def test_method_cue_adds_library():
    assert "mcp__library" in nudge_for("research how to fact-check a viral video", TRIGGERS)


def test_empty_prompt():
    assert nudge_for("", TRIGGERS) is None


def run():
    checks = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    for check in checks:
        check()
    print(f"{len(checks)} checks passed")


if __name__ == "__main__":
    run()
