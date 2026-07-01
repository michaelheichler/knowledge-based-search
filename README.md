# knowledge-based-search

A keyless, self-hosted web-search package for coding agents (Claude Code, Codex, Pi). It runs
triple-engine search (SearXNG primary, duckduckgo, bing, google), ranks results with a local
RAG layer (jina embeddings plus reranker plus bm25, no API key), and returns compact cited
output. It ships with a sidecar skill that teaches search and investigation tradecraft distilled
from one website and three books.

Status: in development. See `tasks/plan.md` for the build plan and `tasks/todo.md` for progress.

## Components

- `server/` the MCP server, search engines, and the RAG client.
- `skills/knowledge-based-search/` the sidecar skill (how to search and investigate).
- `references/` tradecraft summaries built from the website and books.
- `claude-code/`, `codex/`, `pi/` per-runtime install layouts.
- `install.sh` the multi-target installer.

## Tools

- `quick_web_search` fast lookup, rerank, summarized.
- `web_search` full pipeline, embed plus RAG plus rerank, cited output.
- `deep_research` bounded multi-round research, structured cited report.
- `deep_context_aware_search` context-aware broad search with session memory.
- `get_content` drill down into one source by result id or url.

## Design rules

Keyless end to end. No hosted API, no Playwright. SearXNG strongly recommended (the direct
google and bing path is a labelled degraded mode). RAG runs through a machine-level model host so
the models load once across runtimes.
