#!/usr/bin/env python3
# ruff: noqa
"""Generate references/README.md from note front matter."""

import re
from pathlib import Path

ROOT = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "knowledge-based-search"
    / "references"
)
GROUPS = [
    ("exposingtheinvisible", "Exposing the Invisible, The Kit (primary source)"),
    ("osint-techniques", "OSINT Techniques (Bazzell, Edison)"),
    ("osint-resources", "Open Source Intelligence Techniques, Resources (Bazzell)"),
    (
        "digital-research-methods",
        "Handbook of Digital and Computational Research Methods",
    ),
]


def _field(text, key):
    match = re.search(rf"^{key}:\s*(.+)$", text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def _entries(group):
    out = []
    group_dir = ROOT / group
    if not group_dir.is_dir():
        return out
    for path in sorted(group_dir.glob("*.md")):
        if path.name == "README.md":
            continue
        text = path.read_text(encoding="utf-8")
        title = _field(text, "title") or path.stem
        use_when = _field(text, "use_when")
        out.append((f"{group}/{path.name}", title, use_when))
    return out


def run():
    lines = [
        "# Search and Investigation Tradecraft, Reference Index",
        "",
        "These notes distill search and investigation tradecraft from one website and three books.",
        "Each entry names when to consult it. Read the matching note before applying a technique.",
        "",
    ]
    total = 0
    for group, label in GROUPS:
        entries = _entries(group)
        if not entries:
            continue
        total += len(entries)
        lines.append(f"## {label}")
        lines.append("")
        for path, title, use_when in entries:
            hook = f" {use_when}" if use_when else ""
            lines.append(f"- [{title}]({path}).{hook}")
        lines.append("")
    lines.append(f"Total notes: {total}.")
    out_path = ROOT / "README.md"
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out_path} with {total} entries")


if __name__ == "__main__":
    run()
