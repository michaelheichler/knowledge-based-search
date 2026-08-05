---
phase: 5
round: 2
title: Close the two round-01 deviation FAILs, grounding bullets and catch-tuple alignment
type: remediation
status: complete
completed: 2026-08-05
tasks_completed: 2
tasks_total: 2
commit_hashes:
  - 27224485ba3cf841d7fd841262c4a884b56e5d6e
  - b2348510eaa43c1d46a7cde75270fe01097b6152
  - 053d3d8bdd541a6362e7ede05b27f748df990667
files_modified:
  - .vbw-planning/phases/05-literature-review-generation/remediation/qa/round-01/R01-SUMMARY.md
  - server/review_synthesis.py
deviations:
  - >-
    R02's prior deviation and its correction to 393 were wrong.
    The 393 figure came from python3 -m pytest tests/ server/tests/ -q, which
    excludes the 10 benchmark/quality/ tests. The repo-root python3 -m pytest -q
    reports 403 passed, 0 failed, and 1 skipped.
known_issues_input: []
known_issue_resolutions: []
known_issue_outcomes: []
pre_existing_issues: []
verification:
  grounding_bullets: >-
    R01-SUMMARY.md contains exactly two Grounding bullets. One is under Task 3.
    One is under Task 4. Task 6 reports 403 passed, 0 failed, and 1 skipped.
  catch_tuple_alignment: >-
    Both catch sites use the same exception tuple. It includes IndexError,
    KeyError, OSError, RuntimeError, TypeError, and ValueError.
  full_suite: >-
    Pytest passed. Result: 403 passed, 0 failed, and 1 skipped. It ran 40
    subtests.
  static_checks: >-
    Ruff passed on review_synthesis.py. Ruff passed on server/. Pyright passed
    on review_synthesis.py. No findings were reported.
  line_cap: "wc -l server/review_synthesis.py: 399"
---

Closed both round-01 deviation FAILs and recorded the reproducible verification count.

## Task 1: Add grounding bullets and correct the observed suite count

### What Was Built
- Added Grounding bullets for MH-14 claim attribution and INT-01 reporting-frame integrity.
- Restored Task 6 to the accurate repo-root result of 403 passed, 0 failed, and 1 skipped.

### Files Modified
- `.vbw-planning/phases/05-literature-review-generation/remediation/qa/round-01/R01-SUMMARY.md` - added the two grounding records and corrected the suite count.

### Known Issue Outcomes
None.

### Deviations
- Retracted the prior deviation and its claim that 393 was correct. The 393 figure came from python3 -m pytest tests/ server/tests/ -q, which excludes the 10 benchmark/quality/ tests. The repo-root python3 -m pytest -q reports 403 passed, 0 failed, and 1 skipped.

## Task 2: Align the _source_text catch tuple

### What Was Built
- Added `IndexError` to `_source_text` so its catch tuple matches `_document_tool`.

### Files Modified
- `server/review_synthesis.py` - widened the catch tuple by one entry. The file remains 399 lines.

### Known Issue Outcomes
None.

### Deviations
No deviations.
