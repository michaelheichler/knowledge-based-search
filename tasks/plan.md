# knowledge-based-search, current plan

## Goal

Keep `knowledge-based-search` as a small, keyless CLI for coding agents.
Agents use `kbs` through their shell tool instead of an MCP server.

## Current architecture

- `bin/kbs` starts the CLI.
- `server/cli.py` owns command parsing, rendering, exit codes, and `doctor`.
- `server/search_core.py` owns search, result ids, source fetch, deep research, and context search.
- `server/state.py` owns file-backed, session-scoped context memory.
- `server/rag.py` and `server/rag_host.py` own local ranking and daemon lifecycle.
- `hooks/` and `skills/knowledge-based-search/` teach agents when and how to search.
- `claude-code/`, `codex/`, `pi/`, and `opencode/` contain runtime wiring.

## Supported commands

- `kbs quick <query>` for one fast fact.
- `kbs search <query>` for a cited summary.
- `kbs get <url>` for opening one source.
- `kbs deep <query>` for bounded multi-round research.
- `kbs context <query>` for context-aware search with session memory.
- `kbs doctor` for install and daemon diagnostics.

## Install contract

`install.sh` must stay idempotent and portable:

- no machine-specific paths,
- backup before editing user runtime config,
- link `bin/kbs` into `${KBS_BIN_DIR:-$HOME/.local/bin}`,
- preserve unrelated user config,
- strip old KBS MCP registration when encountered,
- install the runtime instruction or hook path for each selected target.

## Verification contract

Before release or sync to another machine, run:

```sh
uv run --with pytest --with bm25s --with numpy --with pypdf pytest tests/ server/tests/ -q
bash -n install.sh
./bin/kbs doctor --json
```

For a remote machine, install from git, not from a copied working tree.
