# knowledge-based-search, implementation plan

A keyless, self-hosted web-search package that makes coding agents (Claude Code, Codex, Pi)
search well and return compact, cited, agent-readable output. It ships with a sidecar skill
that carries OSINT and research tradecraft distilled from one website and three books.

This plan is the build contract. It slices work vertically (each task a complete path that runs
and is testable), orders tasks by dependency, and gates each phase behind a checkpoint.

## Confirmed intent (from interview)

- One repo at `/Users/michael/dev/skills/knowledge-based-search`.
- Four MCP tools: `quick_web_search`, `web_search`, `deep_research`, `get_content`.
- Triple-engine search, always-on merge (no fallback semantics). SearXNG primary when an
  instance address is set at install (default `https://endianness.de`), else google, duckduckgo,
  bing direct (degraded, no key, no Playwright).
- Self-hosted RAG via `skill-model-loader`: `jina-embeddings-v5-text-small` plus
  `jina-reranker-v3`, `bm25s` fusion with reciprocal-rank-fusion (k=60), bm25-only fallback when
  models are unreachable. No hosted API, no key anywhere.
- Sidecar skill teaches how to search and investigate (query craft, source verification, entity
  and people and domain tracing, cross-checking). Lean body, routes to `references/` on demand.
- Knowledge built by a sonnet agent workflow, one agent per chapter or section, into
  `references/<source>/`. Priority: website first (best), books second.
- Multi-target install (claude-code, codex, pi) plus `install.sh`, clean-coder layout as template.

## Constraints and gates (apply to every task)

- Ponytail: climb the ladder, stop at the first rung that holds. No speculative abstraction.
  Reuse `skill-model-loader` and `bm25s`, do not reinvent RAG.
- Clean-coder: WHY-only comments, real tests with assertions, no hollow or skipped tests, no
  em-dash or en-dash or spliced semicolon in any file.
- Token discipline: lean JSON output, provenance fields (title, url, snippet, source, date), no
  "just in case" padding. Default `web_search` response stays near 500 to 1000 tokens.
- Tool surface stays at four (3 to 6 is the agent sweet spot, library-confirmed).
- Stdlib first. SearXNG and DDG fetch over `urllib`/`httpx` already present, no Playwright.

## Verified facts that shape the build

- `skill-model-loader` already runs a shared host (spawn-once over a unix socket, flock,
  refcount relay-race shutdown) that owns jina v5 embeddings, a bm25 plus numpy RAG, and RRF
  fusion. The host currently serves a `judge` op only. We add `embed` and `rerank` ops, or a
  sibling host on the same pattern. `client.py` gives the connect, spawn-once, request, graceful
  `None` fallback we reuse verbatim.
- A stdio MCP server is one persistent subprocess per session. In-process state survives across
  tool calls, so the bm25 index and any warm handles persist without re-init per call.
- RRF k=60 is the canonical dense-plus-sparse fusion already used in the loader. Reuse it.
- bm25s has no incremental add, a full re-index per query batch is fine at web-result scale
  (tens of documents).
- Without SearXNG, scraping google and bing keyless and headless is brittle (soft-block,
  CAPTCHA). DuckDuckGo has a stable keyless HTML endpoint. SearXNG is strongly recommended and
  is the design default. The direct path is an honest degraded mode, labelled as such.

## Dependency graph

```
P0 scaffold
   |
P1 search core (engines + merge)  <--- the spine, everything ranks its output
   |
   +--> P2 RAG layer (model-loader embed/rerank + bm25s fusion + fallback)
   |        |
   |        +--> P3 MCP server + 4 tools (vertical, one tool at a time)
   |                 |
   |                 +--> P6 multi-target install (registers the server)
   |                 +--> P7 tests + benchmark (defines "quick", embed on/off)
   |
P4 references build (sonnet workflow)   [independent of P1..P3, gated only by P0]
   |
P5 sidecar skill + hook  (consumes P4 references, points at P3 tools)
```

P4 is independent and can run in parallel with P1 to P3 (it is the long-running sonnet workflow).
Kick it off early so summaries are ready when P5 needs them.

## Phases and tasks

Each task lists acceptance criteria (AC) and a verification step (V). A task is done only when V
passes. "Model-off" means the test uses a fake embedder or stub so it runs without weights.

### P0. Scaffold and decisions

- **T0.1 Repo skeleton.** Create the directory tree: `server/` (MCP + engines + rag),
  `skills/` (the sidecar skill), `references/` (built later), `claude-code/`, `codex/`, `pi/`,
  `tests/`, `benchmark/`, `install.sh`, `README.md`, `requirements.txt`.
  - AC: tree exists, `requirements.txt` pins only `bm25s` plus an HTTP client already available,
    no Playwright, no jina SDK.
  - V: `find` shows the tree, `python -c "import bm25s"` resolves in the target env.
- **T0.2 Config contract.** One config file read by the server: SearXNG base url (default
  `https://endianness.de`), engine toggles, top-k defaults, model-loader socket path.
  - AC: config loads with safe defaults when the file is absent.
  - V: unit test asserts defaults and override-from-file. Model-off.

CHECKPOINT 0: tree and config reviewed before any logic.

### P1. Search core (the spine)

- **T1.1 SearXNG engine.** Query the SearXNG JSON API, parse to a normalized result
  `{title, url, snippet, engine, rank}`.
  - AC: returns normalized results for a live query, times out cleanly, returns `[]` on error
    (never raises into the caller).
  - V: integration test against `https://endianness.de` asserts non-empty normalized results for
    a stable query. A unit test feeds a saved JSON fixture and asserts parsing. (Live test marked
    so CI can skip it.)
- **T1.2 DuckDuckGo engine.** Keyless HTML endpoint, same normalized shape.
  - AC: returns normalized results, handles the HTML layout, fails soft to `[]`.
  - V: unit test on a saved HTML fixture asserts parsing.
- **T1.3 Direct google and bing (degraded).** Best-effort keyless fetch, same shape, each clearly
  labelled degraded. Honest log line when blocked.
  - AC: returns results or `[]`, never raises, logs the degraded status.
  - V: unit test on fixtures, plus an assertion that a block response yields `[]` and a logged
    warning. Ponytail note in code that this path is brittle by design.
- **T1.4 Merge and dedup.** Run enabled engines concurrently, merge, dedup by normalized URL,
  keep per-engine rank for later fusion.
  - AC: merged list is deduped, preserves provenance (which engines returned each url), bounded
    by a max-results cap.
  - V: unit test with three fake engines asserts dedup, provenance union, cap, and that one slow
    engine does not block the others (timeout isolation). Model-off.

CHECKPOINT 1: search core returns clean merged results from a real query. This is the first
runnable vertical slice (query in, ranked-by-engine results out).

### P2. RAG layer

- **T2.1 Sibling embed/rerank host (decided after rescanning the loader).** Do NOT extend
  `skill-model-loader/host.py` or `backends.py`. Reasons from the scan: `backends.py` hardcodes
  the english and clean-coder lib paths and routes `judge(kind)` to their Gemma-backed prose/code
  judges, the pool work item is a file path (embed/rerank take inline texts), and the module
  swaps `sys.modules` per call, so a third model path is fragile and risks the shared Gemma load.
  Instead build a sibling host on the same proven pattern, reusing `client.py`, `refcount.py`,
  `pool.py`, the flock and relay-race shutdown as libraries. It runs on its own socket, loads only
  `jina-embeddings-v5-text-small` and `jina-reranker-v3`, and never touches the judge path. It
  stays machine-level so Claude Code, Codex, and Pi share one load. First confirm the loader
  interpreter (mlx and sentence_transformers are absent from system python3, so the loader runs in
  its own venv), the sibling host uses that interpreter.
  - AC: `embed(texts) -> vectors` and `rerank(query, docs) -> scored order` answer over a
    dedicated socket, models load once and stay warm across calls, host stays single-instance
    under its flock, the existing judge host and its tests are untouched.
  - V: foreground test with models on, hard timeout: two `embed` calls, assert the model loads
    once (second call warm), one sibling-host process, freed after release. Port the loader
    lifecycle tests against the new socket. Run the existing loader test to prove no regression.
- **T2.2 RAG client shim.** A thin client in `server/rag.py` using `skill-model-loader/client.py`
  to call `embed`/`rerank`, with a bm25-only in-process fallback (`bm25s` plus RRF k=60) when the
  host is unreachable.
  - AC: `rank(query, results)` returns a fused ranked order. With the host up it uses embed plus
    rerank plus bm25 fused by RRF. With the host down it returns bm25-only order. Never raises.
  - V: unit test with a stub host asserts the fused path. A second test with the host forced
    unreachable asserts bm25-only and no exception. Model-off via stub.
- **T2.3 Summarize.** Condense the top reranked chunks into a short cited synthesis for tool
  output. Extractive first (cheap, no model), upgrade only if the benchmark shows it is needed.
  - AC: produces a 2 to 3 sentence synthesis plus the citation list, deterministic, token-bounded.
  - V: unit test asserts length bound, citation count, and that every cited url appears in the
    input. Model-off.

CHECKPOINT 2: a query flows search -> rag.rank -> summarize and returns a cited, ranked,
token-bounded result, both with and without the model host. Decide here whether the reranker
earns its place for web results (record the measurement).

### P3. MCP server and the four tools

Build one tool at a time, each a complete vertical path (request to cited response).

- **T3.1 MCP server skeleton.** A stdio MCP server registering the tool set, reading the config,
  holding the bm25 index in-process across calls.
  - AC: server starts, lists four tools, handles a `tools/call`, shuts down on stdin EOF.
  - V: stub MCP client lists tools and round-trips a no-op. Model-off.
- **T3.2 `web_search`.** Full pipeline: merge engines, fetch top pages, chunk, embed, RAG-retrieve,
  rerank, summarize. Returns `{summary, citations:[{title,url,snippet,source,date}], result_ids}`.
  - AC: default response near 500 to 1000 tokens, result_ids are opaque handles reusable by
    `get_content` and `deep_research`, no raw page bodies in the default response.
  - V: integration test on a live query asserts schema, token bound, and that result_ids resolve.
- **T3.3 `quick_web_search`.** Fast "feeling lucky" lookup. Rerank engine snippets, return top few
  with urls. Embedding on or off is a runtime switch defaulted by the benchmark (P7).
  - AC: latency clearly below `web_search` on the same query, same citation schema, no page fetch
    in the default mode.
  - V: integration test asserts the schema and that it returns without fetching pages. Timing
    recorded for P7.
- **T3.4 `get_content`.** Drill-down: take a `result_id` or url, fetch and clean one page, condense
  against the original query. Truncate to a token cap (around 8k), strip nav and ads.
  - AC: returns cleaned markdown bounded by the cap, resolves a prior result_id without re-querying
    the engines.
  - V: integration test fetches a known stable page and asserts the cap and that boilerplate is
    stripped.
- **T3.5 `deep_research`.** Multi-round loop: decompose the question, run `web_search` across
  sub-queries, follow drill-downs, synthesize a structured cited report
  `{summary, sections:[{heading, content, sources}], citations}`. Bounded rounds. Description warns
  it is expensive.
  - AC: bounded by `max_rounds`, every section cites sources present in the run, total cost logged.
  - V: integration test on a small query asserts bounded rounds, section-to-source integrity, and
    that it terminates.

CHECKPOINT 3: all four tools answer end to end against a live query with cited, bounded output.

### P4. References build (sonnet workflow, runs early and parallel)

- **T4.1 Source extraction.** Extract text from the three books and crawl the website sections.
  EPUB via a stdlib-friendly parser, PDF via a text extractor, website via plain fetch (no
  Playwright). Produce per-chapter or per-section raw text chunks with stable ids.
  - AC: each source yields an ordered list of `{id, title, text}` units (chapters or sections).
  - V: a manifest lists every unit with a non-empty text length. Spot-check three units per source.
- **T4.2 Summarization workflow.** One sonnet agent per unit, writing a short focused summary to
  `references/<source>/<id>.md`, scoped to search and investigation tradecraft (not a generic
  book summary). Website first, books second. Mirror the `algorithmic-thinking/references` format
  (front-matter title, tight sections, a table of contents per source).
  - AC: every unit has a summary file, each under a length cap, each tagged with the source and a
    one-line "use this when" hook for the skill to route on.
  - V: count of summary files equals count of units, a sample of five reads as tradecraft guidance
    not filler, no em-dash or en-dash present (gate check across the directory).
- **T4.3 Reference index.** One `references/README.md` table of contents routing the skill to the
  right file by topic (query craft, verification, entity tracing, people search, domain and
  network, fact-checking).
  - AC: every summary file is reachable from the index by topic.
  - V: link check, every file linked, no dead links.

CHECKPOINT 4: references built and reviewed for quality and licensing note (books are personal
copies, summaries are derivative notes, record provenance).

### P5. Sidecar skill and hook

- **T5.1 SKILL.md.** Lean body teaching the search-and-investigate workflow: pick the right tool,
  craft queries, verify sources, trace entities, cross-check, cite. Routes to `references/` by
  topic. Pushy description for reliable triggering.
  - AC: body under the skill length guidance, all deep knowledge behind `references/` pointers,
    description names concrete triggers (research, verify a claim, find who, OSINT, look up).
  - V: skill-creator trigger evals later. For now, a read-through confirms it routes rather than
    inlines, and names the four tools with when-to-use-each.
- **T5.2 Session-start hook.** A short start statement injected per runtime: a keyless web-search
  tool is available, prefer it over guessing, here is when to reach for each tool and how to drill
  down. Points at the skill for tradecraft.
  - AC: statement is short (a few lines), names the four tools and the drill-down path, present for
    each runtime.
  - V: hook fires in a Claude Code session and the statement appears. Codex and Pi variants exist
    and are wired in their config.

CHECKPOINT 5: skill plus hook reviewed for triggering and brevity.

### P6. Multi-target install

- **T6.1 Per-runtime layout.** Populate `claude-code/`, `codex/`, `pi/` with the skill, hook, and
  MCP server registration each runtime expects, mirroring `clean-coder-discipline` as a template.
  - AC: each runtime directory has its skill copy, hook wiring, and MCP server registration entry.
  - V: inspect each runtime config registers the server and the hook.
- **T6.2 `install.sh`.** Idempotent installer that asks for the SearXNG address (default
  `https://endianness.de`), writes config, registers the MCP server and hook for the chosen
  runtime, and verifies `bm25s` plus the model-loader socket path.
  - AC: re-running does not duplicate entries, missing SearXNG input falls back to the default,
    install verifies the server starts.
  - V: run install into a temp target, assert config written, server lists tools, re-run is a
    no-op.

CHECKPOINT 6: clean install on at least Claude Code, server reachable, tools callable.

### P7. Tests and benchmark

- **T7.1 Benchmark harness.** Time `quick_web_search` and `web_search` over a fixed query set,
  with embedding on and off for quick, recording latency and a relevance proxy (rank of the
  known-best url).
  - AC: produces a table of latency and relevance per mode.
  - V: harness runs and writes the table.
- **T7.2 Settle the open decisions.** From the table, set the default for `quick_web_search`
  embedding on or off, and define the "quick" latency target. Record both in the README with the
  measured numbers.
  - AC: defaults set with data behind them, not a guess.
  - V: README states the chosen default and the measured latency that justifies it.
- **T7.3 Full test pass and clean-coder gate.** Run the whole suite, confirm no hollow or skipped
  tests, run the punctuation and clean-coder checks across the repo.
  - AC: suite green, gates clean.
  - V: test runner exits zero, gate detector reports clean.

CHECKPOINT 7: package complete, benchmarked, gates clean. Ready for skill-creator evals and
description optimization.

## Out of scope

- Hosted RAG APIs, any API key handling, Playwright, the existing academic table-research
  workflow in `deep-research-skills` as a dependency.

## Open risks

- The sibling embed and rerank host reuses `skill-model-loader` internals. Keep it additive, run
  it on its own socket, and never alter the `judge` path the other skills depend on.
- Keyless google and bing scraping is brittle. The design depends on SearXNG, and the direct path
  stays a labelled degraded mode.
- The references summaries are derivative notes from personal book copies. Record provenance,
  keep summaries short and transformative, do not reproduce long passages.
- `deep_research` token cost can balloon. Bound rounds, log spend, warn in the tool description.
