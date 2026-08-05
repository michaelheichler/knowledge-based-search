---
phase: 5
round: 1
title: "Analysis section quote redesign, attribution integrity gate, Conduct/methodology cleanup, REQ-20 rewording"
type: remediation
status: partial
completed: 2026-08-05
tasks_completed: 5
tasks_total: 7
commit_hashes:
  - c7cf4dafd3db555daedd3c4eb682fc31696e5082
  - 2baec3b
  - a107e7e
  - 18a0c81
files_modified:
  - server/science_engines.py
  - server/review_synthesis.py
  - server/review_latex.py
  - server/tests/test_review_synthesis.py
deviations: []
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
