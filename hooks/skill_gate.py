#!/usr/bin/env python3
# ruff: noqa
import json
import os
import re
import sys

SKILL_NAME = "knowledge-based-search"
_KBS_COMMAND_RE = re.compile(r"(^|[;&|]\s*)([A-Za-z_][A-Za-z0-9_]*=\S+\s+)*kbs(\s|$)")
_TRANSCRIPT_CACHE: dict[str, tuple[int, bool]] = {}
SKILL_DENY_REASON = (
    "Load the knowledge-based-search skill with the Skill tool first, then reformulate the "
    "query with its method and run the search again. This gate fires until the skill is loaded "
    "this session."
)
WEB_SEARCH_DENY_REASON = "Built-in web search is disabled. Use kbs through Bash or a configured Linkup tool instead."
_WEB_SEARCH_TOOLS = {"WebSearch", "web_search", "websearch"}


def _line_loads_skill(line):
    try:
        entry = json.loads(line)
    except ValueError:
        return False
    content = entry.get("message", {}).get("content")
    if not isinstance(content, list):
        return False
    for item in content:
        if (
            isinstance(item, dict)
            and item.get("type") == "tool_use"
            and item.get("name") == "Skill"
            and isinstance(item.get("input"), dict)
            and item["input"].get("skill") == SKILL_NAME
        ):
            return True
    return False


def _tool_name(event):
    return event.get("tool_name") or event.get("tool", {}).get("name", "")


def _is_kbs_invocation(event):
    if _tool_name(event) == "Bash":
        tool_input = event.get("tool_input", {})
        command = tool_input.get("command", "") if isinstance(tool_input, dict) else ""
        return bool(_KBS_COMMAND_RE.search(command))
    return False


def deny_reason(event):
    if _tool_name(event) in _WEB_SEARCH_TOOLS:
        return WEB_SEARCH_DENY_REASON
    return SKILL_DENY_REASON


def should_block(event):
    if _tool_name(event) in _WEB_SEARCH_TOOLS:
        return True
    if not _is_kbs_invocation(event):
        return False
    path = event.get("transcript_path")
    if not path:
        return False
    try:
        stamp = os.stat(path).st_mtime_ns
        cached = _TRANSCRIPT_CACHE.get(path)
        if cached and cached[0] == stamp:
            return not cached[1]
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                if SKILL_NAME in line and _line_loads_skill(line):
                    _TRANSCRIPT_CACHE[path] = (stamp, True)
                    return False
    except OSError:
        return False
    _TRANSCRIPT_CACHE[path] = (stamp, False)
    return True


def deny_output(reason=SKILL_DENY_REASON):
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def main():
    try:
        event = json.load(sys.stdin)
    except (ValueError, OSError):
        return
    if should_block(event):
        print(json.dumps(deny_output(deny_reason(event))))


def demo():
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
    assert _line_loads_skill(loaded)
    assert not _line_loads_skill(decoy)
    assert deny_output()["hookSpecificOutput"]["permissionDecision"] == "deny"
    print("demo ok")


if __name__ == "__main__":
    demo() if len(sys.argv) > 1 and sys.argv[1] == "demo" else main()
