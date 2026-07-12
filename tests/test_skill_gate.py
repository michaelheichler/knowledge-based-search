#!/usr/bin/env python3
# ruff: noqa
"""Checks for the PreToolUse skill-load gate."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "hooks"))
import skill_gate  # type: ignore[import-not-found]
from skill_gate import (  # type: ignore[import-not-found]
    SKILL_NAME,
    WEB_SEARCH_DENY_REASON,
    _line_loads_skill,
    deny_reason,
    should_block,
)


def _transcript(lines):
    with tempfile.NamedTemporaryFile(
        "w", suffix=".jsonl", delete=False, encoding="utf-8"
    ) as handle:
        for line in lines:
            handle.write(line + "\n")
        return handle.name


class SkillGateTests(unittest.TestCase):
    def test_blocks_kbs_when_skill_never_loaded(self):
        path = _transcript(
            [
                json.dumps(
                    {
                        "message": {
                            "content": [
                                {
                                    "type": "tool_use",
                                    "name": "Bash",
                                    "input": {"command": "ls"},
                                }
                            ]
                        }
                    }
                ),
            ]
        )
        self.addCleanup(os.unlink, path)
        self.assertTrue(
            should_block(
                {
                    "transcript_path": path,
                    "tool_name": "Bash",
                    "tool_input": {"command": "kbs search current docs"},
                }
            )
        )

    def test_blocks_builtin_web_search(self):
        for tool_name in ["WebSearch", "web_search", "websearch"]:
            with self.subTest(tool_name=tool_name):
                event = {"tool_name": tool_name}
                self.assertTrue(should_block(event))
                self.assertEqual(deny_reason(event), WEB_SEARCH_DENY_REASON)

    def test_allows_non_kbs_bash_without_skill(self):
        path = _transcript([])
        self.addCleanup(os.unlink, path)
        self.assertFalse(
            should_block(
                {
                    "transcript_path": path,
                    "tool_name": "Bash",
                    "tool_input": {"command": "ls"},
                }
            )
        )

    def test_allows_kbs_substrings_that_are_not_commands(self):
        path = _transcript([])
        self.addCleanup(os.unlink, path)
        for command in ["echo kbs", "cat /tmp/kbs-backup", "makbs search"]:
            self.assertFalse(
                should_block(
                    {
                        "transcript_path": path,
                        "tool_name": "Bash",
                        "tool_input": {"command": command},
                    }
                )
            )

    def test_allows_when_skill_loaded(self):
        path = _transcript(
            [
                json.dumps(
                    {
                        "message": {
                            "content": [
                                {
                                    "type": "tool_use",
                                    "name": "Skill",
                                    "input": {"skill": SKILL_NAME},
                                }
                            ]
                        }
                    }
                ),
            ]
        )
        self.addCleanup(os.unlink, path)
        self.assertFalse(should_block({"transcript_path": path}))

    def test_reuses_cache_when_transcript_mtime_is_unchanged(self):
        path = _transcript(
            [
                json.dumps(
                    {
                        "message": {
                            "content": [
                                {
                                    "type": "tool_use",
                                    "name": "Skill",
                                    "input": {"skill": SKILL_NAME},
                                }
                            ]
                        }
                    }
                ),
            ]
        )
        self.addCleanup(os.unlink, path)
        skill_gate._TRANSCRIPT_CACHE.clear()
        opened = []
        real_open = open

        def counting_open(*args, **kwargs):
            opened.append(args[0])
            return real_open(*args, **kwargs)

        event = {
            "transcript_path": path,
            "tool_name": "Bash",
            "tool_input": {"command": "kbs quick pydantic"},
        }

        with mock.patch("builtins.open", counting_open):
            self.assertFalse(should_block(event))
            self.assertFalse(should_block(event))

        self.assertEqual(opened, [path])

    def test_skill_name_in_other_skill_args_does_not_load_gate(self):
        decoy = json.dumps(
            {
                "message": {
                    "content": [
                        {
                            "type": "tool_use",
                            "name": "Skill",
                            "input": {"skill": "interview-me", "args": SKILL_NAME},
                        }
                    ]
                }
            }
        )
        loaded = json.dumps(
            {
                "message": {
                    "content": [
                        {
                            "type": "tool_use",
                            "name": "Skill",
                            "input": {"skill": SKILL_NAME},
                        }
                    ]
                }
            }
        )

        assert not _line_loads_skill(decoy)
        assert _line_loads_skill(loaded)

    def test_non_skill_tool_name_does_not_load_gate(self):
        line = json.dumps(
            {
                "message": {
                    "content": [
                        {
                            "type": "tool_use",
                            "name": "Bash",
                            "input": {"command": "kbs search x"},
                        }
                    ]
                }
            }
        )

        assert not _line_loads_skill(line)

    def test_fails_open_on_missing_path(self):
        self.assertFalse(should_block({}))

    def test_fails_open_on_unreadable_path(self):
        self.assertFalse(should_block({"transcript_path": "/no/such/transcript.jsonl"}))


if __name__ == "__main__":
    unittest.main()
