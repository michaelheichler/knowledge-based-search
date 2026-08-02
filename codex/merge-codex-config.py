#!/usr/bin/env python3
"""Merge the KBS hook into Codex configuration without losing user data."""

# ruff: noqa
import os
import re
import shlex
import sys
import tempfile
import tomllib
from pathlib import Path


START = "# >>> knowledge-based-search >>>"
END = "# <<< knowledge-based-search <<<"


def render(path: Path, repo: Path) -> str:
    """Shell quoting is required because hook paths may contain spaces or metacharacters."""
    text = path.read_text(encoding="utf-8")
    hook_path = shlex.quote(str(repo / "hooks" / "skill_gate.py"))
    text = text.replace("__KBS_HOOK__", hook_path)
    return text.strip()


def strip_fenced(text: str) -> str:
    """Remove existing fenced KBS configuration blocks."""
    pattern = re.compile(
        r"(?ms)^" + re.escape(START) + r".*?^" + re.escape(END) + r"\n*"
    )
    return pattern.sub("", text)


_HOOK_GROUP = re.compile(r"^\[\[hooks\.[^.\]]+\]\]\s*$")


def strip_legacy_kbs_hooks(text: str) -> str:
    """Legacy groups must go because fenced ownership cannot coexist with unfenced hooks."""
    prefix = []
    groups = []
    group = None
    for line in text.splitlines(keepends=True):
        if not _HOOK_GROUP.match(line):
            (prefix if group is None else group).append(line)
            continue
        if group is not None:
            groups.append(group)
        group = [line]
    if group is not None:
        groups.append(group)
    kept = [
        "".join(group)
        for group in groups
        if "knowledge-based-search" not in "".join(group)
    ]
    return "".join(prefix + kept)


KBS_MCP_HEADER = re.compile(
    r'^\[mcp_servers\.(?P<q>["\']?)knowledge-based-search(?P=q)\]'
)


def _is_table_header(line: str) -> bool:
    return line.lstrip().startswith("[")


def strip_stale_mcp_table(text: str) -> str:
    """Remove the obsolete KBS MCP table while preserving later tables."""
    # ponytail: safe while MCP args stay single-line. Use a tomllib round-trip if they span lines.
    kept = []
    skipping = False
    for line in text.splitlines(keepends=True):
        if KBS_MCP_HEADER.match(line):
            skipping = True
            continue
        if skipping and _is_table_header(line):
            skipping = False
        if skipping:
            continue
        kept.append(line)
    return "".join(kept)


def write_atomic(path: Path, text: str) -> None:
    """Replacement stays atomic because interruption must not truncate user configuration."""
    fd, temporary_path = tempfile.mkstemp(
        dir=str(path.parent), prefix=path.name + "."
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(temporary_path, path)
    except BaseException:
        os.unlink(temporary_path)
        raise


def merge(config_path: Path, snippet_path: Path, repo: Path) -> str:
    """Only one owned block may survive because repeated installs must stay idempotent."""
    current = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
    current = strip_stale_mcp_table(
        strip_legacy_kbs_hooks(strip_fenced(current))
    ).rstrip()
    snippet = render(snippet_path, repo)
    block = (
        f"{snippet}\n"
        if START in snippet and END in snippet
        else f"{START}\n{snippet}\n{END}\n"
    )
    merged = f"{current}\n\n{block}" if current else block
    tomllib.loads(merged)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    write_atomic(config_path, merged)
    return merged


def main(argv: list[str]) -> int:
    """Default paths remain because installers depend on noninteractive invocation."""
    config_path = (
        Path(argv[1]).expanduser()
        if len(argv) > 1
        else Path.home() / ".codex" / "config.toml"
    )
    snippet_path = (
        Path(argv[2]).expanduser()
        if len(argv) > 2
        else Path(__file__).with_name("codex-config.snippet.toml")
    )
    repo = (
        Path(argv[3]).expanduser().resolve()
        if len(argv) > 3
        else Path(__file__).resolve().parents[1]
    )
    merge(config_path, snippet_path, repo)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
