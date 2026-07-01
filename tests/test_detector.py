#!/usr/bin/env python3
"""Standalone checks for the prompt trigger detector."""

import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hooks"))
from detector import load_triggers, nudge_for
from method_inject import hook_output
from session_start import PRIMER

TRIGGERS = load_triggers()


class DetectorTests(unittest.TestCase):
    def test_recency_routes_quick(self):
        self.assertTrue(
            nudge_for("what is the latest version of pydantic", TRIGGERS).startswith(
                "Load the knowledge-based-search skill, then use quick_web_search"
            )
        )

    def test_year_pattern_fires(self):
        self.assertIsNotNone(nudge_for("what changed in python in 2026", TRIGGERS))

    def test_deep_routes_deep_research(self):
        self.assertIn(
            "deep_research", nudge_for("do a deep dive on this company", TRIGGERS)
        )

    def test_research_routes_web_search(self):
        result = nudge_for("research the current state of vector databases", TRIGGERS)
        self.assertIsNotNone(result)
        self.assertIn("web_search", result)

    def test_local_scope_suppresses(self):
        self.assertIsNone(nudge_for("refactor the function above in my code", TRIGGERS))

    def test_local_review_scope_suppresses_recency_words(self):
        self.assertIsNone(nudge_for("whole-current-diff code review", TRIGGERS))
        self.assertIsNone(nudge_for("review the current git diff", TRIGGERS))

    def test_plain_prompt_no_nudge(self):
        self.assertIsNone(nudge_for("write a haiku about autumn", TRIGGERS))

    def test_library_first_cue_routes_without_other_category(self):
        old = os.environ.get("KBS_LIBRARY_MCP")
        os.environ["KBS_LIBRARY_MCP"] = "1"
        try:
            result = nudge_for("verify this claim", TRIGGERS)
        finally:
            if old is None:
                os.environ.pop("KBS_LIBRARY_MCP", None)
            else:
                os.environ["KBS_LIBRARY_MCP"] = old
        self.assertIn("web_search", result)
        self.assertIn("mcp__library", result)

    def test_method_cue_skips_absent_library(self):
        old = os.environ.pop("KBS_LIBRARY_MCP", None)
        try:
            self.assertNotIn(
                "mcp__library",
                nudge_for("research how to fact-check a viral video", TRIGGERS),
            )
        finally:
            if old is not None:
                os.environ["KBS_LIBRARY_MCP"] = old

    def test_library_first_cue_skips_absent_library(self):
        old = os.environ.pop("KBS_LIBRARY_MCP", None)
        try:
            result = nudge_for("verify this claim", TRIGGERS)
        finally:
            if old is not None:
                os.environ["KBS_LIBRARY_MCP"] = old
        self.assertIn("knowledge-based-search references", result)
        self.assertNotIn("mcp__library", result)

    def test_method_cue_adds_registered_library(self):
        old = os.environ.get("KBS_LIBRARY_MCP")
        os.environ["KBS_LIBRARY_MCP"] = "1"
        try:
            self.assertIn(
                "mcp__library",
                nudge_for("research how to fact-check a viral video", TRIGGERS),
            )
        finally:
            if old is None:
                os.environ.pop("KBS_LIBRARY_MCP", None)
            else:
                os.environ["KBS_LIBRARY_MCP"] = old

    def test_recency_phrases_do_not_match_inside_other_words(self):
        self.assertIsNone(nudge_for("as of nowhere we are", TRIGGERS))
        self.assertIsNone(nudge_for("all right now and then", TRIGGERS))
        self.assertIsNotNone(nudge_for("what is right now trending", TRIGGERS))

    def test_empty_prompt(self):
        self.assertIsNone(nudge_for("", TRIGGERS))

    def test_post_tool_method_output(self):
        hook = hook_output(TRIGGERS)["hookSpecificOutput"]
        self.assertEqual("PostToolUse", hook["hookEventName"])
        self.assertIn("Use operators", hook["additionalContext"])

    def test_post_tool_method_output_mentions_search_tool(self):
        hook = hook_output(TRIGGERS, {"tool_name": "web_search"})["hookSpecificOutput"]
        self.assertIn("Cite", hook["additionalContext"])

    def test_primer_marks_library_tool_optional(self):
        self.assertIn("if mcp__library is available", PRIMER)

    def test_skill_marks_library_tool_optional(self):
        skill = (
            Path(__file__).resolve().parents[1]
            / "skills"
            / "knowledge-based-search"
            / "SKILL.md"
        )
        text = skill.read_text(encoding="utf-8")

        self.assertIn("if `mcp__library` is available", text)


def run():
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(DetectorTests)
    result = unittest.TextTestRunner().run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)


if __name__ == "__main__":
    run()
