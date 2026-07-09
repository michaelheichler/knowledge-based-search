#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_NAME="knowledge-based-search"
KBS_BIN="$REPO/bin/kbs"
BIN_DIR="${KBS_BIN_DIR:-$HOME/.local/bin}"
VENV_DIR="${KBS_VENV_DIR:-$REPO/.venv}"

WANT_CLAUDE=auto
WANT_CODEX=auto
WANT_PI=auto
WANT_OPENCODE=auto
ASSUME_YES=0
EXPLICIT_TARGET=0

select_target() {
	if [ "$EXPLICIT_TARGET" = 0 ]; then
		WANT_CLAUDE=0
		WANT_CODEX=0
		WANT_PI=0
		WANT_OPENCODE=0
		EXPLICIT_TARGET=1
	fi
}

for arg in "$@"; do
	case "$arg" in
	--claude)
		select_target
		WANT_CLAUDE=1
		;;
	--codex)
		select_target
		WANT_CODEX=1
		;;
	--pi)
		select_target
		WANT_PI=1
		;;
	--opencode)
		select_target
		WANT_OPENCODE=1
		;;
	-y | --yes)
		ASSUME_YES=1
		;;
	-h | --help)
		printf '%s\n' "Usage: ./install.sh [--claude] [--codex] [--pi] [--opencode] [-y]"
		exit 0
		;;
	*)
		printf '%s\n' "unknown flag: $arg" >&2
		exit 1
		;;
	esac
done

resolve() {
	local want="$1"
	local probe="$2"
	case "$want" in
	1) printf '1\n' ;;
	0) printf '0\n' ;;
	auto) [ -e "$probe" ] && printf '1\n' || printf '0\n' ;;
	esac
}

backup() {
	local path="$1"
	[ -f "$path" ] || return 0
	local stamp target n
	stamp="$(date -u +%Y%m%dT%H%M%SZ)"
	target="$path.kbs.$stamp.bak"
	n=1
	while [ -e "$target" ]; do
		n=$((n + 1))
		target="$path.kbs.$stamp.$n.bak"
	done
	cp "$path" "$target"
	printf '%s\n' "backed up $path to $target"
}

prompt_url() {
	local default="https://endianness.de"
	local value=""
	if [ "$ASSUME_YES" = 0 ] && [ -t 0 ]; then
		printf 'SearXNG base URL [%s]: ' "$default"
		read -r value
	fi
	printf '%s\n' "${value:-$default}"
}

write_config() {
	local url="$1"
	python3 - "$REPO/server/config.json" "$url" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
data = {"searxng_url": sys.argv[2], "duckduckgo": True}
path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
PY
	printf '%s\n' "wrote $REPO/server/config.json"
}

install_claude() {
	local cfg="$HOME/.claude.json"
	mkdir -p "$HOME/.claude/skills"
	backup "$cfg"
	ln -snf "$REPO/skills/knowledge-based-search" "$HOME/.claude/skills/knowledge-based-search"
	python3 "$REPO/claude-code/merge-claude-settings.py" "$cfg" "$REPO/claude-code/claude-settings.snippet.json" "$REPO"
	printf '%s\n' "Claude skill linked"
}

install_codex() {
	local cfg="$HOME/.codex/config.toml"
	mkdir -p "$HOME/.codex/skills"
	backup "$cfg"
	ln -snf "$REPO/skills/knowledge-based-search" "$HOME/.codex/skills/knowledge-based-search"
	python3 "$REPO/codex/merge-codex-config.py" "$cfg" "$REPO/codex/codex-config.snippet.toml" "$REPO"
	printf '%s\n' "Codex skill linked"
}

install_pi() {
	local cfg="$HOME/.pi/agent/settings.json"
	local ext="$REPO/pi/extensions/knowledge-based-search/index.ts"
	mkdir -p "$HOME/.pi/agent" "$HOME/.pi/agent/skills" "$HOME/.pi/agent/prompts"
	backup "$cfg"
	python3 "$REPO/pi/merge-pi-settings.py" "$cfg" "$ext"
	ln -snf "$REPO/skills/knowledge-based-search" "$HOME/.pi/agent/skills/knowledge-based-search"
	cp "$REPO/pi/prompts/search.md" "$HOME/.pi/agent/prompts/search.md"
	printf '%s\n' "Pi extension registered"
	printf '%s\n' "Pi skill linked"
	printf '%s\n' "Pi /search prompt installed"
}

kbs_instructions() {
	cat <<'INSTRUCTIONS'
Keyless web search via kbs CLI:
  kbs quick <query>      one fast fact, ranked links and snippets
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

python_has_requirements() {
	python3 - <<'PY' >/dev/null 2>&1
import bm25s
import numpy
import pypdf
PY
}

ensure_kbs_python() {
	if python_has_requirements; then
		printf '%s\n' "python3"
		return 0
	fi
	python3 -m venv "$VENV_DIR"
	"$VENV_DIR/bin/python" -m pip install -r "$REPO/requirements.txt" >&2
	printf '%s\n' "$VENV_DIR/bin/python"
}

write_kbs_wrapper() {
	local python_bin="$1"
	local target="$BIN_DIR/kbs"
	rm -f "$target"
	cat >"$target" <<EOF
#!/usr/bin/env bash
exec "$python_bin" "$KBS_BIN" "\$@"
EOF
	chmod +x "$target"
}

install_kbs_bin() {
	if [ ! -f "$KBS_BIN" ]; then
		printf '%s\n' "bin/kbs not found at $KBS_BIN, skipping PATH install" >&2
		return 0
	fi
	mkdir -p "$BIN_DIR"
	write_kbs_wrapper "$(ensure_kbs_python)"
	printf '%s\n' "Installed kbs wrapper at $BIN_DIR/kbs"
}

install_opencode() {
	local cfg_dir="$HOME/.config/opencode"
	local agents="$cfg_dir/AGENTS.md"
	mkdir -p "$cfg_dir"
	backup "$agents"
	kbs_instructions >"$agents"
	printf '%s\n' "OpenCode instructions written to $agents"
}

verify_claude() {
	local settings="$HOME/.claude/settings.json"
	if [ -f "$settings" ] && grep -q "$SERVER_NAME/hooks/session_start.py" "$settings"; then
		printf '%s\n' "Claude kbs hooks installed"
	else
		printf '%s\n' "Claude kbs hooks not found"
	fi
}

verify_codex() {
	local cfg="$HOME/.codex/config.toml"
	if [ -f "$cfg" ] && grep -q "$SERVER_NAME/hooks/session_start.py" "$cfg"; then
		printf '%s\n' "Codex kbs hooks installed"
	else
		printf '%s\n' "Codex kbs hooks not found"
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

CLAUDE="$(resolve "$WANT_CLAUDE" "$HOME/.claude")"
CODEX="$(resolve "$WANT_CODEX" "$HOME/.codex")"
PI="$(resolve "$WANT_PI" "$HOME/.pi")"
OPENCODE="$(resolve "$WANT_OPENCODE" "$HOME/.config/opencode")"

if [ "$CLAUDE" = 0 ] && [ "$CODEX" = 0 ] && [ "$PI" = 0 ] && [ "$OPENCODE" = 0 ]; then
	printf '%s\n' "nothing selected" >&2
	exit 1
fi

write_config "$(prompt_url)"

install_kbs_bin

[ "$CLAUDE" = 1 ] && install_claude
[ "$CODEX" = 1 ] && install_codex
[ "$PI" = 1 ] && install_pi
[ "$OPENCODE" = 1 ] && install_opencode

printf '%s\n' "--- kbs CLI instructions ---"
kbs_instructions
printf '%s\n' "---"

verify_kbs

[ "$CLAUDE" = 1 ] && verify_claude
[ "$CODEX" = 1 ] && verify_codex
[ "$PI" = 1 ] && verify_pi

exit 0
