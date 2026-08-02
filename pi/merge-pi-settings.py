#!/usr/bin/env python3
"""Merge the KBS extension into Pi settings without losing user data."""

# ruff: noqa
import json
import os
import sys
import tempfile
from pathlib import Path


SERVER_NAME = "knowledge-based-search"


def is_knowledge_based_search_extension(item: object) -> bool:
    """Return whether an extension path points to the KBS extension."""
    path = Path(str(item))
    return path.name == "index.ts" and path.parent.name == SERVER_NAME


def read_json(path: Path) -> dict[str, object]:
    """Read a JSON object, refusing malformed files and non-object roots."""
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise SystemExit(f"refusing to overwrite malformed JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"refusing to overwrite {path}: JSON root must be an object")
    return data


def write_atomic(path: Path, text: str) -> None:
    """Write text through a same-directory temporary file and rename."""
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


def merge(settings_path: Path, extension_path: Path) -> dict[str, object]:
    """Replace stale KBS entries while preserving unrelated Pi settings."""
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
    mcp_servers = data.get("mcpServers")
    if isinstance(mcp_servers, dict):
        mcp_servers.pop(SERVER_NAME, None)
        if not mcp_servers:
            data.pop("mcpServers", None)
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    write_atomic(settings_path, json.dumps(data, indent=2) + "\n")
    return data


def main(argv: list[str]) -> int:
    """Merge settings from command-line paths or their default locations."""
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
