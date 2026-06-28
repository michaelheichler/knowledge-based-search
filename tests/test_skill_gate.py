#!/usr/bin/env python3
"""Checks for the PreToolUse skill-load gate."""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hooks"))
from skill_gate import should_block, _line_loads_skill, SKILL_NAME


def _transcript(lines):
    handle = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8")
    for line in lines:
        handle.write(line + "\n")
    handle.close()
    return handle.name


class SkillGateTests(unittest.TestCase):
    def test_blocks_when_skill_never_loaded(self):
        path = _transcript([
            json.dumps({"message": {"content": [{"type": "tool_use", "name": "Bash", "input": {"command": "ls"}}]}}),
        ])
        self.addCleanup(os.unlink, path)
        self.assertTrue(should_block({"transcript_path": path}))

    def test_allows_when_skill_loaded(self):
        path = _transcript([
            json.dumps({"message": {"content": [{"type": "tool_use", "name": "Skill", "input": {"skill": SKILL_NAME}}]}}),
        ])
        self.addCleanup(os.unlink, path)
        self.assertFalse(should_block({"transcript_path": path}))

    def test_skill_name_in_other_skill_args_does_not_pass(self):
        decoy = json.dumps({"message": {"content": [{"type": "tool_use", "name": "Skill", "input": {"skill": "interview-me", "args": SKILL_NAME}}]}})
        self.assertFalse(_line_loads_skill(decoy))

    def test_mcp_tool_name_does_not_pass(self):
        line = json.dumps({"message": {"content": [{"type": "tool_use", "name": "mcp__knowledge-based-search__web_search", "input": {"query": "x"}}]}})
        self.assertFalse(_line_loads_skill(line))

    def test_fails_open_on_missing_path(self):
        self.assertFalse(should_block({}))

    def test_fails_open_on_unreadable_path(self):
        self.assertFalse(should_block({"transcript_path": "/no/such/transcript.jsonl"}))


if __name__ == "__main__":
    unittest.main()
