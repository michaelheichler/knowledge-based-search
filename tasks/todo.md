# knowledge-based-search, task list

## Done

- CLI entry point: `bin/kbs`.
- Commands: `quick`, `search`, `get`, `deep`, `context`, `doctor`.
- Transport-free core in `server/search_core.py`.
- Session-scoped state in `server/state.py`.
- RAG daemon lifecycle in `server/rag_host.py`.
- Runtime wiring for Claude Code, Codex, Pi, and OpenCode.
- Runtime installers use `kbs`, not KBS MCP registration.
- Deleted the old MCP adapter.
- Converted tests to target `search_core`, `cli`, and `state`.

## Open

- Keep SearXNG reliability under watch.
- Keep direct engine fallbacks honest about degraded behavior.
- Re-run remote installs from git when syncing another machine.

## Release check

```sh
uv run --with pytest --with bm25s --with numpy --with pypdf pytest tests/ server/tests/ -q
bash -n install.sh
./bin/kbs doctor --json
```
