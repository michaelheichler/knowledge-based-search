#!/usr/bin/env python3
# ruff: noqa
"""Checks for the PreToolUse skill-load gate."""

import json
import os
import tempfile
import unittest
from unittest import mock

import skill_gate  # type: ignore[import-not-found]
from skill_gate import (  # type: ignore[import-not-found]
    SKILL_NAME,
    TRANSCRIPT_DENY_REASON,
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


def _tool_line(name, tool_input):
    item = {"type": "tool_use", "name": name, "input": tool_input}
    return json.dumps({"message": {"content": [item]}})


def _event(command, path=None):
    return {
        "transcript_path": path,
        "tool_name": "Bash",
        "tool_input": {"command": command},
    }


_BYPASS_COMMANDS = (
    "./bin/kbs search x",
    "/opt/kbs/bin/kbs search x",
    "/usr/local/kbs search x",
    "python3 /opt/kbs/bin/kbs search x",
    "python3 -X utf8 /opt/kbs search x",
    "command kbs search x",
    "env KBS_SESSION=s kbs search x",
    "true; kbs search x",
    "true && kbs search x",
    "printf x | kbs search x",
    "printf x\nkbs search x",
    "echo $(kbs search x)",
    'bash -c "kbs search x"',
    "bash -lc 'kbs search x'",
    "zsh -c 'kbs search x'",
    "sh -c 'kbs search x'",
    "exec kbs search x",
    "(kbs search x)",
    "{ kbs search x; }",
    "timeout 5 kbs search x",
    "timeout --signal KILL 5 kbs search x",
    "timeout -k 2 --foreground 5 kbs search x",
    "sudo -u root kbs search x",
    "sudo --non-interactive kbs search x",
    "nice -n 10 kbs search x",
    "nice -5 kbs search x",
    "/usr/bin/time -f %e kbs search x",
    "time -p kbs search x",
    "nohup kbs search x",
    "xargs kbs",
    "../kbs search x",
    'kbs search "unbalanced',
    'bash -c "kbs search x',
    "eval kbs search x",
    'eval "kbs search x"',
    'env -S "kbs search x"',
    "env --split-string='kbs search x'",
)


class SkillGateTests(unittest.TestCase):
    def test_blocks_kbs_when_skill_never_loaded(self) -> None:
        path = _transcript([_tool_line("Bash", {"command": "ls"})])
        self.addCleanup(os.unlink, path)
        self.assertTrue(should_block(_event("kbs search current docs", path)))

    def test_blocks_builtin_web_search(self) -> None:
        for tool_name in ["WebSearch", "web_search", "websearch"]:
            with self.subTest(tool_name=tool_name):
                event = {"tool_name": tool_name}
                self.assertTrue(should_block(event))
                self.assertEqual(deny_reason(event), WEB_SEARCH_DENY_REASON)

    def test_allows_non_kbs_bash_without_skill(self) -> None:
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

    def test_allows_kbs_substrings_that_are_not_commands(self) -> None:
        path = _transcript([])
        self.addCleanup(os.unlink, path)
        commands = [
            "echo kbs",
            "cat /tmp/kbs-backup",
            "makbs search",
            "printf '%s' 'text | kbs search x'",
            "printf '%s' 'text && kbs search x'",
        ]
        for command in commands:
            self.assertFalse(
                should_block(
                    {
                        "transcript_path": path,
                        "tool_name": "Bash",
                        "tool_input": {"command": command},
                    }
                )
            )

    def test_allows_when_skill_loaded(self) -> None:
        path = _transcript([_tool_line("Skill", {"skill": SKILL_NAME})])
        self.addCleanup(os.unlink, path)
        self.assertFalse(should_block(_event("kbs search x", path)))

    def test_allows_plugin_namespaced_skill_id(self) -> None:
        namespaced = f"{SKILL_NAME}:{SKILL_NAME}"
        path = _transcript([_tool_line("Skill", {"skill": namespaced})])
        self.addCleanup(os.unlink, path)
        self.assertFalse(should_block(_event("kbs search x", path)))

    def test_rejects_foreign_namespaced_skill_id(self) -> None:
        path = _transcript(
            [_tool_line("Skill", {"skill": "other:knowledge-based-search"})]
        )
        self.addCleanup(os.unlink, path)
        self.assertTrue(should_block(_event("kbs search x", path)))

    def test_reuses_cache_when_transcript_mtime_is_unchanged(self) -> None:
        path = _transcript([_tool_line("Skill", {"skill": SKILL_NAME})])
        self.addCleanup(os.unlink, path)
        skill_gate._TRANSCRIPT_CACHE.clear()
        opened = []
        real_open = open

        def counting_open(*args, **kwargs) -> object:
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

    def test_skill_name_in_other_skill_args_does_not_load_gate(self) -> None:
        decoy = _tool_line("Skill", {"skill": "interview-me", "args": SKILL_NAME})
        loaded = _tool_line("Skill", {"skill": SKILL_NAME})

        assert not _line_loads_skill(decoy)
        assert not _line_loads_skill(_tool_line("Skill", {"skill": []}))
        assert _line_loads_skill(loaded)

    def test_non_skill_tool_name_does_not_load_gate(self) -> None:
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

    def test_blocks_recognized_kbs_when_transcript_path_is_missing(self) -> None:
        event = _event("kbs search x")
        self.assertTrue(should_block(event))
        self.assertEqual(deny_reason(event), TRANSCRIPT_DENY_REASON)

    def test_blocks_recognized_kbs_when_transcript_is_unreadable(self) -> None:
        event = _event("kbs search x", "/no/such/transcript.jsonl")
        self.assertTrue(should_block(event))
        self.assertEqual(deny_reason(event), TRANSCRIPT_DENY_REASON)

    def test_allows_runtime_event_without_transcript_key(self) -> None:
        event = {"tool_name": "Bash", "tool_input": {"command": "kbs search x"}}
        self.assertFalse(should_block(event))

    def test_catches_supported_shell_bypass_spellings(self) -> None:
        path = _transcript([])
        self.addCleanup(os.unlink, path)
        for command in _BYPASS_COMMANDS:
            with self.subTest(command=command):
                self.assertTrue(should_block(_event(command, path)))


if __name__ == "__main__":
    unittest.main()
