#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$REPO/scripts/lib.sh"
SERVER_NAME="knowledge-based-search"
KBS_BIN="$REPO/bin/kbs"
BIN_DIR="${KBS_BIN_DIR:-$HOME/.local/bin}"
VENV_DIR="${KBS_VENV_DIR:-$HOME/.local/share/kbs/venv}"
VENV_MARKER=".kbs-owned-venv"
FENCE_START="<!-- kbs:start -->"
FENCE_END="<!-- kbs:end -->"

CLAUDE_REQUESTED=0
WANT_CODEX=auto
WANT_PI=auto
WANT_OPENCODE=auto
WANT_ZED=auto
ASSUME_YES=0

for arg in "$@"; do
	case "$arg" in
	--claude | --codex | --pi | --opencode | --zed | --zcode)
		WANT_CODEX=0
		WANT_PI=0
		WANT_OPENCODE=0
		WANT_ZED=0
		break
		;;
	esac
done

for arg in "$@"; do
	case "$arg" in
	--claude)
		CLAUDE_REQUESTED=1
		;;
	--codex)
		WANT_CODEX=1
		;;
	--pi)
		WANT_PI=1
		;;
	--opencode)
		WANT_OPENCODE=1
		;;
	--zed | --zcode)
		WANT_ZED=1
		;;
	-y | --yes)
		ASSUME_YES=1
		;;
	-h | --help)
		printf '%s\n' "Usage: ./install.sh [--claude] [--codex] [--pi] [--opencode] [--zed] [-y]"
		exit 0
		;;
	*)
		printf '%s\n' "unknown flag: $arg" >&2
		exit 1
		;;
	esac
done

require_python() {
	if ! python3 -c 'import sys; raise SystemExit(sys.version_info < (3, 11))' >/dev/null 2>&1; then
		printf '%s\n' "kbs requires python3 3.11 or newer" >&2
		exit 1
	fi
}

require_python

resolve() {
	local want="$1"
	local probe="$2"
	case "$want" in
	1) printf '1\n' ;;
	0) printf '0\n' ;;
	auto) [ -e "$probe" ] && printf '1\n' || printf '0\n' ;;
	esac
}

prompt_url() {
	local value=""
	if [ "$ASSUME_YES" = 0 ] && [ -t 0 ]; then
		printf '%s' "SearXNG base URL (empty for DuckDuckGo only): "
		read -r value || true
	fi
	printf '%s\n' "$value"
}

write_config() {
	local path="$HOME/.config/kbs/config.json"
	if [ -e "$path" ]; then
		printf '%s\n' "kept existing $path"
		return 0
	fi
	local url
	url="$(prompt_url)"
	mkdir -p "$(dirname "$path")"
	python3 - "$path" "$url" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
data = {"duckduckgo": True}
if sys.argv[2]:
    data["searxng_url"] = sys.argv[2]
path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
PY
	printf '%s\n' "wrote $path"
}

install_codex() {
	local cfg="$HOME/.codex/config.toml"
	mkdir -p "$HOME/.codex/skills"
	backup_file "$cfg"
	ln -snf "$REPO/skills/knowledge-based-search" "$HOME/.codex/skills/knowledge-based-search"
	python3 "$REPO/codex/merge-codex-config.py" "$cfg" "$REPO/codex/codex-config.snippet.toml" "$REPO"
	printf '%s\n' "Codex skill linked"
}

install_pi() {
	local cfg="$HOME/.pi/agent/settings.json"
	local ext="$REPO/pi/extensions/knowledge-based-search/index.ts"
	mkdir -p "$HOME/.pi/agent" "$HOME/.pi/agent/skills" "$HOME/.pi/agent/prompts"
	backup_file "$cfg"
	python3 "$REPO/pi/merge-pi-settings.py" "$cfg" "$ext"
	ln -snf "$REPO/skills/knowledge-based-search" "$HOME/.pi/agent/skills/knowledge-based-search"
	backup_file "$HOME/.pi/agent/prompts/search.md"
	cp "$REPO/pi/prompts/search.md" "$HOME/.pi/agent/prompts/search.md"
	printf '%s\n' "Pi extension registered"
	printf '%s\n' "Pi skill linked"
	printf '%s\n' "Pi /search prompt installed"
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

venv_path_is_safe() {
	if ! python3 - "$VENV_DIR" "$HOME" <<'PY'
"""Reject venv paths that resolve to protected directories."""
import sys
from pathlib import Path

venv = Path(sys.argv[1]).expanduser().resolve()
home = Path(sys.argv[2]).expanduser().resolve()
raise SystemExit(venv in {Path("/"), home})
PY
	then
		printf '%s\n' "refusing unsafe KBS_VENV_DIR: $VENV_DIR" >&2
		return 1
	fi
	if [ -e "$VENV_DIR" ] && [ ! -d "$VENV_DIR" ]; then
		printf '%s\n' "refusing KBS_VENV_DIR that is not a directory: $VENV_DIR" >&2
		return 1
	fi
}

venv_dir_is_nonempty() {
	[ -d "$VENV_DIR" ] && [ -n "$(find "$VENV_DIR" -mindepth 1 -maxdepth 1 -print -quit)" ]
}

venv_dir_is_venv() {
	[ -x "$VENV_DIR/bin/python" ] && [ -f "$VENV_DIR/pyvenv.cfg" ]
}

kbs_venv_is_ready() {
	venv_dir_is_venv || return 1
	"$VENV_DIR/bin/python" - <<'PY' >/dev/null 2>&1
import bm25s
import numpy
import pypdf
PY
}

ensure_kbs_python() {
	venv_path_is_safe
	if venv_dir_is_nonempty && ! venv_dir_is_venv; then
		printf '%s\n' "refusing non-empty non-venv KBS_VENV_DIR: $VENV_DIR" >&2
		return 1
	fi
	if venv_dir_is_nonempty && [ ! -f "$VENV_DIR/$VENV_MARKER" ]; then
		printf '%s\n' "refusing unowned venv at $VENV_DIR, choose another KBS_VENV_DIR" >&2
		return 1
	fi
	if ! venv_dir_is_nonempty; then
		python3 -m venv "$VENV_DIR"
		touch "$VENV_DIR/$VENV_MARKER"
	fi
	if ! kbs_venv_is_ready; then
		"$VENV_DIR/bin/python" -m pip install -r "$REPO/requirements.txt" >&2
	fi
	printf '%s\n' "$VENV_DIR/bin/python"
}

write_kbs_wrapper() {
	local python_bin="$1"
	local target="$BIN_DIR/kbs"
	rm -f "$target"
	{
		printf '%s\n' '#!/usr/bin/env bash'
		printf 'exec %q %q "$@"\n' "$python_bin" "$KBS_BIN"
	} >"$target"
	chmod +x "$target"
}

install_kbs_bin() {
	local target="$BIN_DIR/kbs"
	local escaped_kbs_bin python_bin
	printf -v escaped_kbs_bin '%q' "$KBS_BIN"
	if [ ! -f "$KBS_BIN" ]; then
		printf '%s\n' "bin/kbs not found at $KBS_BIN, skipping PATH install" >&2
		return 0
	fi
	mkdir -p "$BIN_DIR"
	if { [ -e "$target" ] || [ -L "$target" ]; } && ! grep -qF "$escaped_kbs_bin" "$target" 2>/dev/null; then
		backup_file "$target"
	fi
	python_bin="$(ensure_kbs_python)"
	write_kbs_wrapper "$python_bin"
	printf '%s\n' "Installed kbs wrapper at $target"
}

write_fenced_block() {
	local path="$1"
	local content="$2"
	python3 - "$path" "$FENCE_START" "$FENCE_END" "$content" <<'PY'
"""Refresh one fenced KBS block without replacing surrounding content."""
import os, re, sys, tempfile
from pathlib import Path

path = Path(sys.argv[1])
start, end, content = sys.argv[2:]
original = path.read_text(encoding="utf-8") if path.exists() else ""
block = f"{start}\n{content.rstrip()}\n{end}"
pattern = re.compile(rf"(?ms)^{re.escape(start)}\n.*?^{re.escape(end)}\n?")
if pattern.search(original):
    updated = pattern.sub(lambda _: block + "\n", original, count=1)
else:
    separator = "" if not original else "\n" if original.endswith("\n") else "\n\n"
    updated = original + separator + block + "\n"
fd, temporary_path = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".")
try:
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(updated)
    os.replace(temporary_path, path)
except BaseException:
    os.unlink(temporary_path)
    raise
PY
}

install_opencode() {
	local config_dir="$HOME/.config/opencode"
	local agents="$config_dir/AGENTS.md"
	mkdir -p "$config_dir/plugins" "$config_dir/skills"
	ln -snf "$REPO/skills/knowledge-based-search" "$config_dir/skills/knowledge-based-search"
	cp "$REPO/opencode/plugins/knowledge-based-search.ts" "$config_dir/plugins/knowledge-based-search.ts"
	backup_file "$agents"
	write_fenced_block "$agents" "$(<"$REPO/opencode/AGENTS.md")"
	printf '%s\n' "OpenCode KBS gate installed"
}

install_zed() {
	write_instructions_to "Zed" "$HOME/.config/zed/AGENTS.md"
}

write_instructions_to() {
	local label="$1"
	local agents="$2"
	mkdir -p "$(dirname "$agents")"
	backup_file "$agents"
	write_fenced_block "$agents" "$(kbs_instructions)"
	printf '%s\n' "$label instructions written to $agents"
}

verify_codex() {
	local cfg="$HOME/.codex/config.toml"
	if [ -f "$cfg" ] && grep -q "$SERVER_NAME/hooks/skill_gate.py" "$cfg"; then
		printf '%s\n' "Codex KBS gate installed"
	else
		printf '%s\n' "Codex KBS gate not found"
	fi
}

verify_pi() {
	local cfg="$HOME/.pi/agent/settings.json"
	if [ -f "$cfg" ] && grep -q "$SERVER_NAME" "$cfg"; then
		printf '%s\n' "Pi lists $SERVER_NAME extension"
	else
		printf '%s\n' "Pi does not list $SERVER_NAME extension"
	fi
}

verify_kbs() {
	local kbs_path
	kbs_path="$(command -v kbs 2>/dev/null || true)"
	if [ -n "$kbs_path" ]; then
		printf '%s\n' "kbs resolves to $kbs_path"
		kbs doctor --json >/dev/null 2>&1 && printf '%s\n' "kbs doctor: ok" || printf '%s\n' "kbs doctor: daemon not responding" >&2
	else
		printf '%s\n' "kbs not on PATH. Add $BIN_DIR to PATH." >&2
	fi
}

CODEX="$(resolve "$WANT_CODEX" "$HOME/.codex")"
PI="$(resolve "$WANT_PI" "$HOME/.pi")"
OPENCODE="$(resolve "$WANT_OPENCODE" "$HOME/.config/opencode")"
ZED="$(resolve "$WANT_ZED" "$HOME/.config/zed")"

if [ "$CLAUDE_REQUESTED" = 1 ]; then
	printf '%s\n' "Claude Code uses the plugin: /plugin install"
fi

if [ "$CODEX" = 0 ] && [ "$PI" = 0 ] && [ "$OPENCODE" = 0 ] && [ "$ZED" = 0 ]; then
	[ "$CLAUDE_REQUESTED" = 1 ] && exit 0
	printf '%s\n' "nothing selected" >&2
	exit 1
fi

write_config
install_kbs_bin

[ "$CODEX" = 1 ] && install_codex
[ "$PI" = 1 ] && install_pi
[ "$OPENCODE" = 1 ] && install_opencode
[ "$ZED" = 1 ] && install_zed

printf '%s\n' "--- kbs CLI instructions ---"
kbs_instructions
printf '%s\n' "---"

verify_kbs

[ "$CODEX" = 1 ] && verify_codex
[ "$PI" = 1 ] && verify_pi

exit 0
