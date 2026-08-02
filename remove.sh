#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$REPO/scripts/lib.sh"
BIN_DIR="${KBS_BIN_DIR:-$HOME/.local/bin}"
VENV_DIR="${KBS_VENV_DIR:-$HOME/.local/share/kbs/venv}"
VENV_MARKER=".kbs-owned-venv"
FENCE_START="<!-- kbs:start -->"
FENCE_END="<!-- kbs:end -->"
printf -v KBS_BIN_NEEDLE '%q' "$REPO/bin/kbs"

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

remove_if_same_file() {
	local path="$1"
	local source="$2"
	[ -f "$path" ] || return 0
	if cmp -s "$path" "$source"; then
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
		case "$(readlink "$path")" in
		"$REPO"/*)
			rm -f "$path"
			printf '%s\n' "removed $path"
			;;
		*)
			printf '%s\n' "kept $path, symlink does not point into this install"
			;;
		esac
	elif [ -d "$path" ] && [ "$(cd "$path" && pwd)" = "$REPO/skills/knowledge-based-search" ]; then
		rm -rf "$path"
		printf '%s\n' "removed $path"
	else
		printf '%s\n' "kept $path, not owned by this install"
	fi
}

fence_pair_is_sane() {
	awk -v start="$FENCE_START" -v end="$FENCE_END" '
		$0==start {if (seen_start || seen_end) invalid=1; seen_start=1}
		$0==end {if (!seen_start || seen_end) invalid=1; seen_end=1}
		END {exit !(seen_start && seen_end && !invalid)}
	' "$1"
}

remove_fenced_block() {
	local path="$1"
	[ -f "$path" ] || return 0
	grep -qF "$FENCE_START" "$path" || grep -qF "$FENCE_END" "$path" || return 0
	if ! grep -qF "$FENCE_START" "$path" || ! grep -qF "$FENCE_END" "$path" || ! fence_pair_is_sane "$path"; then
		printf '%s\n' "kept $path, malformed kbs fence markers"
		return 0
	fi
	local tmp
	tmp="$(mktemp)"
	awk -v start="$FENCE_START" -v end="$FENCE_END" '$0==start{skip=1;next} $0==end{skip=0;next} !skip' "$path" >"$tmp"
	if grep -q '[^[:space:]]' "$tmp"; then
		mv "$tmp" "$path"
		printf '%s\n' "removed kbs block from $path"
	else
		rm -f "$path" "$tmp"
		printf '%s\n' "removed $path"
	fi
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

remove_legacy_zed_instructions() {
	local path="$HOME/.config/zed/AGENTS.md"
	[ -f "$path" ] || return 0
	local expected
	expected="$(mktemp)"
	kbs_instructions >"$expected"
	remove_if_same_file "$path" "$expected"
	rm -f "$expected"
}

remove_venv() {
	[ -d "$VENV_DIR" ] || return 0
	local resolved
	resolved="$(cd "$VENV_DIR" && pwd)"
	if [ "$resolved" = "/" ] || [ "$resolved" = "$HOME" ] || [ ! -f "$resolved/$VENV_MARKER" ]; then
		printf '%s\n' "kept $resolved, missing $VENV_MARKER marker" >&2
		return 0
	fi
	rm -rf "$resolved"
	printf '%s\n' "removed $resolved"
}

backup_file "$HOME/.claude/settings.json" kbs-remove
backup_file "$HOME/.claude.json" kbs-remove
backup_file "$HOME/.codex/config.toml" kbs-remove
backup_file "$HOME/.pi/agent/settings.json" kbs-remove
backup_file "$HOME/.config/opencode/AGENTS.md" kbs-remove
backup_file "$HOME/.config/zed/AGENTS.md" kbs-remove

remove_if_owned_file "$BIN_DIR/kbs" "$KBS_BIN_NEEDLE"
remove_link_or_owned_dir "$HOME/.claude/skills/knowledge-based-search"
remove_link_or_owned_dir "$HOME/.codex/skills/knowledge-based-search"
remove_link_or_owned_dir "$HOME/.pi/agent/skills/knowledge-based-search"
remove_if_owned_file "$HOME/.pi/agent/prompts/search.md" "knowledge-based-search"
remove_link_or_owned_dir "$HOME/.config/opencode/skills/knowledge-based-search"
remove_if_same_file "$HOME/.config/opencode/plugins/knowledge-based-search.ts" "$REPO/opencode/plugins/knowledge-based-search.ts"
remove_fenced_block "$HOME/.config/opencode/AGENTS.md"
remove_if_same_file "$HOME/.config/opencode/AGENTS.md" "$REPO/opencode/AGENTS.md"
remove_fenced_block "$HOME/.config/zed/AGENTS.md"
remove_legacy_zed_instructions

python3 "$REPO/scripts/uninstall_configs.py" claude
python3 "$REPO/scripts/uninstall_configs.py" codex
python3 "$REPO/scripts/uninstall_configs.py" pi

remove_venv

printf '%s\n' "user config remains at $HOME/.config/kbs/config.json when present"
printf '%s\n' "removed knowledge-based-search install artifacts"
