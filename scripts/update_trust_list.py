#!/usr/bin/env python3
"""Refresh the MBFC-derived news scores while preserving curated categories."""

import json
import sys
from pathlib import Path
from urllib.request import urlopen

_SOURCE_URL = (
    "https://raw.githubusercontent.com/drmikecrowe/mbfcext/master/docs/csources.json"
)
_TRUST_PATH = Path(__file__).resolve().parents[1] / "server" / "data" / "trust.json"
_RATING_SCORES = {
    "VERY HIGH": 95,
    "HIGH": 80,
    "High": 80,
    "MOSTLY FACTUAL": 65,
    "MIXED": 45,
    "LOW": 20,
    "VERY LOW": 10,
    "FAKE": 5,
}


def main() -> None:
    """Curated categories must survive generated news refreshes."""
    trust = json.loads(_TRUST_PATH.read_text(encoding="utf-8"))
    with urlopen(_SOURCE_URL, timeout=30) as response:
        sources = json.load(response)
    unknown_ratings = sorted(
        {
            item["r"]
            for item in sources.values()
            if item.get("r") is not None and _RATING_SCORES.get(item["r"]) is None
        }
    )
    if unknown_ratings:
        print(
            f"warning: skipped unmapped ratings: {', '.join(unknown_ratings)}",
            file=sys.stderr,
        )
    news = {
        item["d"].lower(): score
        for item in sources.values()
        if (score := _RATING_SCORES.get(item.get("r"))) is not None
    }
    updated = {"news": dict(sorted(news.items())), "categories": trust["categories"]}
    _TRUST_PATH.write_text(json.dumps(updated, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
