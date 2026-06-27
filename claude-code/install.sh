#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
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

mkdir -p "$HOME/.claude/skills"
backup "$HOME/.claude.json"
ln -snf "$REPO/skills/knowledge-based-search" "$HOME/.claude/skills/knowledge-based-search"
python3 "$REPO/claude-code/merge-claude-settings.py" "$HOME/.claude.json" "$REPO/claude-code/claude-settings.snippet.json" "$REPO"
