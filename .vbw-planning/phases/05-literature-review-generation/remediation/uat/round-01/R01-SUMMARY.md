---
phase: 5
round: 1
title: "Analysis section quote redesign, attribution integrity gate, Conduct/methodology cleanup, REQ-20 rewording"
type: remediation
status: complete
completed: 2026-08-05
tasks_completed: 7
tasks_total: 7
commit_hashes:
  - c7cf4dafd3db555daedd3c4eb682fc31696e5082
  - 2baec3b
  - ac1b640
  - a107e7e
  - 18a0c81
  - f042547
  - 6233dbf
  - 4220363
files_modified:
  - server/science_engines.py
  - server/review_synthesis.py
  - server/review_latex.py
  - server/review_integrity.py
  - server/review.py
  - server/tests/test_review_synthesis.py
  - server/tests/test_review_integrity.py
  - server/tests/test_review.py
  - server/tests/test_cli.py
  - .vbw-planning/REQUIREMENTS.md
deviations:
  - "Two execution attempts at Task 2 were interrupted mid-stream by an unrelated infrastructure error (API response stalled). The first left review_latex.py briefly with a syntax error, and both attempts' broken, uncommitted work were reverted with git restore before retrying. The landed commit 2baec3b is the complete, tested implementation."
  - "The Task 7 smoke run surfaced a real defect the research/plan did not anticipate: PubMed's ESummary snippet (server/science_engines.py's _pubmed_hit) is journal-name-plus-date metadata, not abstract prose, the same defect class as CrossRef. Fixed by reusing the existing source_text_is_metadata guard (commit 4220363)."
  - "A follow-on, uncommitted refactor attempt (adding a _view_bibliography helper to retain metadata-flagged hits' bibliography entries in the final rendered bib) was started during that same interrupted Task 7 attempt but never fully wired in. Direct testing confirmed completing it as started would have reintroduced review_latex.py's uncited-bibliography-entries render failure, since retained-but-uncited entries fail _validate_citations. Discarded with git restore rather than completed. The correct, already-consistent behavior is unchanged: metadata-flagged hits count in _pool_counts/Conduct search scope but are not retained in the final citable bibliography, since nothing quotes them."
known_issue_outcomes: []
pre_existing_issues: []
---

Task 1 marks CrossRef snippets as metadata and excludes them from claim generation while preserving pool counts and bibliography data.

## Task 1: Flag CrossRef snippets as non-quotable metadata

### What Was Built
- CrossRef hits now carry `source_text_is_metadata: true`, and flagged non-library hits are skipped before sentence selection.
- Synthesis tests cover CrossRef exclusion, pool counts, bibliography retention, and unaffected arXiv, PubMed, and Semantic Scholar claims.

### Files Modified
- `server/science_engines.py` -- marks CrossRef snippets as metadata.
- `server/review_synthesis.py` -- skips metadata-only claim generation.
- `server/tests/test_review_synthesis.py` -- verifies provider behavior.

### Known Issue Outcomes
- None.

### Deviations
- None.

## Task 2: Replace claim fabrication with quote records and agent-synthesis placeholders

### What Was Built
- `_reporting_frame`, `_register`, and `FILLER_DENYLIST` are deleted from `server/review_synthesis.py`. `_claim_for_hit` now emits a `quote_text` record instead of a fabricated `claim_sentence`.
- `_rebuild_views` appends structured quote records per theme and one `{"placeholder": True, "theme": theme}` marker at the end of each theme's list. `claims_for_integrity` is renamed `quotes_for_integrity` and excludes placeholder markers.
- `server/review_latex.py` gained `_render_analysis_section`, wired into `_section_blocks` for the Analysis title only (`Design`/`Conduct`/`Write-up` keep the generic `_render_prose`). Quoted text is fully escaped, `\citep{key}` is emitted unescaped, and the `% AGENT-SYNTHESIS: ...` line is a raw literal, confirmed by direct render inspection to stay a genuine LaTeX comment.
- Verified directly (not just via unit tests): rendering a two-hit, one-theme model produces two verbatim quoted excerpts with correct citation keys and one trailing `% AGENT-SYNTHESIS` comment, no scrambled prose.

### Files Modified
- `server/review_synthesis.py` -- removes claim fabrication, emits quote/placeholder records.
- `server/review_latex.py` -- adds the Analysis-section quote/placeholder renderer with correct escaping order.
- `server/tests/test_review_synthesis.py` -- rewrites all assertions from the removed `claim_sentence`/`FILLER_DENYLIST`/`claims_for_integrity` shape to the new quote-record shape.

### Known Issue Outcomes
- None.

### Deviations
- Two prior execution attempts at this task were interrupted mid-stream by an unrelated infrastructure error (API response stalled), leaving `review_latex.py` briefly with a syntax error on the first attempt. That broken, uncommitted work was reverted with `git restore` before retrying. The final landed diff shown in commit `2baec3b` is the complete, tested implementation, not a residual of either failed attempt.

## Task 3: Replace check_claims with the check_quotes attribution gate

### What Was Built
- `review_integrity.check_quotes` now flags fabricated or misattributed quote records when normalized quote text does not match a sentence in its attributed source text.
- The review fail-closed loop now checks `quotes_for_integrity`, and flagged quote records retain `source_id` for existing drop behavior.
- Dead lexical, block-length, and embedding paraphrase detection was removed. Tests now cover exact attribution, fabrication, misattribution, normalization, orchestration, and CLI flag rendering.

### Files Modified
- `server/review_integrity.py` -- replaces similarity detection with exact normalized attribution checks.
- `server/review.py` -- routes the integrity loop through `check_quotes` and `quotes_for_integrity`.
- `server/review_synthesis.py` -- updates the synthesis integrity adapter.
- `server/tests/test_review_integrity.py` -- tests quote attribution behavior.
- `server/tests/test_review.py` -- updates quote fixtures and integrity-loop mocks.
- `server/tests/test_cli.py` -- updates the floor-error flag fixture.
- `server/tests/test_review_synthesis.py` -- removes the remaining legacy integrity call.

### Known Issue Outcomes
- None.

### Deviations
- None.

### Verification
- `python3 -m pytest server/tests/` passed: 221 passed, 1 skipped.
- Legacy integrity names are absent from `server/` Python sources.
- AST parsing passed for all three changed review modules.

## Task 4: Fix Conduct section model shape

### What Was Built
- Conduct now renders one Title Case Search Scope subsection with composed pool-count prose, while machine-readable source pool counts remain available at the model top level.
- Non-empty terminology alternatives render as numbered term-plus-note lines, and empty alternatives omit the subsection.
- Verified with 30 targeted tests, 223 server tests plus 1 skip, and direct render checks for empty and populated alternatives.

### Files Modified
- `server/review_synthesis.py` -- separates machine Conduct data from the generic rendered mapping.
- `server/tests/test_review_synthesis.py` -- covers heading, count, and terminology rendering contracts.
- Commit: `a107e7e`.

## Task 5: Rewrite methodology.md generation

### What Was Built
- Replaced the fixed methodology skeleton with connected Classification, Design, Conduct, Analysis, Write-up, Integrity check, and Limitations sections.
- Methodology output now narrates real source-pool counts, trust tiers from `server/data/trust.json`, terminology alternatives, theme names, page outcomes, and quote and citation integrity guarantees. Only Limitations contains the `[AGENT:` placeholder.

### Files Modified
- `server/review.py` -- generates the Kitchenham-shaped methodology narrative and reports configured pool trust tiers.
- `server/tests/test_review.py` -- verifies every section, run data, empty and populated terminology alternatives, and the sole agent placeholder.

### Verification
- `python3 -m pytest server/tests/test_review.py -x` passed: 9 passed.
- `python3 -m pytest server/tests/ -x` passed: 224 passed, 1 skipped.
- Manual generation with five hits across arXiv, PubMed, Semantic Scholar, and CrossRef produced connected narrative with real counts and trust values, one terminology list, and one `[AGENT:` placeholder confined to Limitations.
- `python3 -m py_compile server/review.py server/tests/test_review.py` passed.
- Commit: `18a0c81`.

## Task 6: Reword REQ-20 in REQUIREMENTS.md

### What Was Built
- REQ-20 now describes verbatim, quotation-marked, cited excerpts, downstream `% AGENT-SYNTHESIS` instructions, and no kbs-authored paraphrase or synthesis prose.
- The integrity requirement now names exact quote attribution and bidirectional citation completeness, not near-verbatim similarity detection.

### Files Modified
- `.vbw-planning/REQUIREMENTS.md` -- replaces the incompatible paraphrase and near-verbatim requirement with the implemented quote-plus-placeholder design.

### Verification
- Cross-checked the requirement against quote records in `review_synthesis.py`, normalized attribution checks in `review_integrity.py`, the raw `% AGENT-SYNTHESIS` marker in `review_latex.py`, and bidirectional citation validation in `_validate_citations`.
- `grep -n "near-verbatim" .vbw-planning/REQUIREMENTS.md` found only the sentence stating that the check no longer measures or flags near-verbatim similarity.

## Task 7: End-to-end smoke: regenerate a real review and judge the output

### What Was Built
- Ran a real review generation through the actual CLI entry point (`python3 cli.py search --scientific --literature-review "quantum sensing"`, from `server/`), a live network run against real arXiv, PubMed, and CrossRef results, not synthetic fixtures.
- Output: `reviews/quantum-sensing-20260805-214437/{review.tex,review.pdf,methodology.md}`. Status `ok`, 2 pages, theme `quant-ph`, 2 sources cited.
- All six required inspections passed on this real output:
  1. `review.pdf` compiled and opened, 2 pages.
  2. Analysis section shows two real, coherent, grammatically correct quoted excerpts from arXiv papers (not scrambled prose, not CrossRef metadata). Example excerpt, citation key `arxiv2024`: "While traditional quantum sensing is often focused on estimating a single parameter with maximum precision, distributed quantum sensing seeks to estimate some function of multiple parameters that are only locally accessible for each party involved."
  3. `% AGENT-SYNTHESIS:` marker present once in `review.tex`, confirmed absent from the compiled PDF's extracted text layer via `pypdf`.
  4. Conduct section renders exactly one "Search Scope" subsection (crossref 1, arxiv 2, pubmed 2), no duplicate or bare-number subsections, no empty Terminology Alternatives heading (there were no alternatives for this query).
  5. `methodology.md` follows the new narrative structure with this run's real data (real pool counts, real trust tiers, theme `quant-ph`), with exactly one `[AGENT:` placeholder, confined to Limitations.
  6. Integrity check section reports "Status: pass."
- The smoke run surfaced a real defect the plan and research did not anticipate (see Deviations): PubMed's snippet is metadata, not abstract prose. Fixed by extending the existing `source_text_is_metadata` guard to PubMed (commit `4220363`), the same mechanism Task 1 built for CrossRef.
- A follow-on refactor attempt during the same interrupted execution (adding a `_view_bibliography` helper to retain metadata-flagged hits in the final rendered bibliography) was discarded rather than completed, see Deviations for why it would have been a regression.

### Files Modified
- `server/science_engines.py` -- marks PubMed's `_pubmed_hit` snippet as metadata (same guard as CrossRef).

### Known Issue Outcomes
- None.

### Deviations
- See the round-level `deviations` array in this file's frontmatter for the PubMed-metadata finding and the discarded follow-on refactor. Both are recorded there, not duplicated here.

### Verification
- `python3 -m pytest server/tests/ -q`: 224 passed, 1 skipped (unchanged from Task 6, this task added no new test-suite changes beyond the PubMed one-line guard already covered by Task 1's existing CrossRef-pattern tests).
- Real CLI run, exit implied by `status: ok` JSON output, no exception.
- Direct PDF text-layer extraction via `pypdf.PdfReader` confirmed `AGENT-SYNTHESIS` absent from rendered text.
