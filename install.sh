#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_NAME="knowledge-based-search"
SERVER_PY="$REPO/server/mcp_server.py"
MCP_PY="/Users/michael/dev/skills/skill-model-loader/.venv/bin/python"

WANT_CLAUDE=auto
WANT_CODEX=auto
WANT_PI=auto
ASSUME_YES=0

for arg in "$@"; do
  case "$arg" in
    --claude) WANT_CLAUDE=1 ;;
    --codex) WANT_CODEX=1 ;;
    --pi) WANT_PI=1 ;;
    -y|--yes) ASSUME_YES=1 ;;
    -h|--help)
      printf '%s\n' "Usage: ./install.sh [--claude] [--codex] [--pi] [-y]"
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
  mkdir -p "$HOME/.pi/agent"
  backup "$cfg"
  python3 "$REPO/pi/merge-pi-settings.py" "$cfg" "$ext"
  printf '%s\n' "Pi extension registered"
}

verify_claude() {
  if command -v claude >/dev/null 2>&1 && claude mcp list 2>/dev/null | grep -q "$SERVER_NAME"; then
    printf '%s\n' "Claude lists $SERVER_NAME"
  else
    printf '%s\n' "Claude does not list $SERVER_NAME"
  fi
}

verify_codex() {
  if command -v codex >/dev/null 2>&1 && codex mcp list 2>/dev/null | grep -q "$SERVER_NAME"; then
    printf '%s\n' "Codex lists $SERVER_NAME"
  else
    printf '%s\n' "Codex does not list $SERVER_NAME"
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

CLAUDE="$(resolve "$WANT_CLAUDE" "$HOME/.claude")"
CODEX="$(resolve "$WANT_CODEX" "$HOME/.codex")"
PI="$(resolve "$WANT_PI" "$HOME/.pi")"

if [ "$CLAUDE" = 0 ] && [ "$CODEX" = 0 ] && [ "$PI" = 0 ]; then
  printf '%s\n' "nothing selected" >&2
  exit 1
fi

write_config "$(prompt_url)"

[ "$CLAUDE" = 1 ] && install_claude
[ "$CODEX" = 1 ] && install_codex
[ "$PI" = 1 ] && install_pi

printf '%s\n' "MCP command: $MCP_PY $SERVER_PY"

[ "$CLAUDE" = 1 ] && verify_claude
[ "$CODEX" = 1 ] && verify_codex
[ "$PI" = 1 ] && verify_pi
