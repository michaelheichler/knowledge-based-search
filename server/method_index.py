"""Topic-to-method route table for ``kbs plan``."""

import shlex
from typing import TypedDict


class _Route(TypedDict):
    topic: str
    keywords: list[str]
    references: list[str]
    commands: list[str]


class _Fallback(TypedDict):
    topic: str
    references: list[str]
    commands: list[str]


_ROUTES: list[_Route] = [
    {
        "topic": "fact-checking",
        "keywords": [
            "fact-check",
            "fact check",
            "verify a claim",
            "verify the claim",
            "verify this claim",
            "verify claim",
            "viral",
            "debunk",
        ],
        "references": [
            "exposingtheinvisible/fact-checking.md",
            "exposingtheinvisible/evaluate-evidence.md",
        ],
        "commands": [
            "kbs search {query} fact check",
            "kbs deep {query}",
        ],
    },
    {
        "topic": "osint",
        "keywords": [
            "osint",
            "how to investigate",
            "investigation method",
            "tradecraft",
            "how to research",
        ],
        "references": [
            "exposingtheinvisible/osint-ocean.md",
            "exposingtheinvisible/investigation-concepts.md",
        ],
        "commands": [
            "kbs search {query}",
            "kbs deep {query}",
        ],
    },
    {
        "topic": "source-evaluation",
        "keywords": [
            "source evaluation",
            "evaluate evidence",
            "evaluate sources",
        ],
        "references": [
            "exposingtheinvisible/evaluate-evidence.md",
            "exposingtheinvisible/fact-checking.md",
        ],
        "commands": [
            "kbs search {query}",
            "kbs deep {query}",
        ],
    },
    {
        "topic": "disinformation",
        "keywords": [
            "disinformation",
            "misinformation",
            "fake news",
        ],
        "references": [
            "exposingtheinvisible/disinformation.md",
        ],
        "commands": [
            "kbs search {query}",
            "kbs deep {query}",
        ],
    },
    {
        "topic": "interview",
        "keywords": [
            "interview",
            "source management",
            "manage sources",
        ],
        "references": [
            "exposingtheinvisible/interviews.md",
            "exposingtheinvisible/manage-sources.md",
        ],
        "commands": [
            "kbs search {query}",
        ],
    },
    {
        "topic": "company-domain",
        "keywords": [
            "who owns",
            "who is",
            "company",
            "ownership",
            "due diligence",
            "background check",
            "domain lookup",
            "whois",
            "dns",
            "corporate",
        ],
        "references": [
            "exposingtheinvisible/companies.md",
            "exposingtheinvisible/web.md",
            "osint-techniques/ch39.md",
        ],
        "commands": [
            "kbs search {query} site:opencorporates.com OR site:linkedin.com",
            "kbs deep {query} ownership",
        ],
    },
    {
        "topic": "username-trace",
        "keywords": [
            "trace a username",
            "trace username",
            "trace an email",
            "trace email",
            "username",
            "trace",
            "alias",
            "handle",
            "email address",
        ],
        "references": [
            "osint-techniques/ch31.md",
            "osint-techniques/ch30.md",
        ],
        "commands": [
            "kbs search {query} username OR profile",
            "kbs deep {query} trace",
        ],
    },
    {
        "topic": "geolocation",
        "keywords": [
            "geolocate",
            "geolocation",
            "where is this",
            "image location",
        ],
        "references": [
            "exposingtheinvisible/geolocation.md",
            "exposingtheinvisible/maps.md",
        ],
        "commands": [
            "kbs search {query} reverse image search",
            "kbs deep {query} geolocation",
        ],
    },
    {
        "topic": "dorking",
        "keywords": [
            "dorking",
            "google dork",
            "search operator",
        ],
        "references": [
            "exposingtheinvisible/google-dorking.md",
        ],
        "commands": [
            "kbs search {query} site: filetype:",
        ],
    },
    {
        "topic": "web-archive",
        "keywords": [
            "wayback",
            "archive",
            "cached page",
            "deleted page",
            "web archive",
        ],
        "references": [
            "exposingtheinvisible/web-archive.md",
        ],
        "commands": [
            "kbs search {query} site:web.archive.org",
        ],
    },
]

_FALLBACK: _Fallback = {
    "topic": "general",
    "references": [
        "README.md",
        "exposingtheinvisible/google-dorking.md",
    ],
    "commands": [
        "kbs search {query}",
        "kbs deep {query}",
    ],
}


def _match(query: str) -> list[_Route]:
    low = query.lower()
    return [route for route in _ROUTES if any(kw in low for kw in route["keywords"])]


def plan_search(query: str) -> dict[str, object]:
    query = (query or "").strip()
    if not query:
        raise ValueError("query is required")
    safe = shlex.quote(query)
    matched: list[_Route] = _match(query)
    if not matched:
        return {
            "route": _FALLBACK["topic"],
            "references": list(_FALLBACK["references"]),
            "commands": [cmd.replace("{query}", safe) for cmd in _FALLBACK["commands"]],
            "matched_topics": [],
        }
    references: list[str] = []
    commands: list[str] = []
    seen_ref: set[str] = set()
    seen_cmd: set[str] = set()
    for route in matched:
        for ref in route["references"]:
            if ref not in seen_ref:
                seen_ref.add(ref)
                references.append(ref)
        for cmd in route["commands"]:
            formatted = cmd.replace("{query}", safe)
            if formatted not in seen_cmd:
                seen_cmd.add(formatted)
                commands.append(formatted)
    return {
        "route": matched[0]["topic"],
        "references": references,
        "commands": commands,
        "matched_topics": [route["topic"] for route in matched],
    }
