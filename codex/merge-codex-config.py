#!/usr/bin/env python3
import re
import os
import sys
import tomllib
from pathlib import Path


START = "# >>> knowledge-based-search >>>"
END = "# <<< knowledge-based-search <<<"


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


def render(path, repo):
    text = path.read_text(encoding="utf-8")
    values = {
        "__KBS_DIR__": str(repo),
        "__KBS_PYTHON__": resolve_python(repo),
        "__KBS_SERVER__": str(repo / "server" / "mcp_server.py"),
    }
    for key, value in values.items():
        text = text.replace(key, value)
    return text.strip()


def strip_fenced(text):
    pattern = re.compile(
        r"(?ms)^" + re.escape(START) + r".*?^" + re.escape(END) + r"\n*"
    )
    return pattern.sub("", text)


def merge(config_path, snippet_path, repo):
    current = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
    current = strip_fenced(current).rstrip()
    snippet = render(snippet_path, repo)
    block = (
        f"{snippet}\n"
        if START in snippet and END in snippet
        else f"{START}\n{snippet}\n{END}\n"
    )
    merged = f"{current}\n\n{block}" if current else block
    tomllib.loads(merged)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(merged, encoding="utf-8")
    return merged


def main(argv):
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
