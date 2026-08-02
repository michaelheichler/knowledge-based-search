#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/lib.sh"
BIN_DIR="${KBS_BIN_DIR:-$HOME/.local/bin}"
VENV_DIR="${KBS_VENV_DIR:-$HOME/.local/share/kbs/venv}"
CONFIG_PATH="$HOME/.config/kbs/config.json"
VENV_MARKER=".kbs-owned-venv"

require_python() {
	if ! python3 -c 'import sys; raise SystemExit(sys.version_info < (3, 11))' >/dev/null 2>&1; then
		printf '%s\n' "kbs requires python3 3.11 or newer" >&2
		exit 1
	fi
}

backup_wrapper() {
	local target="$BIN_DIR/kbs"
	local escaped_kbs_bin
	printf -v escaped_kbs_bin '%q' "$ROOT/bin/kbs"
	[ -e "$target" ] || [ -L "$target" ] || return 0
	grep -qF "$escaped_kbs_bin" "$target" 2>/dev/null && return 0
	backup_file "$target"
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

install_python() {
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
	"$VENV_DIR/bin/python" -m pip install -r "$ROOT/requirements.txt"
}

write_wrapper() {
	local target="$BIN_DIR/kbs"
	mkdir -p "$BIN_DIR"
	backup_wrapper
	rm -f "$target"
	{
		printf '%s\n' '#!/usr/bin/env bash'
		printf 'exec %q %q "$@"\n' "$VENV_DIR/bin/python" "$ROOT/bin/kbs"
	} >"$target"
	chmod +x "$target"
}

write_config() {
	[ ! -e "$CONFIG_PATH" ] || {
		printf '%s\n' "kept existing $CONFIG_PATH"
		return 0
	}
	local url=""
	if [ -t 0 ]; then
		printf '%s' "SearXNG base URL (empty for DuckDuckGo only): "
		read -r url || true
	fi
	mkdir -p "$(dirname "$CONFIG_PATH")"
	python3 - "$CONFIG_PATH" "$url" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
data = {"duckduckgo": True}
if sys.argv[2]:
    data["searxng_url"] = sys.argv[2]
path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
PY
	printf '%s\n' "wrote $CONFIG_PATH"
}

require_python
install_python
write_wrapper
write_config
printf '%s\n' "installed kbs wrapper at $BIN_DIR/kbs"
