#!/usr/bin/env python3
"""Remove KBS-owned entries from Claude, Codex, and Pi config files."""

import json
import os
import re
import sys
import tempfile
from pathlib import Path

SERVER_NAME = "knowledge-based-search"


def read_json_dict(path):
    """Return the JSON object in path, or None when missing or malformed."""
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def write_atomic(path, text):
    """Write text to path through a same-directory temp file and rename."""
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=path.name + ".")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(tmp, path)
    except BaseException:
        os.unlink(tmp)
        raise


def write_json_atomic(path, data):
    """Serialize data as indented JSON and write it atomically."""
    write_atomic(path, json.dumps(data, indent=2) + "\n")


def hook_is_ours(entry):
    """Return True when a hook entry references the KBS hooks directory."""
    return f"{SERVER_NAME}/hooks" in json.dumps(entry)


def strip_kbs_hooks(settings):
    """Drop KBS hook entries from a settings dict, pruning empty containers."""
    changed = False
    hooks = settings.get("hooks")
    if not isinstance(hooks, dict):
        return False
    for event, entries in list(hooks.items()):
        if isinstance(entries, list):
            kept = [entry for entry in entries if not hook_is_ours(entry)]
            if kept != entries:
                hooks[event] = kept
                changed = True
        if hooks.get(event) == []:
            del hooks[event]
            changed = True
    if hooks == {}:
        settings.pop("hooks", None)
        changed = True
    return changed


def strip_kbs_mcp_server(data):
    """Drop the stale KBS MCP server entry, pruning the empty container."""
    servers = data.get("mcpServers")
    if not isinstance(servers, dict) or SERVER_NAME not in servers:
        return False
    del servers[SERVER_NAME]
    if not servers:
        data.pop("mcpServers", None)
    return True


def remove_claude(home):
    """Strip KBS hooks and MCP entries from the Claude Code config files."""
    settings_path = home / ".claude" / "settings.json"
    settings = read_json_dict(settings_path)
    if settings is not None and strip_kbs_hooks(settings):
        write_json_atomic(settings_path, settings)
        print(f"removed Claude hooks from {settings_path}")
    config_path = home / ".claude.json"
    config = read_json_dict(config_path)
    if config is not None and strip_kbs_mcp_server(config):
        write_json_atomic(config_path, config)
        print(f"removed Claude MCP server from {config_path}")


def strip_codex_text(text):
    """Return TOML text without KBS fenced blocks, hooks, or MCP tables."""
    text = re.sub(
        rf"(?ms)^# >>> {SERVER_NAME} >>>.*?^# <<< {SERVER_NAME} <<<\n*", "", text
    )
    header = re.compile(rf"^\[mcp_servers\.(['\"]?){SERVER_NAME}\1\]")
    kept = []
    skipping = False
    for line in text.splitlines(keepends=True):
        if header.match(line):
            skipping = True
            continue
        if skipping and line.lstrip().startswith("["):
            skipping = False
        if not skipping:
            kept.append(line)
    return "".join(kept)


def remove_codex(home):
    """Strip KBS blocks from the Codex TOML config."""
    path = home / ".codex" / "config.toml"
    if not path.exists():
        return
    original = path.read_text(encoding="utf-8")
    text = strip_codex_text(original)
    if text != original:
        write_atomic(path, text.rstrip() + "\n")
        print(f"removed Codex kbs block from {path}")


def remove_pi(home):
    """Strip the KBS extension and MCP entry from the Pi settings file."""
    path = home / ".pi" / "agent" / "settings.json"
    data = read_json_dict(path)
    if data is None:
        return
    changed = False
    extensions = data.get("extensions")
    if isinstance(extensions, list):
        kept = [
            item
            for item in extensions
            if not (SERVER_NAME in str(item) and str(item).endswith("index.ts"))
        ]
        if kept != extensions:
            data["extensions"] = kept
            changed = True
    changed = strip_kbs_mcp_server(data) or changed
    if changed:
        write_json_atomic(path, data)
        print(f"removed Pi kbs extension from {path}")


def main(argv):
    """Dispatch to the runtime handler named by the first argument."""
    handlers = {"claude": remove_claude, "codex": remove_codex, "pi": remove_pi}
    if len(argv) != 2 or argv[1] not in handlers:
        print(f"usage: {argv[0]} {{claude|codex|pi}}", file=sys.stderr)
        return 2
    handlers[argv[1]](Path.home())
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
