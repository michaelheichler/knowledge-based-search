#!/usr/bin/env python3
# ruff: noqa
"""SessionStart hook: inject the standing search primer once per session."""

import json
import sys

PRIMER = (
    "Keyless web search is available via the kbs CLI. Commands: "
    "kbs quick (one fast fact), kbs search (read sources and answer with citations), "
    "kbs deep (multi-round cited report), kbs context (context-aware recall), "
    "kbs get <url> (open one source). "
    "kbs deep is bounded but expensive. Reach for kbs search first, then escalate when needed. "
    "Before using any of them, load the knowledge-based-search skill. "
    "Verify any fact that can change since training (versions, APIs, prices, releases, events, "
    "people, current status) with these tools before stating it, because answering a changeable "
    "fact from memory is how stale answers slip through. When unsure whether a fact is current, "
    "run kbs quick. For search and investigation method, use the knowledge-based-search "
    "skill, and use the book library if mcp__library is available."
)


def main():
    sys.stdin.read()
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": PRIMER,
                }
            }
        )
    )


if __name__ == "__main__":
    main()
