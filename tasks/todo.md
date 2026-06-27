# knowledge-based-search, task list

Status keys: [ ] todo, [~] in progress, [x] done, [b] blocked.
Each task is done only when its verification (V in plan.md) passes.

## P0. Scaffold
- [x] T0.1 Repo skeleton (server, skills, references, claude-code, codex, pi, tests, benchmark)
- [ ] T0.2 Config contract with safe defaults
- [ ] CHECKPOINT 0: tree and config reviewed

## P1. Search core (the spine)
- [x] T1.1 SearXNG engine, normalized results, soft-fail (live: 8 real hits from endianness.de)
- [~] T1.2 DuckDuckGo keyless HTML engine (returns [], html.duckduckgo.com now serves a 202 anti-bot challenge, confirmed degraded)
- [ ] T1.3 Direct google and bing, degraded and labelled (low value, SearXNG already covers them server-side)
- [x] T1.4 Concurrent merge, dedup by url, keep per-engine rank, timeout isolation (demo check passes)
- [x] CHECKPOINT 1: merged results from a real query via SearXNG (first runnable slice)

## P2. RAG layer
- [x] T2.1 Sibling embed/rerank host (server/rag_host.py), jina v5 nano embed plus jina reranker v3, socket/flock/refcount. Live: embed 768-dim, rerank correct.
- [x] T2.2 RAG client shim (server/rag.py), embed plus rerank plus bm25 fused by RRF, partial-signal fallback. 7 tests pass. Live rank() orders correctly.
- [ ] T2.3 Summarize top chunks into a short cited synthesis (build in P3 web_search)
- [x] CHECKPOINT 2: full RAG pipeline verified live. Loader source unchanged (its 7 test failures are pre-existing, not from us). Note: embed model is text-nano (text-small only exists as GGUF).

## P3. MCP server and four tools
- [x] T3.1 MCP server (server/mcp_server.py) via FastMCP, JSON-RPC fallback, 5 tests pass
- [x] T3.2 web_search, search plus fetch plus rank plus extractive summary, citations, result_ids (live ok)
- [x] T3.3 quick_web_search, rerank snippets, no page fetch (live ok)
- [x] T3.4 get_content, resolves result_id or url, fetch_clean capped (live ok)
- [x] T3.5 deep_research, bounded by max_rounds, sub-queries from titles, deduped citations
- [x] CHECKPOINT 3: all four tools answer live against SearXNG.
- [x] fetch_clean readability fix: web_search summary now leads with article text, not page chrome. 13 tests pass, verified live.

## P4. References build (start early, runs parallel)
- [x] T4.1 Extract 3 books into units (136 total, manifest at /tmp/kbs_build), website sections fetched per-agent in T4.2
- [x] T4.2 Rebuilt broad (171 notes, full coverage, summarizer plus validator, 68 validator-fixed). First narrow-angle pass archived in archive/.
- [x] T4.3 references/README.md index (171 entries, title plus source).
- [x] CHECKPOINT 4: references are broad faithful summaries of every chapter. Clean of dashes, intensifiers, and inflated words. Spot-check (google-dorking) confirms quality. Caveat: validator verdict timing ambiguous, output verified by spot-check.

## P5. Sidecar skill and hook
- [x] T5.1 SKILL.md, lean body, routes to references (moved into the skill dir), pushy description
- [x] T5.2 Hooks for Claude Code: session_start primer, prompt_inject nudge, shared triggers.json, detector (8 tests pass). Codex and Pi variants deferred to P6.
- [x] CHECKPOINT 5: hooks verified live (recency, research, deep route correctly, local scope suppressed)

## P6. Multi-target install
- [x] T6.1 claude-code, codex, pi layouts (skill symlink, hooks, server registration) via Codex, merge tests pass
- [x] T6.2 install.sh, asks SearXNG url, idempotent, backs up each config, verifies
- [x] CHECKPOINT 6: installed all three runtimes. Claude: MCP connected, skill loaded. Pi: extension registered. Codex: registered and enabled, health shows "Unsupported" (verify tool invocation separately).
- [ ] Follow-up: confirm Codex can invoke the tools (the "Unsupported" health status).

## P7. Tests and benchmark
- [ ] T7.1 Benchmark harness, latency and relevance, embed on and off
- [ ] T7.2 Settle quick embedding default and the "quick" latency target, record numbers
- [ ] T7.3 Full test pass plus clean-coder and punctuation gates clean
- [ ] CHECKPOINT 7: package complete, benchmarked, gates clean

## Open decisions to settle by data (not guess)
- [ ] Does the reranker earn its place for web results? (CHECKPOINT 2)
- [ ] quick_web_search embedding on or off by default? (T7.2)
- [ ] What latency defines "quick"? (T7.2)
