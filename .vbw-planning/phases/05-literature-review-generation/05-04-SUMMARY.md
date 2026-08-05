---
phase: 5
plan: 4
title: Orchestrator, CLI flag, methodology guide and setup docs
status: complete
completed: 2026-08-05
tasks_completed: 4
tasks_total: 4
commit_hashes:
  - c5329ef
  - 2a6077a
  - 6c05278
  - e3211dc
deviations:
  - "The original manual-smoke completion claim was unsupported while ART-01 and INT-01 were live. A post-remediation direct CLI run exited 0 and published reviews/quantum-sensing-20260805-153239/review.tex, review.bib, review.pdf, and methodology.md with 3 pages."
pre_existing_issues: []
ac_results:
  - criterion: "REQ-22 outputs use <cwd>/reviews/<topic-slug>-<YYYYMMDD-HHMMSS>/ with review.tex, review.bib, review.pdf and methodology.md"
    verdict: pass
    evidence: "c5329ef, 6c05278, server/tests/test_review.py"
  - criterion: "REQ-20 integrity checks run before compile, remove flagged claims, recheck, and fail at the claim floor"
    verdict: pass
    evidence: "c5329ef, server/tests/test_review.py"
  - criterion: "REQ-21 methodology.md documents Rapid Review method, Snyder phases, source pools, integrity checks and page handling"
    verdict: pass
    evidence: "6c05278, server/review.py, server/tests/test_review.py"
  - criterion: "REQ-05 and REQ-14 literature-review wiring requires scientific mode"
    verdict: pass
    evidence: "2a6077a, server/cli.py, server/tests/test_cli.py"
  - criterion: "REQ-09 review generation stays within the existing scientific search and library deepening paths"
    verdict: pass
    evidence: "2a6077a, c5329ef, server/search_core.py"
  - criterion: "Compile and integrity failures use the existing structured CLI error response"
    verdict: pass
    evidence: "c5329ef, 2a6077a, server/tests/test_review.py, server/tests/test_cli.py"
  - criterion: "README documents the full TeX prerequisite and MiKTeX on-demand network risk"
    verdict: pass
    evidence: "e3211dc, README.md"
  - criterion: "Full pytest suite remains green"
    verdict: pass
    evidence: "389 passed, 0 failed, 1 skipped"
  - criterion: "server/review.py exposes generate_review and the methodology writer"
    verdict: pass
    evidence: "c5329ef, 6c05278, server/review.py"
  - criterion: "CLI exposes literature-review and dispatches to review generation"
    verdict: pass
    evidence: "2a6077a, server/cli.py, server/search_core.py"
  - criterion: "Review tests cover orchestration, fail-closed behavior, guide output and real compilation"
    verdict: pass
    evidence: "c5329ef, 6c05278, e3211dc, server/tests/test_review.py"
  - criterion: "CLI review path calls generate_review through search_core"
    verdict: pass
    evidence: "2a6077a, server/search_core.py"
  - criterion: "review.py uses review_synthesis for model, claims, drop, shrink and grow"
    verdict: pass
    evidence: "c5329ef, server/review.py"
  - criterion: "review.py uses review_integrity.check_claims before compilation"
    verdict: pass
    evidence: "c5329ef, server/review.py"
  - criterion: "review.py uses review_latex.compile_review with synthesis callbacks"
    verdict: pass
    evidence: "c5329ef, server/review.py"
  - criterion: "Manual smoke publishes all four review artifacts under the invocation cwd with an in-range PDF"
    verdict: pass
    evidence: >-
      Direct cli.main smoke invocation exited 0 at
      reviews/quantum-sensing-20260805-153239. It published review.tex,
      review.bib, review.pdf, and methodology.md. pypdf counted 3 pages.
---
Fail-closed scientific review generation now archives a cited PDF, LaTeX source, bibliography and run-specific methodology guide under the invocation directory.

## What Was Built

- Added the orchestrator, CLI flag validation and dispatch threading, with real integrity-gated review compilation.
- Added a data-backed methodology guide with Rapid Review classification, Snyder phases, source-pool counts, themes, live integrity thresholds and page-bound outcome.
- Added an offline end-to-end compile check and documented output layout plus full TeX and MiKTeX setup requirements.
- REQ-18 remains v2: the rag_host daemon pattern is reusable, but no OLMo/mlx-lm generation wiring exists.
- Grounding: d03-wp-semantics-of-the-language and d04-termination-and-euclid briefs read. Postcondition: the integrity loop passes only a clean model to compilation or returns the final IntegrityFloor flag report. Invariant: each iteration's model contains only claims not flagged by completed checks. Variant: claim count strictly decreases on every flagged iteration.

## Files Modified

- `server/review.py` - orchestrates gated compilation and atomically writes methodology.md.
- `server/cli.py` - accepts and validates --literature-review.
- `server/search_core.py` - dispatches ranked scientific hits to review generation.
- `server/tests/test_review.py` - covers orchestration, guide output and real offline compilation.
- `server/tests/test_cli.py` - covers flag validation, threading and rendering.
- `README.md` - documents review invocation, artifacts and TeX prerequisites.
