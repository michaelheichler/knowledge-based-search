#!/usr/bin/env python3
import json
import sys

SKILL_NAME = "knowledge-based-search"
DENY_REASON = (
    "Load the knowledge-based-search skill with the Skill tool first, then reformulate the "
    "query with its method and run the search again. This gate fires until the skill is loaded "
    "this session."
)


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


def should_block(event):
    path = event.get("transcript_path")
    if not path:
        return False
    try:
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                if SKILL_NAME in line and _line_loads_skill(line):
                    return False
    except OSError:
        return False
    return True


def deny_output(reason=DENY_REASON):
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
    except ValueError:
        return
    if should_block(event):
        print(json.dumps(deny_output()))


def demo():
    loaded = json.dumps({"message": {"content": [{"type": "tool_use", "name": "Skill", "input": {"skill": SKILL_NAME}}]}})
    decoy = json.dumps({"message": {"content": [{"type": "tool_use", "name": "Skill", "input": {"skill": "interview-me", "args": SKILL_NAME}}]}})
    assert _line_loads_skill(loaded)
    assert not _line_loads_skill(decoy)
    assert deny_output()["hookSpecificOutput"]["permissionDecision"] == "deny"
    print("demo ok")


if __name__ == "__main__":
    demo() if len(sys.argv) > 1 and sys.argv[1] == "demo" else main()
