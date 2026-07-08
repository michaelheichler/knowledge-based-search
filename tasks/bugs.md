# Bug and reliability list

## Open

- No known blocking bugs after the CLI migration.
- Public SearXNG instances can be rate-limited or intermittent. Keep direct keyless engines as degraded fallbacks and prefer a reliable SearXNG instance when available.

## Closed

- KBS no longer depends on a runtime MCP server.
- Claude Code, Codex, Pi, and OpenCode now receive instructions or hooks that call `kbs` through the shell.
- The deleted adapter is no longer imported by tests or benchmarks.
- Context memory is file-backed through `server/state.py`. The dead in-process context dict was removed.

## Verification

```sh
uv run --with pytest --with bm25s --with numpy --with pypdf pytest tests/ server/tests/ -q
bash -n install.sh
./bin/kbs doctor --json
```
