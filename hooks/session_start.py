#!/usr/bin/env python3
"""SessionStart hook: inject the standing search primer once per session."""

import json
import sys

PRIMER = (
    "Keyless web search is available via the knowledge-based-search MCP. Tools: "
    "quick_web_search (one fast fact), web_search (read sources and answer with citations), "
    "deep_research (multi-round cited report), deep_context_aware_search (context-aware recall), "
    "get_content (open one source). "
    "deep_research is bounded but expensive. Reach for web_search first, then escalate when needed. "
    "Before using any of them, load the knowledge-based-search skill. "
    "Verify any fact that can change since training (versions, APIs, prices, releases, events, "
    "people, current status) with these tools before stating it, because answering a changeable "
    "fact from memory is how stale answers slip through. When unsure whether a fact is current, "
    "run quick_web_search. For search and investigation method, use the knowledge-based-search "
    "skill, and use the book library if mcp__library is available."
)


def main():
    try:
        json.load(sys.stdin)
    except Exception:
        pass
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
