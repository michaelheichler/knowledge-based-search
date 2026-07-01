#!/usr/bin/env python3
import json
import sys

from detector import load_triggers


def hook_output(triggers=None, event=None):
    triggers = triggers or load_triggers()
    event = event or {}
    text = triggers["method"]["text"]
    tool_name = event.get("tool_name") or event.get("tool", {}).get("name", "")
    if tool_name in {"web_search", "deep_research", "get_content"}:
        text += " Cite each sourced claim and check each source date."
    return {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": text,
        }
    }


def main():
    event = json.load(sys.stdin)
    print(json.dumps(hook_output(event=event)))


def demo():
    output = hook_output()
    hook = output["hookSpecificOutput"]
    assert hook["hookEventName"] == "PostToolUse"
    assert "Use operators" in hook["additionalContext"]
    print("demo ok")


if __name__ == "__main__":
    demo() if len(sys.argv) > 1 and sys.argv[1] == "demo" else main()
