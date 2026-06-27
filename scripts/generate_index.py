#!/usr/bin/env python3
"""Generate references/README.md, a routing index built from each note front matter."""
import os
import re

ROOT = "/Users/michael/dev/skills/knowledge-based-search/skills/knowledge-based-search/references"
GROUPS = [
    ("exposingtheinvisible", "Exposing the Invisible, The Kit (primary source)"),
    ("osint-techniques", "OSINT Techniques (Bazzell, Edison)"),
    ("osint-resources", "Open Source Intelligence Techniques, Resources (Bazzell)"),
    ("digital-research-methods", "Handbook of Digital and Computational Research Methods"),
]


def _field(text, key):
    match = re.search(rf"^{key}:\s*(.+)$", text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def _entries(group):
    out = []
    group_dir = os.path.join(ROOT, group)
    if not os.path.isdir(group_dir):
        return out
    for name in sorted(os.listdir(group_dir)):
        if not name.endswith(".md") or name == "README.md":
            continue
        text = open(os.path.join(group_dir, name), encoding="utf-8").read()
        title = _field(text, "title") or name[:-3]
        use_when = _field(text, "use_when")
        out.append((f"{group}/{name}", title, use_when))
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
    out_path = os.path.join(ROOT, "README.md")
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"wrote {out_path} with {total} entries")


if __name__ == "__main__":
    run()
