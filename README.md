# kbs

`kbs` is a keyless web search CLI for coding agents. Agents call it through their normal shell tool, not through an MCP server. This follows the approach in Mario Zechner's [What if you don't need MCP at all?](https://mariozechner.at/posts/2025-11-02-what-if-you-dont-need-mcp/).

## Search model

DuckDuckGo, Mwmbl, and Wikipedia are enabled keyless engines. When multiple engines are available, `kbs` queries them in parallel, merges duplicate results, and records provider provenance. SearXNG and Tavily are optional.

The agent contract comes from the books in `skills/knowledge-based-search/references/`:

- Query rewriting and bounded corrective rounds run before a weak result is returned.
- Human and JSON output include the correction trail.
- Search rounds, fetch counts, and output sizes have hard budgets.
- Results include source quality and confidence labels. Confirmation requires corroboration across distinct domains.
- `--raw` disables query rewriting and automatic recovery for commands that accept it.

## Commands

```sh
kbs quick <query>      # ranked links and snippets
kbs plan <query>       # book-backed research method plan
kbs search <query>     # search with a cited summary
kbs get <r1-or-url>    # fetch one result or URL
kbs deep <query>       # bounded multi-round report
kbs context <query>    # search with session memory
kbs doctor             # explain config, ranking, daemon, and PATH status
```

Add `--json` for machine-readable output.

## Scientific literature reviews

Request a bounded Rapid Review explicitly with `--scientific`:

```sh
kbs search "quantum methods" --scientific --literature-review
```

`--literature-review` requires `--scientific`. Each run writes its artifacts under
`<cwd>/reviews/<topic-slug>-<YYYYMMDD-HHMMSS>/`:

- `review.tex`, the Harvard-style LaTeX source
- `review.bib`, the cited bibliography
- `review.pdf`, the compiled review
- `methodology.md`, the run-specific methodology guide

Compilation requires a full TeX distribution, such as MacTeX or TeX Live full.
MiKTeX users must pre-install `natbib`, `harvard`, `geometry`, `amsmath`, `pgfplots`,
and `tikz`, or disable on-demand package installation. An on-demand package fetch
would add a network dependency to an otherwise offline compile step.

## Requirements

Python 3.11 or newer is required.

## Claude Code install

Add this repository as a plugin marketplace, install the plugin, then run its setup command:

```text
/plugin marketplace add michaelheichler/knowledge-based-search
/plugin install knowledge-based-search@knowledge-based-search
/kbs-setup
```

`/kbs-setup` creates the runtime environment, writes the `kbs` wrapper, and prompts for an optional SearXNG URL.

## Other runtime install

Codex, Pi, OpenCode, and Zed use the root installer:

```sh
./install.sh
```

The installer detects existing runtimes. Pass `--codex`, `--pi`, `--opencode`, or `--zed` to select one explicitly. The wrapper is installed in `${KBS_BIN_DIR:-$HOME/.local/bin}`. Put that directory on `PATH`.

## Configuration

User configuration lives at `~/.config/kbs/config.json`. The default keyless engines are:

```json
{
  "duckduckgo": true,
  "mwmbl": true,
  "wikipedia": true
}
```

Add optional SearXNG and Tavily access when available:

```json
{
  "searxng_url": "https://searxng.example.org",
  "tavily_api_key": "tvly-..."
}
```

| Config key | Default | Engine |
|---|---|---|
| `duckduckgo` | `true` | DuckDuckGo direct search |
| `mwmbl` | `true` | Mwmbl keyless JSON API |
| `wikipedia` | `true` | English Wikipedia search API |
| `google` | `false` | Google direct search or configured API |
| `bing` | `false` | Bing direct search |
| `startpage` | `false` | Startpage direct search |
| `mojeek` | `false` | Mojeek direct search |
| `searxng_url` | unset | SearXNG instance URL |
| `tavily_api_key` | unset | Tavily API, enabled when a key is present |

There is no default SearXNG URL. `KBS_CONFIG` can contain inline JSON or a path to another JSON file. `KBS_STATE_FILE` overrides the state file used for session context and result references. `KBS_ENGINE_STATE` overrides the provider pacing and cooldown state file.

## Optional dense ranking

Dense ranking requires the separate `skill-model-loader` project and compatible local models. Without them, search degrades to BM25 ranking. `kbs doctor` reports whether dense ranking is available and explains missing requirements.

## Uninstall

```sh
./remove.sh
```

The uninstaller removes owned runtime files and leaves `~/.config/kbs/config.json` in place.

## Development

```sh
python3 -m pytest tests/ server/tests/ -q
bash -n install.sh remove.sh scripts/setup.sh scripts/lib.sh
./bin/kbs doctor --json
```
