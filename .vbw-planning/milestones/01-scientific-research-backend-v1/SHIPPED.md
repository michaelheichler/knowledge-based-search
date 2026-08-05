# Shipped: Scientific Research Backend v1

**Shipped:** 2026-08-06

## Summary

Extends `kbs`'s existing keyless web-search pipeline to also serve scientific research requests against a unified web-plus-library source pool, then adds an on-demand Rapid Review PDF generator on top.

## Phases

1. **Scientific Source Integration**: Routes `--scientific` queries through arXiv, PubMed, Semantic Scholar, CrossRef, and the personal library MCP as first-class sources under one trust and ranking pipeline.
2. **Combined Relevance and Date Ranking**: Guarantees every scientific search combines relevance and date signals by default, no mode strips either.
3. **Module Size Refactor**: Decomposed `server/search_core.py` and `server/enforce.py` along existing internal seams, no behavior change.
4. **Terminology Alternatives**: A new, capped, source-grounded terminology-alternative display for scientific queries.
5. **Literature Review Generation**: `--literature-review` produces a LaTeX-compiled Rapid Review PDF, `.bib` file, and methodology guide. The Analysis section presents verbatim quoted, cited evidence (never fabricated paraphrase), with synthesis explicitly delegated to the invoking agent via `% AGENT-SYNTHESIS` markers.

## Metrics

- Phases: 5
- Tasks executed: 89
- Commits: 86
- Requirements: 21/23 satisfied (REQ-10 multi-round refinement and REQ-11 citation export formats were not scoped into any phase this milestone, deferred)
- Recorded deviations: 14 across all phases and remediation rounds

## Key Decisions

- Generated reviews are typed as Rapid Reviews, not Systematic Reviews (Grant & Booth, 2009).
- Review write-up follows Snyder's four-phase structure (design, conduct, analysis, write-up) (Snyder, 2019).
- The Analysis section never fabricates synthesis prose. Evidence is verbatim quotation with citation. Synthesis is an explicit agent-fill placeholder, since kbs has no local generative model in v1 (REQ-18 deferred as a stretch goal).
- Scientific search shares one ranking and trust pipeline across web and library sources, never a separate silo.

## Remediation History

Phase 5 required 2 UAT remediation rounds after its initial UAT found a critical defect: a word-scrambling technique built to dodge a mechanical paraphrase-integrity check produced unreadable Analysis-section prose. Round 1 replaced synthesized claim fabrication with honest verbatim quotes plus an explicit downstream-agent synthesis placeholder. It also fixed a related CrossRef/PubMed metadata-as-evidence defect. It rewrote `methodology.md` as connected narrative grounded in a real academic search-methodology example, and reworded REQ-20 to match the new design. Round 2 fixed a minor LaTeX paragraph-indentation defect the round-1 UAT itself surfaced.
