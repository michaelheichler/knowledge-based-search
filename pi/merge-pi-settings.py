#!/usr/bin/env python3
import json
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


def merge(settings_path, extension_path):
    data = read_json(settings_path)
    extensions = data.get("extensions", [])
    if not isinstance(extensions, list):
        extensions = []
    extension = str(extension_path)
    data["extensions"] = [item for item in extensions if item != extension and SERVER_NAME not in str(item)]
    data["extensions"].append(extension)
    repo = extension_path.parents[3]
    servers = data.setdefault("mcpServers", {})
    servers[SERVER_NAME] = {
        "command": PYTHON,
        "args": [str(repo / "server" / "mcp_server.py")],
    }
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return data


def main(argv):
    settings_path = Path(argv[1]).expanduser() if len(argv) > 1 else Path.home() / ".pi" / "agent" / "settings.json"
    extension_path = Path(argv[2]).expanduser().resolve() if len(argv) > 2 else Path(__file__).resolve().parent / "extensions" / "knowledge-based-search" / "index.ts"
    merge(settings_path, extension_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
