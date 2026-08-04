---
phase: 3
plan: 1
title: Split enforce.py and search_core.py along their internal seams
status: complete
completed: 2026-08-04
tasks_completed: 4
tasks_total: 4
commit_hashes:
  - e4b4fcdc77513eada30227fe0c1310b7f54a15d1
  - 606b89b977e978a994691814bf37816a5dbdb0ce
  - 40707cdfef5cf8eae4db1c4f6a4a6180a5e892ba
deviations:
  - "DEV-01 resolved-by-amendment (R01 Amendment): The baseline and final suite reported 316 passed and 1 skipped, rather than the plan estimate of 327 passed, with no test failures."
  - >-
    DEV-02: Existing hook size findings required behavior-preserving formatting and test-stub extraction in touched files.
    R01 reverted the three call-site reflows.
    It also extracted _validate_platform_args in server/cli.py and _build_search_request in server/search_context.py.
    PY002 blocks the verbatim inline bodies at about 34 and 29 lines.
    The moved lines are byte-identical to 48187ba, and behavior is unchanged.
    The contract holds under the R02 amendment of MH-02 and MH-05.
    That amendment authorizes exactly these two seams.
    This is resolved-by-amendment.
    See the Amendment (R02) note in 03-01-PLAN.md.
  - "DEV-03 and UNDECL-01 resolved-by-amendment (R01 Amendment): Direct callers outside the listed task files were rewired in server/tests/test_deep_context_search.py, benchmark/deep_context_bench.py, server/tests/test_cli.py, and server/tests/test_search_api.py."
  - "Final verification created no cleanup commit because Ruff was clean and Pyright matched the baseline."
pre_existing_issues:
  - '{"test":"pyright server/","file":"server/fetch.py","error":"Argument of type str | int cannot be assigned to parameter value of type str in _forbidden_address"}'
  - '{"test":"pyright server/","file":"server/fetch.py","error":"HTTPRedirectHandler.redirect_request override returns object instead of Request | None"}'
  - '{"test":"pyright server/","file":"server/tests/test_fetch.py","error":"None cannot be assigned to redirect_request req parameter of type Request"}'
  - '{"test":"pyright server/","file":"server/tests/test_fetch.py","error":"None cannot be assigned to redirect_request fp parameter of type IO[bytes]"}'
  - '{"test":"pyright server/","file":"server/tests/test_fetch.py","error":"dict cannot be assigned to redirect_request headers parameter of type HTTPMessage"}'
  - '{"test":"pyright server/","file":"server/tests/test_rag_host_memory.py","error":"Server has no known ref_dir attribute"}'
  - '{"test":"pyright server/","file":"server/tests/test_rag_host_memory.py","error":"ModuleType has no known _IDLE_SECS attribute"}'
  - '{"test":"pyright server/","file":"server/tests/test_rag_host_memory.py","error":"ModuleType has no known _IDLE_POLL_SECS attribute"}'
  - '{"test":"pyright server/","file":"server/tests/test_search_api.py","error":"object has no known append attribute at the existing fixture calls site"}'
ac_results:
  - criterion: "Full test suite stays green after every task commit"
    verdict: pass
    evidence: "pytest tests/ server/tests/: 316 passed, 1 skipped after each task"
  - criterion: "CLI command names, flags, and JSON output shapes do not change"
    verdict: partial
    evidence: >-
      git diff 48187ba server/cli.py shows imports, dispatch prefixes, the _validate_platform_args extraction hunk,
      and the R01-restored multi-line call formatting. Under amended MH-02, the diff contains exactly the authorized elements.
  - criterion: "No compatibility re-exports create circular imports"
    verdict: pass
    evidence: "grep found no search_deep or search_context import in server/search_core.py and no trust import in server/enforce.py"
  - criterion: "_try_fetch remains defined in server/search_core.py"
    verdict: pass
    evidence: "server/search_core.py:394"
  - criterion: "Moved functions preserve signatures and behavior"
    verdict: pass
    evidence: >-
      AST comparison matched all trust and deep symbols and all context symbols except the required search_core._try_fetch qualification.
      _gather_pool delegates request construction to _build_search_request, whose moved lines match 48187ba line for line under amended MH-05.
  - criterion: "Ruff and Pyright introduce no findings beyond baseline"
    verdict: pass
    evidence: "Ruff clean, Pyright has the same 9 baseline findings"
  - criterion: "server/trust.py provides trust scoring, RRF ranking, and quality gating"
    verdict: pass
    evidence: "server/trust.py contains rrf_rank and is 332 lines"
  - criterion: "server/search_deep.py provides deep_research"
    verdict: pass
    evidence: "server/search_deep.py contains deep_research and is 222 lines"
  - criterion: "server/search_context.py provides deep_context_aware_search"
    verdict: pass
    evidence: "server/search_context.py contains deep_context_aware_search and is 262 lines"
  - criterion: "server/enforce.py keeps query rewriting and retry mutation"
    verdict: pass
    evidence: "server/enforce.py is 454 lines and defines enforce_query"
  - criterion: "server/search_core.py keeps shared orchestration and _try_fetch"
    verdict: pass
    evidence: "server/search_core.py is 481 lines and defines _try_fetch"
  - criterion: "Deep tests mirror search_deep.py"
    verdict: pass
    evidence: "tests/test_search_deep.py imports search_deep"
  - criterion: "Context tests mirror search_context.py"
    verdict: pass
    evidence: "tests/test_search_context.py imports search_context"
  - criterion: "trust.py imports _STOPWORDS from enforce.py in one direction"
    verdict: pass
    evidence: "server/trust.py imports enforce._STOPWORDS and server/enforce.py does not import trust"
  - criterion: "search_core.py calls trust ranking, gating, and tiering"
    verdict: pass
    evidence: "search_core runtime call sites use trust.rrf_rank, trust.quality_gate, and trust.source_tier"
  - criterion: "CLI dispatches deep research through search_deep"
    verdict: pass
    evidence: "server/cli.py calls search_deep.deep_research"
  - criterion: "CLI dispatches context search through search_context"
    verdict: pass
    evidence: "server/cli.py calls search_context.deep_context_aware_search"
  - criterion: "search_deep imports shared search_core functions without a back-import"
    verdict: pass
    evidence: "server/search_deep.py imports shared helpers from search_core and search_core.py has no search_deep reference"
  - criterion: "search_context uses search_core._try_fetch so fetch monkeypatches retain scope"
    verdict: pass
    evidence: "server/search_context.py calls search_core._try_fetch and server/search_core.py defines _try_fetch"
---

## What Was Built

- Extracted trust scoring and ranking into `server/trust.py`, deep research into `server/search_deep.py`, and context search into `server/search_context.py`.
- Rewired runtime callers, tests, and the context benchmark while preserving the existing CLI surface and search behavior.
- Completed four green-to-green task gates. Ruff is clean, and Pyright matches the captured baseline.

## Files Modified

- `server/enforce.py`, `server/trust.py`: separated query enforcement from trust and ranking logic.
- `server/search_core.py`, `server/search_deep.py`, `server/search_context.py`: split orchestration clusters along their existing seams.
- `server/cli.py`: dispatched deep and context commands through their extracted modules.
- `tests/test_search_core.py`, `tests/test_search_deep.py`, `tests/test_search_context.py`: mirrored the new module boundaries.
- `tests/test_enforce.py`, `server/tests/test_trust.py`, `server/tests/test_cli.py`, `server/tests/test_search_api.py`, `server/tests/test_deep_context_search.py`: updated extracted-module callers and coverage.
- `benchmark/deep_context_bench.py`: updated the context benchmark caller.

## QA Remediation

- QA FAIL for plan 03-01 prompted commit `d14058e4d6489b71754325a3a0df40d6345a4513`.
- Files changed: `benchmark/deep_context_bench.py` and `server/tests/test_cli.py`.
- Rebound the benchmark call to imported `search_context` so its first run no longer raises `NameError`. Replaced the test lambda's `or` return trick with named `fake_quick`, preserving captured arguments and the empty-results return.
