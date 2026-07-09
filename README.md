# knowledge-based-search

Keyless web search for coding agents through one shell command: `kbs`.

The package gives Claude Code, Codex, Pi, OpenCode, and Zed a shared search path without an MCP server. Agents call `kbs` through their normal shell tool, and the CLI returns compact, cited output.

## Commands

```sh
kbs quick <query>      # one fast fact, ranked links and snippets
kbs search <query>     # full search pipeline, cited summary
kbs get <url>          # open one source in full
kbs deep <query>       # bounded multi-round cited report
kbs context <query>    # context-aware search with session memory
kbs doctor             # check config, daemon, PATH, and examples
```

Use `--json` on any command for machine-readable output.

## Components

- `bin/kbs`: executable entry point.
- `server/cli.py`: argument parsing, rendering, exit codes, and doctor output.
- `server/search_core.py`: transport-free search, content fetch, deep research, and context search.
- `server/state.py`: session-scoped context memory.
- `server/rag.py` and `server/rag_host.py`: optional local ranking daemon with bm25 fallback.
- `hooks/`: runtime reminders that nudge agents toward `kbs` when a prompt needs current sources.
- `skills/knowledge-based-search/`: agent-facing method guide and reference notes.
- `claude-code/`, `codex/`, `pi/`, `opencode/`: runtime wiring. Zed reuses the shared instruction block written to `~/.config/zed/AGENTS.md`.

## Install

```sh
./install.sh --claude --codex --pi --opencode --zed -y
```

The installer:

- writes `server/config.json` with the SearXNG URL,
- links `bin/kbs` into `${KBS_BIN_DIR:-$HOME/.local/bin}`,
- backs up existing runtime config before editing it,
- installs the skill or instruction file for each selected runtime,
- installs hooks where the runtime supports them,
- prints the exact agent instruction block.

Make sure the bin directory is on `PATH`. For zsh on Linux, a common choice is:

```sh
printf '\nexport PATH="$HOME/.local/bin:$PATH"\n' >> ~/.zshenv
```

## Configuration

Default config lives in `server/config.json`:

```json
{"searxng_url": "https://endianness.de", "duckduckgo": true}
```

Override at runtime with `KBS_CONFIG`, either as JSON or as a path to a JSON file.

Context memory defaults to `~/.cache/knowledge-based-search/state.json`. Override with `KBS_STATE_FILE`.

## Development

```sh
uv run --with pytest --with bm25s --with numpy --with pypdf pytest tests/ server/tests/ -q
bash -n install.sh
./bin/kbs doctor --json
```

No MCP server remains in the runtime path. The old adapter was removed after the CLI path was proven for all supported runtimes.
