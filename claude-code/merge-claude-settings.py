#!/usr/bin/env python3
# ruff: noqa
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


SERVER_NAME = "knowledge-based-search"


def read_json(path):
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as handle:
        try:
            data = json.load(handle)
        except ValueError:
            data = {}
    return data if isinstance(data, dict) else {}


def render_snippet(path, repo):
    text = path.read_text(encoding="utf-8")
    text = text.replace("__KBS_DIR__", str(repo))
    try:
        return json.loads(text)
    except ValueError as exc:
        raise SystemExit(f"invalid Claude settings snippet {path}: {exc}") from exc


def hook_entry_is_ours(entry):
    return "knowledge-based-search/hooks" in json.dumps(entry)


def backup(path):
    if not path.exists():
        return
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = Path(f"{path}.kbs.{stamp}.bak")
    copy_number = 1
    while target.exists():
        copy_number += 1
        target = Path(f"{path}.kbs.{stamp}.{copy_number}.bak")
    target.write_bytes(path.read_bytes())


def merge_lists(current, incoming):
    """Incoming entries append after user entries so reruns keep stable order."""
    seen = {json.dumps(item, sort_keys=True) for item in current}
    for item in incoming:
        key = json.dumps(item, sort_keys=True)
        if key not in seen:
            current.append(item)
            seen.add(key)
    return current


def deep_merge(current, incoming):
    for key, value in incoming.items():
        if isinstance(value, dict) and isinstance(current.get(key), dict):
            deep_merge(current[key], value)
        elif isinstance(value, list) and isinstance(current.get(key), list):
            current[key] = merge_lists(current[key], value)
        else:
            current[key] = value
    return current


def remove_our_hooks(data):
    hooks = data.get("hooks", {})
    if not isinstance(hooks, dict):
        return data
    for event, entries in list(hooks.items()):
        if isinstance(entries, list):
            hooks[event] = [entry for entry in entries if not hook_entry_is_ours(entry)]
    return data


def remove_kbs_server_config(data):
    mcp_servers = data.get("mcpServers")
    if not isinstance(mcp_servers, dict):
        return data
    mcp_servers.pop(SERVER_NAME, None)
    if not mcp_servers:
        data.pop("mcpServers", None)
    return data


def merge_hooks(settings, incoming_hooks):
    hooks = settings.setdefault("hooks", {})
    for event, incoming_entries in incoming_hooks.items():
        current_entries = hooks.get(event, [])
        if not isinstance(current_entries, list):
            current_entries = []
        hooks[event] = [
            entry for entry in current_entries if not hook_entry_is_ours(entry)
        ]
        merge_lists(hooks[event], incoming_entries)
    return settings


def merge(config_path, snippet_path, repo, settings_path=None):
    config = read_json(config_path)
    snippet = render_snippet(snippet_path, repo)
    settings_path = settings_path or Path.home() / ".claude" / "settings.json"
    settings = read_json(settings_path)
    config_snippet = {key: value for key, value in snippet.items() if key != "hooks"}
    remove_our_hooks(config)
    remove_kbs_server_config(config)
    deep_merge(config, config_snippet)
    merge_hooks(settings, snippet.get("hooks", {}))
    config_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    backup(settings_path)
    config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    return config


def main(argv):
    home = Path.home()
    config_path = Path(argv[1]).expanduser() if len(argv) > 1 else home / ".claude.json"
    snippet_path = (
        Path(argv[2]).expanduser()
        if len(argv) > 2
        else Path(__file__).with_name("claude-settings.snippet.json")
    )
    repo = (
        Path(argv[3]).expanduser().resolve()
        if len(argv) > 3
        else Path(__file__).resolve().parents[1]
    )
    settings_path = (
        Path(argv[4]).expanduser()
        if len(argv) > 4
        else home / ".claude" / "settings.json"
    )
    merge(config_path, snippet_path, repo, settings_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
