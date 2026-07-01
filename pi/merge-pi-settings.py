#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path


SERVER_NAME = "knowledge-based-search"


def resolve_python(repo):
    configured = os.environ.get("KBS_PYTHON")
    if configured:
        return configured
    sibling = repo.parent / "skill-model-loader" / ".venv" / "bin" / "python"
    if sibling.exists():
        return str(sibling)
    raise SystemExit(
        "Set KBS_PYTHON to the Python interpreter that can run knowledge-based-search"
    )


def resolve_repo(extension_path):
    configured = os.environ.get("KBS_DIR")
    if configured:
        return Path(configured).expanduser().resolve()
    for parent in [extension_path.parent, *extension_path.parents]:
        if (parent / "hooks" / "session_start.py").exists():
            return parent
    raise SystemExit("Set KBS_DIR to the knowledge-based-search repo")


def is_knowledge_based_search_extension(item):
    path = Path(str(item))
    return path.name == "index.ts" and path.parent.name == SERVER_NAME


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
    data["extensions"] = [
        item
        for item in extensions
        if item != extension and not is_knowledge_based_search_extension(item)
    ]
    data["extensions"].append(extension)
    repo = resolve_repo(extension_path)
    servers = data.setdefault("mcpServers", {})
    servers[SERVER_NAME] = {
        "command": resolve_python(repo),
        "args": [str(repo / "server" / "mcp_server.py")],
    }
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return data


def main(argv):
    settings_path = (
        Path(argv[1]).expanduser()
        if len(argv) > 1
        else Path.home() / ".pi" / "agent" / "settings.json"
    )
    extension_path = (
        Path(argv[2]).expanduser().resolve()
        if len(argv) > 2
        else Path(__file__).resolve().parent
        / "extensions"
        / "knowledge-based-search"
        / "index.ts"
    )
    merge(settings_path, extension_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
