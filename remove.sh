#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_NAME="knowledge-based-search"
BIN_DIR="${KBS_BIN_DIR:-$HOME/.local/bin}"
VENV_DIR="${KBS_VENV_DIR:-$REPO/.venv}"

backup() {
	local path="$1"
	[ -f "$path" ] || return 0
	local stamp target n
	stamp="$(date -u +%Y%m%dT%H%M%SZ)"
	target="$path.kbs-remove.$stamp.bak"
	n=1
	while [ -e "$target" ]; do
		n=$((n + 1))
		target="$path.kbs-remove.$stamp.$n.bak"
	done
	cp "$path" "$target"
	printf '%s\n' "backed up $path to $target"
}

remove_if_owned_file() {
	local path="$1"
	local needle="$2"
	[ -f "$path" ] || return 0
	if grep -qF "$needle" "$path"; then
		rm -f "$path"
		printf '%s\n' "removed $path"
	else
		printf '%s\n' "kept $path, not owned by this install"
	fi
}

remove_link_or_owned_dir() {
	local path="$1"
	[ -e "$path" ] || [ -L "$path" ] || return 0
	if [ -L "$path" ]; then
		rm -f "$path"
		printf '%s\n' "removed $path"
	elif [ -d "$path" ] && [ "$(cd "$path" && pwd)" = "$REPO/skills/knowledge-based-search" ]; then
		rm -rf "$path"
		printf '%s\n' "removed $path"
	else
		printf '%s\n' "kept $path, not owned by this install"
	fi
}

remove_claude_settings() {
	local settings="$HOME/.claude/settings.json"
	local cfg="$HOME/.claude.json"
	python3 - "$settings" "$cfg" <<'PY'
import json
import sys
from pathlib import Path

server_name = "knowledge-based-search"
settings_path = Path(sys.argv[1]).expanduser()
config_path = Path(sys.argv[2]).expanduser()


def read_json(path):
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def hook_is_ours(entry):
    return "knowledge-based-search/hooks" in json.dumps(entry)

changed = False
settings = read_json(settings_path)
if settings is not None:
    hooks = settings.get("hooks")
    if isinstance(hooks, dict):
        for event, entries in list(hooks.items()):
            if isinstance(entries, list):
                kept = [entry for entry in entries if not hook_is_ours(entry)]
                if kept != entries:
                    hooks[event] = kept
                    changed = True
        for event in list(hooks):
            if hooks[event] == []:
                del hooks[event]
                changed = True
        if hooks == {}:
            settings.pop("hooks", None)
            changed = True
    if changed:
        write_json(settings_path, settings)
        print(f"removed Claude hooks from {settings_path}")

changed = False
config = read_json(config_path)
if config is not None:
    servers = config.get("mcpServers")
    if isinstance(servers, dict) and server_name in servers:
        del servers[server_name]
        changed = True
        if not servers:
            config.pop("mcpServers", None)
    if changed:
        write_json(config_path, config)
        print(f"removed Claude MCP server from {config_path}")
PY
}

remove_codex_config() {
	local cfg="$HOME/.codex/config.toml"
	[ -f "$cfg" ] || return 0
	python3 - "$cfg" <<'PY'
import re
import sys
from pathlib import Path

path = Path(sys.argv[1]).expanduser()
text = path.read_text(encoding="utf-8")
original = text
text = re.sub(
    r"(?ms)^# >>> knowledge-based-search >>>.*?^# <<< knowledge-based-search <<<\n*",
    "",
    text,
)
lines = []
skipping = False
for line in text.splitlines(keepends=True):
    if re.match(r"^\[mcp_servers\.(['\"]?)knowledge-based-search\1\]", line):
        skipping = True
        continue
    if skipping and line.lstrip().startswith("["):
        skipping = False
    if not skipping:
        lines.append(line)
text = "".join(lines)
if text != original:
    path.write_text(text.rstrip() + "\n", encoding="utf-8")
    print(f"removed Codex kbs block from {path}")
PY
}

remove_agents_duplicate_skill() {
	local path="$HOME/.agents/skills/knowledge-based-search"
	[ -e "$path" ] || [ -L "$path" ] || return 0
	if [ -L "$path" ]; then
		rm -f "$path"
		printf '%s\n' "removed $path"
		return 0
	fi
	if [ -f "$path/SKILL.md" ] && grep -q '^name: knowledge-based-search$' "$path/SKILL.md"; then
		local disabled stamp target
		disabled="$HOME/.agents/skills/.disabled-conflicts"
		stamp="$(date -u +%Y%m%dT%H%M%SZ)"
		target="$disabled/knowledge-based-search.$stamp"
		mkdir -p "$disabled"
		mv "$path" "$target"
		printf '%s\n' "moved duplicate skill to $target"
	else
		printf '%s\n' "kept $path, not recognized as knowledge-based-search"
	fi
}

remove_pi_settings() {
	local cfg="$HOME/.pi/agent/settings.json"
	[ -f "$cfg" ] || return 0
	python3 - "$cfg" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1]).expanduser()
try:
    data = json.loads(path.read_text(encoding="utf-8"))
except ValueError:
    raise SystemExit(0)
if not isinstance(data, dict):
    raise SystemExit(0)
changed = False
extensions = data.get("extensions")
if isinstance(extensions, list):
    kept = []
    for item in extensions:
        text = str(item)
        if "knowledge-based-search" in text and text.endswith("index.ts"):
            changed = True
            continue
        kept.append(item)
    data["extensions"] = kept
servers = data.get("mcpServers")
if isinstance(servers, dict) and "knowledge-based-search" in servers:
    del servers["knowledge-based-search"]
    changed = True
    if not servers:
        data.pop("mcpServers", None)
if changed:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"removed Pi kbs extension from {path}")
PY
}

kbs_instructions() {
	cat <<'INSTRUCTIONS'
Keyless web search via kbs CLI:
  kbs quick <query>      one fast fact, ranked links and snippets
  kbs plan <query>       method plan with reference notes before OSINT/fact checks
  kbs search <query>     full pipeline, cited summary
  kbs get <url>          open one source in full
  kbs deep <query>       bounded multi-round cited report
  kbs context <query>    context-aware search with session memory
  kbs doctor             check daemon health and PATH
Load the knowledge-based-search skill before searching.
Reach for kbs search first, escalate to kbs deep when needed.
Verify any fact that can change since training before stating it.
INSTRUCTIONS
}

remove_instructions_file() {
	local path="$1"
	[ -f "$path" ] || return 0
	local expected
	expected="$(mktemp)"
	kbs_instructions >"$expected"
	if cmp -s "$path" "$expected"; then
		rm -f "$path"
		printf '%s\n' "removed $path"
	else
		printf '%s\n' "kept $path, not owned by this install"
	fi
	rm -f "$expected"
}

backup "$HOME/.claude/settings.json"
backup "$HOME/.claude.json"
backup "$HOME/.codex/config.toml"
backup "$HOME/.pi/agent/settings.json"
backup "$HOME/.config/opencode/AGENTS.md"
backup "$HOME/.config/zed/AGENTS.md"

remove_if_owned_file "$BIN_DIR/kbs" "$REPO/bin/kbs"
remove_link_or_owned_dir "$HOME/.claude/skills/knowledge-based-search"
remove_link_or_owned_dir "$HOME/.codex/skills/knowledge-based-search"
remove_link_or_owned_dir "$HOME/.pi/agent/skills/knowledge-based-search"
remove_if_owned_file "$HOME/.pi/agent/prompts/search.md" "knowledge-based-search"
remove_link_or_owned_dir "$HOME/.config/opencode/skills/knowledge-based-search"
remove_if_owned_file "$HOME/.config/opencode/plugins/knowledge-based-search.ts" "$REPO/opencode/plugins/knowledge-based-search.ts"
remove_agents_duplicate_skill
remove_if_owned_file "$HOME/.config/opencode/AGENTS.md" "$REPO/opencode/AGENTS.md"
remove_instructions_file "$HOME/.config/zed/AGENTS.md"

remove_claude_settings
remove_codex_config
remove_pi_settings

if [ -d "$VENV_DIR" ]; then
	rm -rf "$VENV_DIR"
	printf '%s\n' "removed $VENV_DIR"
fi

printf '%s\n' "removed knowledge-based-search install artifacts"
