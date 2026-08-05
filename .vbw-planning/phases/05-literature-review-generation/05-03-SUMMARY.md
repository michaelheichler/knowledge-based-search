---
phase: 5
plan: 3
title: Review synthesis engine (content model from ranked hits)
status: complete
completed: 2026-08-05
tasks_completed: 3
tasks_total: 3
commit_hashes:
  - d3e8132
  - 696a952
  - d540cdf
task_statuses:
  - task: Theme grouping and bibliography construction
    status: complete
    commit: d3e8132
  - task: Claim construction with attribution
    status: complete
    commit: 696a952
  - task: Model assembly plus shrink and grow contract
    status: complete
    commit: d540cdf
deviations: []
pre_existing_issues: []
ac_results:
  - criterion: "REQ-07: synthesis groups findings by theme rather than source order"
    verdict: pass
    evidence: "group_themes and test_group_themes_caps_without_singleton_groups"
  - criterion: "REQ-08: claims retain source attribution and bibliography entries remain cited"
    verdict: pass
    evidence: "build_model, drop_flagged, and shrink/grow tests"
  - criterion: "REQ-06: the model contains design, conduct, analysis, and write-up phases"
    verdict: pass
    evidence: "test_build_model_contains_four_phases_and_source_pool_counts"
  - criterion: "REQ-23: generated claims avoid denylisted filler openers"
    verdict: pass
    evidence: "FILLER_DENYLIST and test_generated_claims_do_not_start_with_filler_phrases"
  - criterion: "REQ-19: charts and formulas use only retrieved source data"
    verdict: pass
    evidence: "formulas_from_hits, chart_from_bibliography, and test_formula_and_chart_candidates_require_source_data"
  - criterion: "Claims remain deterministic, transformed, and source-text attached"
    verdict: pass
    evidence: "build_claims and test_claims_keep_attribution_and_use_one_real_citation"
  - criterion: "Shrink, grow, and flag removal operate on whole claims and preserve citation coverage"
    verdict: pass
    evidence: "shrink, grow, claims_for_integrity, drop_flagged, and task three tests"
  - criterion: "REQ-09: synthesis uses no network path beyond allowlisted library deepening"
    verdict: pass
    evidence: "review_synthesis source boundary and library-only deepening path"
  - criterion: "Full test suite passes"
    verdict: pass
    evidence: "python3 -m pytest tests/ server/tests/ -q: 376 passed, 1 skipped"
  - criterion: "Synthesis module remains below the 400-line cap"
    verdict: pass
    evidence: "wc -l server/review_synthesis.py: 394"
---

The deterministic literature synthesis engine now assembles attributed, theme-grouped review models and supports safe page-budget edits.

## What Was Built

- Added thematic grouping, stable bibliography keys, source-backed claims, formula detection, and publication-year chart data.
- Added Snyder phase model assembly, source-pool conduct metadata, minimum-claim errors, integrity projection, and orphan-safe shrink, grow, and flag removal.
- Validated the focused tests, full suite, Ruff, Pyright, and the module size cap.
- Grounding: d03-wp-semantics-of-the-language and d04-termination-and-euclid briefs read. Postcondition: every emitted claim keeps one resolvable citation key, source_id, and source_text from its supplying hit, with copied runs below LONGEST_BLOCK_WORDS. Invariant: processed theme-ordered hits retain matching bibliography entries. Variant: remaining flattened hits decrease.

## Files Modified

- `server/review_synthesis.py` - added model assembly and claim-preserving page-budget callbacks.
- `server/tests/test_review_synthesis.py` - added model, floor, bibliography, integrity, and callback coverage.
