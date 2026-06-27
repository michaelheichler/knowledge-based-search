#!/usr/bin/env python3
"""Standalone checks for the prompt trigger detector."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hooks"))
from detector import load_triggers, nudge_for
from method_inject import hook_output

TRIGGERS = load_triggers()


class DetectorTests(unittest.TestCase):
    def test_recency_routes_quick(self):
        self.assertTrue(
            nudge_for("what is the latest version of pydantic", TRIGGERS).startswith("Load the knowledge-based-search skill, then use quick_web_search")
        )

    def test_year_pattern_fires(self):
        self.assertIsNotNone(nudge_for("what changed in python in 2026", TRIGGERS))

    def test_deep_routes_deep_research(self):
        self.assertIn("deep_research", nudge_for("do a deep dive on this company", TRIGGERS))

    def test_research_routes_web_search(self):
        result = nudge_for("research the current state of vector databases", TRIGGERS)
        self.assertIsNotNone(result)
        self.assertIn("web_search", result)

    def test_local_scope_suppresses(self):
        self.assertIsNone(nudge_for("refactor the function above in my code", TRIGGERS))

    def test_plain_prompt_no_nudge(self):
        self.assertIsNone(nudge_for("write a haiku about autumn", TRIGGERS))

    def test_method_cue_adds_library(self):
        self.assertIn("mcp__library", nudge_for("research how to fact-check a viral video", TRIGGERS))

    def test_empty_prompt(self):
        self.assertIsNone(nudge_for("", TRIGGERS))

    def test_post_tool_method_output(self):
        hook = hook_output(TRIGGERS)["hookSpecificOutput"]
        self.assertEqual("PostToolUse", hook["hookEventName"])
        self.assertIn("Use operators", hook["additionalContext"])


def run():
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(DetectorTests)
    result = unittest.TextTestRunner().run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)


if __name__ == "__main__":
    run()
