#!/usr/bin/env python3
"""UserPromptSubmit hook: inject a search nudge when the prompt matches a trigger."""
import json
import sys

from detector import nudge_for

_PROMPT_KEYS = ("prompt", "user_prompt", "message", "input")


def _prompt(event):
    for key in _PROMPT_KEYS:
        value = event.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return ""


def main():
    try:
        event = json.load(sys.stdin)
    except Exception:
        return
    nudge = nudge_for(_prompt(event))
    if not nudge:
        return
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": nudge}}))


if __name__ == "__main__":
    main()
