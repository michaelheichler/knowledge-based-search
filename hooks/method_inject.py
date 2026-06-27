#!/usr/bin/env python3
import json
import sys

from detector import load_triggers


def hook_output(triggers=None):
    triggers = triggers or load_triggers()
    return {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": triggers["method"]["text"],
        }
    }


def main():
    json.load(sys.stdin)
    print(json.dumps(hook_output()))


def demo():
    output = hook_output()
    hook = output["hookSpecificOutput"]
    assert hook["hookEventName"] == "PostToolUse"
    assert "Use operators" in hook["additionalContext"]
    print("demo ok")


if __name__ == "__main__":
    demo() if len(sys.argv) > 1 and sys.argv[1] == "demo" else main()
