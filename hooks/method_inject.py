#!/usr/bin/env python3
# ruff: noqa
import json
import re
import sys

from detector import load_triggers

_KBS_COMMAND_RE = re.compile(r"(^|[;&|]\s*)([A-Za-z_][A-Za-z0-9_]*=\S+\s+)*kbs(\s|$)")


def hook_output(triggers=None, event=None):
    triggers = triggers or load_triggers()
    event = event or {}
    text = triggers["method"]["text"]
    tool_name = event.get("tool_name") or event.get("tool", {}).get("name", "")
    tool_input = event.get("tool_input", {})
    command = tool_input.get("command", "") if isinstance(tool_input, dict) else ""
    is_kbs = tool_name == "Bash" and bool(_KBS_COMMAND_RE.search(command))
    if is_kbs:
        text += " Cite each sourced claim and check each source date."
    return {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": text,
        }
    }


def main():
    try:
        event = json.load(sys.stdin)
    except (ValueError, OSError):
        return
    print(json.dumps(hook_output(event=event)))


def demo():
    output = hook_output()
    hook = output["hookSpecificOutput"]
    assert hook["hookEventName"] == "PostToolUse"
    assert "Use operators" in hook["additionalContext"]
    print("demo ok")


if __name__ == "__main__":
    demo() if len(sys.argv) > 1 and sys.argv[1] == "demo" else main()
