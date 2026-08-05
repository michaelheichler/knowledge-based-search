# knowledge-based-search: Scientific Research Backend Requirements

Defined: 2026-08-03 | Core value: one keyless command surface for web and scientific research, with an honest, citation-grounded literature review

## Domain Context

**Research Date:** 2026-08-03
**Domain:** Literature review methodology and search strategy for an automated, keyless research tool

Three sources ground the design decisions below. Grant & Booth (2009), *A typology of reviews: an analysis of 14 review types and associated methodologies* (Health Information & Libraries Journal), supplies the SALSA framework (Search, Appraisal, Synthesis, Analysis) and a comparison table of 14 review types. Snyder (2019), *Literature review as a research methodology: An overview and guidelines* (Journal of Business Research), supplies the four-phase review process (design, conduct, analysis, write-up) and common failure modes. Pautasso (2013), *Ten Simple Rules for Writing a Literature Review* (PLoS Computational Biology, via PMC3715443), supplies practical search-tracking and currency guidance. The personal library MCP (216 books) was queried for supplementary methodology evidence and returned none above its relevance floor. That absence is treated as a finding, not a gap to guess around.

The central design decision this research settles: a kbs-generated review must be classified as a **Rapid Review** (Grant & Booth, 2009, Table 1), not a Systematic Review. A Rapid Review is defined by time-constrained search completeness, time-limited quality appraisal, and narrative-plus-tabular synthesis, which matches what a single keyless CLI tool can honestly deliver in a 2 to 4 page bounded output. Claiming Systematic Review rigor (exhaustive multi-database searching, formal inclusion or exclusion protocol) would misrepresent the output.

## v1 Requirements

### Scientific source integration
- [ ] **REQ-01**: Scientific search requests route through kbs's existing keyless-engine allowlist (web providers) plus the personal library MCP as an additional source pool, never introducing a new external network path. (Grant & Booth, 2009: the SALSA "Search" component requires a documented, bounded source scope.)
- [ ] **REQ-02**: Book-derived evidence surfaces in scientific research results (`kbs search`, `kbs deep`, `kbs context`) through the same trust-tier and ranking pipeline web evidence already uses, not a separate silo. (Snyder, 2019, section 3.1: a review's search scope must be defined as one coherent whole before execution. Addresses the common pitfall of siloed source pools.)

### Ranking
- [ ] **REQ-03**: Every scientific search combines relevance rank and date or recency rank by default. No mode strips either signal. (Non-negotiable. Grounded in Grant & Booth, 2009, Table 1: a Rapid Review requires both a quality-of-evidence appraisal and a current state-of-knowledge synthesis, which together require both signals.)

### Terminology alternatives
- [ ] **REQ-04**: Before executing a scientific search, kbs surfaces up to 5 terminology alternatives for the user's query term, each with a one-line scope note. (Typical approach: Snyder, 2019, section 3.1, search terms should be words and concepts directly related to the research question. Pautasso, 2013, rule 2, track and vary search terms for reproducibility. Display format is a new design, not a prior given: see PROJECT.md Key Decisions.)

**Terminology-alternative display format (new design):**
```
Terminology alternatives for "<original term>":
  1. <alternative> (one-line scope/nuance note)
  2. <alternative> (one-line scope/nuance note)
  ...
  (up to 5, omitted entirely if none found)
```
Rendered through kbs's existing `_render*` human-output convention (`server/cli.py`) for text mode, and as a `terminology_alternatives` array (max length 5) alongside existing fields in `--json` mode.

### Literature review generation: methodology
- [ ] **REQ-05**: On explicit user or agent request, kbs generates a Rapid Review-type literature review PDF, 2 to 4 pages. (Grant & Booth, 2009, Table 1: Rapid review methodology, not Systematic Review, since kbs cannot deliver exhaustive multi-database searching or a pre-registered inclusion or exclusion protocol.)
- [ ] **REQ-06**: The review is structured in four phases per Snyder (2019), section 3. Stated topic and question (design). Documented search scope across web and library sources with per-source outcome (conduct). Thematic synthesis (analysis). Dense citation-grounded write-up capped at 2 to 4 pages with no filler (write-up).
- [ ] **REQ-07**: The review's synthesis groups findings by theme, not by describing each source in turn. (Snyder, 2019, section 5: describing sources one by one without deeper analysis is the most common reason literature reviews fail to make a contribution.)
- [ ] **REQ-08**: Every claim in the generated review cites its source inline. No source is listed without being cited in the running text. (Snyder, 2019, section 4: quality requires depth, rigor, and replicability, following Palmatier et al.'s criteria as summarized in the source.)
- [ ] **REQ-23**: The review's prose register avoids filler and "book writing" language, matching the clipped, structured register demonstrated in the Grant & Booth (2009) and Snyder (2019) source papers themselves.

### Literature review generation: output format
- [ ] **REQ-19**: The review is produced as LaTeX source compiled to PDF, in standard academic style, using Harvard (author-date) citation style. Content elements (mathematical formulas, graphs) are chosen automatically based on the topic domain, not a fixed template (user decision, Phase 1 discussion, deferred to Phase 4 scope).
- [ ] **REQ-21**: `--literature-review` produces a separate guide document, distinct from the review PDF, documenting the review methodology for the calling agent to reuse. (User decision, Phase 1 discussion.)
- [ ] **REQ-22**: Generated reviews are saved to disk inside the project directory, not only streamed back to the caller. (User decision, Phase 1 discussion: research archival.)

### Literature review generation: integrity
- [ ] **REQ-20**: The Analysis section presents supporting evidence only as short, quotation-marked excerpts copied verbatim from their attributed source, each with an inline citation (`\citep{key}`). No excerpt is ever presented as though it were review-authored prose, and kbs never paraphrases or fabricates a connecting claim. Each theme's synthesis is left as an explicit, clearly marked instruction for a downstream agent to write (for example an `% AGENT-SYNTHESIS: ...` LaTeX comment). kbs itself performs no generative synthesis, matching v1 scope's absence of any local generative model. An automated verification step, run before the review is finalized, confirms that (a) every rendered excerpt's text exactly matches a sentence in its attributed, retrieved source text (guards against fabrication or misattribution, not against similarity), and (b) every citation key used in the body has exactly one corresponding bibliography entry and vice versa. This step no longer measures or flags near-verbatim similarity between claim and source. An excerpt matching its source exactly is the intended, honest behavior under this design.

### Non-negotiables (carried from brief)
- [ ] **REQ-09**: No search query, rewritten alternative, or literature-review draft is ever transmitted outside kbs's existing keyless-engine allowlist.

### Scientific platforms (added during Phase 1 discussion, 2026-08-03)
- [ ] **REQ-12**: arXiv, PubMed (NCBI E-utilities), Semantic Scholar (Graph API), and CrossRef are added as default keyless scientific providers in `server/engines.py`, following the existing provider adapter pattern. Keyless status and base endpoints verified directly on 2026-08-03, not assumed from training data.
- [ ] **REQ-13**: OpenAlex is available only as an optional, user-keyed provider, matching how Tavily and SearXNG already work, never a default. (Verified 2026-08-03: OpenAlex now requires a free API key, which would violate REQ-09 if made default.)
- [ ] **REQ-14**: A `--scientific` flag triggers the scientific provider group (arXiv, PubMed, Semantic Scholar, CrossRef, library MCP). A `--platform <list>` flag narrows scope to one or more specific platforms when `--scientific` is active. Explicit flags, not an auto-heuristic (user decision, Phase 1 discussion).
- [ ] **REQ-15**: Library MCP results are assigned a synthetic `library://{book_id}?chunk={chunk_id}` identifier so they flow through the existing URL-based merge and dedup pipeline (`engines.py`'s `merge()`/`norm_url()`) without a new result shape. (Corrected 2026-08-03 by Phase 1 research: a `#{chunk_id}` fragment is dropped by `norm_url()` and would collapse all chunks of one book into a single merged result. The query-string form is preserved correctly.)
- [ ] **REQ-16**: Library results get a fixed high-trust tier (no domain to score). The four new scientific domains get real `trust.json` entries. Per-paper trust additionally weighs citation count (available from Semantic Scholar and CrossRef) and query-alignment (the existing relevance signal). View or download count is explicitly out of scope: no verified keyless API exposes it.
- [ ] **REQ-17**: The four new scientific providers get standard `engine_state.py` pacing and cooldown entries matching their documented limits. Library MCP stays exempt from pacing, called synchronously outside the network-provider thread pool since it is a private LAN MCP server, not an in-process local call. (Corrected 2026-08-03: research found the library MCP is an HTTP server on the LAN, not local. The pacing exemption still holds. The reason changed from "local call" to "not part of the paced network fan-out.")

## v2 Requirements
- [ ] **REQ-10**: Multi-round refinement for literature reviews, reusing kbs's existing query-correction retry loop (`server/search_core.py`'s refinement-budget mechanism) extended to scientific terminology.
- [ ] **REQ-11**: Citation export formats (BibTeX, RIS) for generated reviews.
- [ ] **REQ-18**: Local generative LLM pre-drafting for literature reviews via a new MLX model (research-backed candidate: AI2's OLMo-2, MLX-converted, not Qwen or Gemma family). No generative LLM exists in kbs's stack today (only embedding and reranking). Feasibility to validate during Phase 4 planning before commitment.

## Out of Scope

- Full PRISMA-compliant Systematic Review methodology (deliberately excluded: no database licenses, no multi-month timeline, and a Rapid Review is the honest classification per Grant & Booth, 2009)
- Integrative Review-style new theory generation (deliberately excluded: requires sustained critical synthesis beyond what a bounded automated output can produce, per Snyder, 2019, section 2.1.3)
- Writing implementation code in this pass (owned by vbw-lead and vbw-dev once phases below are scoped into plans)
- Any UI beyond the existing kbs CLI and agent tool surface
