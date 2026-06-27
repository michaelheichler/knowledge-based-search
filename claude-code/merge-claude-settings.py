#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path


SERVER_NAME = "knowledge-based-search"
PYTHON = "/Users/michael/dev/skills/skill-model-loader/.venv/bin/python"


def read_json(path):
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as handle:
        try:
            data = json.load(handle)
        except json.JSONDecodeError:
            data = {}
    return data if isinstance(data, dict) else {}


def render_snippet(path, repo):
    text = path.read_text(encoding="utf-8")
    values = {
        "__KBS_DIR__": str(repo),
        "__KBS_PYTHON__": PYTHON,
        "__KBS_SERVER__": str(repo / "server" / "mcp_server.py"),
    }
    for key, value in values.items():
        text = text.replace(key, value)
    return json.loads(text)


def hook_entry_is_ours(entry):
    return "knowledge-based-search" in json.dumps(entry)


def merge_lists(current, incoming):
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


def merge(config_path, snippet_path, repo):
    config = read_json(config_path)
    snippet = render_snippet(snippet_path, repo)
    hooks = config.setdefault("hooks", {})
    for event in snippet.get("hooks", {}):
        hooks[event] = [entry for entry in hooks.get(event, []) if not hook_entry_is_ours(entry)]
    deep_merge(config, snippet)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    return config


def main(argv):
    home = Path.home()
    config_path = Path(argv[1]).expanduser() if len(argv) > 1 else home / ".claude.json"
    snippet_path = Path(argv[2]).expanduser() if len(argv) > 2 else Path(__file__).with_name("claude-settings.snippet.json")
    repo = Path(argv[3]).expanduser().resolve() if len(argv) > 3 else Path(__file__).resolve().parents[1]
    merge(config_path, snippet_path, repo)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
