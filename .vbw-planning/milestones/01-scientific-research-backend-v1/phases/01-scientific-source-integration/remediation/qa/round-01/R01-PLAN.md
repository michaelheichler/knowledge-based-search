---
phase: 1
round: 1
plan: R01
title: Phase 01 QA remediation, suite green, test-style repair, engines split
type: remediation
autonomous: true
effort_override: balanced
skills_used: [python-testing-patterns, repo-hygiene:keeping-files-small, refactoring-patterns, agent-skills:planning-and-task-breakdown]
files_modified:
  - tests/test_engines.py
  - tests/conftest.py
  - tests/test_enforce.py
  - tests/test_search_core.py
  - server/tests/test_search_api.py
  - server/engines.py
  - server/engine_pacing.py
  - server/library_engine.py
  - server/direct_engines.py
  - server/cli.py
  - server/enforce.py
  - server/rag_host.py
  - .vbw-planning/phases/01-scientific-source-integration/01-01-PLAN.md
  - .vbw-planning/phases/01-scientific-source-integration/01-04-PLAN.md
forbidden_commands: []
fail_classifications:
  - {id: "DEV-01", type: "plan-amendment", rationale: "The scientific adapter split into server/science_engines.py is a valid improvement. The module is cohesive and tested, and it keeps engines.py smaller. Amend the plan file contract to include science_engines.py.", source_plan: "01-01-PLAN.md"}
  - {id: "DEV-02", type: "code-fix", rationale: "Full-suite verification was blocked by nine stale baseline tests, not by unverifiable work. Tasks 1 and 2 repair those tests so the suite gate can pass."}
  - {id: "DEV-03", type: "code-fix", rationale: "Same root cause as DEV-02. The retained failures are stale provider expectations and missing test-state isolation, all fixable in this round."}
  - {id: "DEV-04", type: "code-fix", rationale: "CONV-010 requires unittest.TestCase style in the tests/ root. Wrapping the five new bare functions in a TestCase class with pytest.MonkeyPatch context managers is a direct fix."}
  - {id: "DEV-05", type: "code-fix", rationale: "engines.py at 992 lines has two clear seams, the library MCP client and the pacing state. Task 4 extracts both into new modules with re-exports as a mechanical behavior-preserving split."}
  - {id: "DEV-06", type: "code-fix", rationale: "Same retained-failure set as DEV-02 and DEV-03. Resolved by the same test repairs in Tasks 1 and 2."}
  - {id: "DEV-07", type: "plan-amendment", rationale: "The deep-context test module belongs under server/tests/ per CONV-010, which reserves that root for server-internal pytest suites. The plan text named tests/test_deep_context_search.py in error. Correct the plan path to server/tests/test_deep_context_search.py.", source_plan: "01-04-PLAN.md"}
  - {id: "DEV-08", type: "code-fix", rationale: "Same retained-failure set as DEV-02, DEV-03 and DEV-06. Resolved by Tasks 1 and 2, then proven by the full-suite gate in Task 5."}
known_issues_input:
  - '{"test":"SearchOutcomeTests.test_all_provider_failures_raise_network_error","file":"tests/test_engines.py","error":"AllProvidersFailed was not raised"}'
  - '{"test":"SearchOutcomeTests.test_all_provider_failures_raise_network_error","file":"tests/test_engines.py","error":"AllProvidersFailed was not raised because config omitted default-enabled mwmbl and wikipedia, and shared provider cache/state can count a prior result as success"}'
  - '{"test":"SearchOutcomeTests.test_blocked_duckduckgo_is_a_network_failure","file":"tests/test_engines.py","error":"AllProvidersFailed was not raised because config omitted default-enabled mwmbl and wikipedia, and shared provider cache/state bypassed the patched DuckDuckGo call"}'
  - '{"test":"SearchOutcomeTests.test_blocked_duckduckgo_is_a_network_failure","file":"tests/test_engines.py","error":"AllProvidersFailed was not raised for the blocked DuckDuckGo case"}'
  - '{"test":"SearchOutcomeTests.test_disabled_engines_are_never_fallback_targets","file":"tests/test_engines.py","error":"Unexpected mwmbl and wikipedia hits came from default-enabled free providers and shared cache state"}'
  - '{"test":"SearchOutcomeTests.test_disabled_engines_are_never_fallback_targets","file":"tests/test_engines.py","error":"Unexpected mwmbl and wikipedia hits were returned"}'
  - '{"test":"SearchOutcomeTests.test_malformed_provider_shape_completes_future_with_error","file":"tests/test_engines.py","error":"AllProvidersFailed was not raised"}'
  - '{"test":"SearchOutcomeTests.test_malformed_provider_shape_completes_future_with_error","file":"tests/test_engines.py","error":"AllProvidersFailed was not raised because default-enabled providers completed with successful empty results"}'
  - '{"test":"SearchOutcomeTests.test_merged_json_keeps_provider_provenance","file":"tests/test_engines.py","error":"Merged provenance came from cached mwmbl and wikipedia hits instead of the patched SearXNG and DuckDuckGo providers"}'
  - '{"test":"SearchOutcomeTests.test_merged_json_keeps_provider_provenance","file":"tests/test_engines.py","error":"Merged provenance came from mwmbl and wikipedia instead of the expected providers"}'
  - '{"test":"SearchOutcomeTests.test_partial_provider_failure_is_structured","file":"tests/test_engines.py","error":"SearXNG outcome was ok instead of error"}'
  - '{"test":"SearchOutcomeTests.test_partial_provider_failure_is_structured","file":"tests/test_engines.py","error":"SearXNG outcome was ok instead of error because shared provider cache/state bypassed the patched failure"}'
  - '{"test":"SearchOutcomeTests.test_search_defaults_to_searxng_and_duckduckgo_only","file":"tests/test_engines.py","error":"Default-enabled mwmbl and wikipedia produced extra hits"}'
  - '{"test":"SearchOutcomeTests.test_search_defaults_to_searxng_and_duckduckgo_only","file":"tests/test_engines.py","error":"Default-enabled mwmbl and wikipedia providers produced extra hits beyond the test legacy expected set"}'
  - '{"test":"SearchOutcomeTests.test_search_defaults_to_searxng_and_duckduckgo_only","file":"tests/test_engines.py","error":"Default-enabled mwmbl and wikipedia providers produced extra hits beyond the test''s legacy expected set"}'
  - '{"test":"SearchOutcomeTests.test_search_wires_opted_in_direct_engines","file":"tests/test_engines.py","error":"Default-enabled mwmbl produced an extra hit"}'
  - '{"test":"SearchOutcomeTests.test_search_wires_opted_in_direct_engines","file":"tests/test_engines.py","error":"Default-enabled mwmbl produced an extra hit beyond the test legacy expected set"}'
  - '{"test":"SearchOutcomeTests.test_search_wires_opted_in_direct_engines","file":"tests/test_engines.py","error":"Default-enabled mwmbl produced an extra hit beyond the test''s legacy expected set"}'
  - '{"test":"pyright and rag_host warnings","file":"server/engines.py:420, server/cli.py, server/enforce.py:332, tests/test_search_core.py, server/rag_host.py:392","error":"All reproduce identically on the pre-phase baseline 78c07c4"}'
  - '{"test":"test_all_provider_failures_raise_network_error","file":"tests/test_engines.py","error":"AllProvidersFailed not raised. On baseline"}'
  - '{"test":"test_blocked_duckduckgo_is_a_network_failure","file":"tests/test_engines.py","error":"AllProvidersFailed not raised. On baseline"}'
  - '{"test":"test_disabled_engines_are_never_fallback_targets","file":"tests/test_engines.py","error":"Default Mwmbl and Wikipedia hits returned. On baseline"}'
  - '{"test":"test_malformed_provider_shape_completes_future_with_error","file":"tests/test_engines.py","error":"AllProvidersFailed not raised. On baseline"}'
  - '{"test":"test_merged_json_keeps_provider_provenance","file":"tests/test_engines.py","error":"Provenance from default providers. On baseline"}'
  - '{"test":"test_partial_provider_failure_is_structured","file":"tests/test_engines.py","error":"SearXNG outcome ok instead of error. On baseline"}'
  - '{"test":"test_quality_gate_tags_tiers_and_diversity","file":"tests/test_enforce.py","error":"At index 1, confidence was primary but the test expects standard"}'
  - '{"test":"test_quality_gate_tags_tiers_and_diversity","file":"tests/test_enforce.py","error":"Reuters is tagged primary while the test expects standard, indicating a pre-existing trust-tier expectation mismatch"}'
  - '{"test":"test_quality_gate_tags_tiers_and_diversity","file":"tests/test_enforce.py","error":"Reuters primary, test expects standard. On baseline"}'
  - '{"test":"test_result_reference_survives_separate_cli_processes","file":"server/tests/test_search_api.py","error":"CLI subprocess cannot import bm25s, ModuleNotFoundError: No module named bm25s"}'
  - '{"test":"test_search_defaults_to_searxng_and_duckduckgo_only","file":"tests/test_engines.py","error":"Defaults differ from legacy expectation. On baseline"}'
  - '{"test":"test_search_wires_opted_in_direct_engines","file":"tests/test_engines.py","error":"Default Mwmbl added an extra hit. On baseline"}'
known_issue_resolutions:
  - '{"test":"SearchOutcomeTests.test_all_provider_failures_raise_network_error","file":"tests/test_engines.py","error":"AllProvidersFailed was not raised","disposition":"resolved","rationale":"Task 1 pins explicit provider config without default free providers and resets shared engines state per test"}'
  - '{"test":"SearchOutcomeTests.test_all_provider_failures_raise_network_error","file":"tests/test_engines.py","error":"AllProvidersFailed was not raised because config omitted default-enabled mwmbl and wikipedia, and shared provider cache/state can count a prior result as success","disposition":"resolved","rationale":"Task 1 pins explicit provider config and resets the short query cache and engine state per test"}'
  - '{"test":"SearchOutcomeTests.test_blocked_duckduckgo_is_a_network_failure","file":"tests/test_engines.py","error":"AllProvidersFailed was not raised because config omitted default-enabled mwmbl and wikipedia, and shared provider cache/state bypassed the patched DuckDuckGo call","disposition":"resolved","rationale":"Task 1 pins explicit provider config and resets shared state so the patched DuckDuckGo failure is exercised"}'
  - '{"test":"SearchOutcomeTests.test_blocked_duckduckgo_is_a_network_failure","file":"tests/test_engines.py","error":"AllProvidersFailed was not raised for the blocked DuckDuckGo case","disposition":"resolved","rationale":"Task 1 pins explicit provider config and resets shared state so the blocked path raises again"}'
  - '{"test":"SearchOutcomeTests.test_disabled_engines_are_never_fallback_targets","file":"tests/test_engines.py","error":"Unexpected mwmbl and wikipedia hits came from default-enabled free providers and shared cache state","disposition":"resolved","rationale":"Task 1 disables the default free providers explicitly in the test config and clears cache state per test"}'
  - '{"test":"SearchOutcomeTests.test_disabled_engines_are_never_fallback_targets","file":"tests/test_engines.py","error":"Unexpected mwmbl and wikipedia hits were returned","disposition":"resolved","rationale":"Task 1 disables the default free providers explicitly in the test config and clears cache state per test"}'
  - '{"test":"SearchOutcomeTests.test_malformed_provider_shape_completes_future_with_error","file":"tests/test_engines.py","error":"AllProvidersFailed was not raised","disposition":"resolved","rationale":"Task 1 pins explicit provider config so only the malformed provider participates and the error path raises"}'
  - '{"test":"SearchOutcomeTests.test_malformed_provider_shape_completes_future_with_error","file":"tests/test_engines.py","error":"AllProvidersFailed was not raised because default-enabled providers completed with successful empty results","disposition":"resolved","rationale":"Task 1 pins explicit provider config so default-enabled providers cannot mask the malformed provider error"}'
  - '{"test":"SearchOutcomeTests.test_merged_json_keeps_provider_provenance","file":"tests/test_engines.py","error":"Merged provenance came from cached mwmbl and wikipedia hits instead of the patched SearXNG and DuckDuckGo providers","disposition":"resolved","rationale":"Task 1 clears cached provider results per test and pins the provider set to the patched providers"}'
  - '{"test":"SearchOutcomeTests.test_merged_json_keeps_provider_provenance","file":"tests/test_engines.py","error":"Merged provenance came from mwmbl and wikipedia instead of the expected providers","disposition":"resolved","rationale":"Task 1 clears cached provider results per test and pins the provider set to the patched providers"}'
  - '{"test":"SearchOutcomeTests.test_partial_provider_failure_is_structured","file":"tests/test_engines.py","error":"SearXNG outcome was ok instead of error","disposition":"resolved","rationale":"Task 1 resets shared provider cache and state so the patched SearXNG failure reaches the outcome map"}'
  - '{"test":"SearchOutcomeTests.test_partial_provider_failure_is_structured","file":"tests/test_engines.py","error":"SearXNG outcome was ok instead of error because shared provider cache/state bypassed the patched failure","disposition":"resolved","rationale":"Task 1 resets shared provider cache and state so the patched SearXNG failure reaches the outcome map"}'
  - '{"test":"SearchOutcomeTests.test_search_defaults_to_searxng_and_duckduckgo_only","file":"tests/test_engines.py","error":"Default-enabled mwmbl and wikipedia produced extra hits","disposition":"resolved","rationale":"Task 1 updates the stale legacy expectation to the intended default provider set shipped in 78c07c4"}'
  - '{"test":"SearchOutcomeTests.test_search_defaults_to_searxng_and_duckduckgo_only","file":"tests/test_engines.py","error":"Default-enabled mwmbl and wikipedia providers produced extra hits beyond the test legacy expected set","disposition":"resolved","rationale":"Task 1 updates the stale legacy expectation to the intended default provider set shipped in 78c07c4"}'
  - '{"test":"SearchOutcomeTests.test_search_defaults_to_searxng_and_duckduckgo_only","file":"tests/test_engines.py","error":"Default-enabled mwmbl and wikipedia providers produced extra hits beyond the test''s legacy expected set","disposition":"resolved","rationale":"Task 1 updates the stale legacy expectation to the intended default provider set shipped in 78c07c4"}'
  - '{"test":"SearchOutcomeTests.test_search_wires_opted_in_direct_engines","file":"tests/test_engines.py","error":"Default-enabled mwmbl produced an extra hit","disposition":"resolved","rationale":"Task 1 updates the expected wired-engine set to include the intended default-enabled free providers"}'
  - '{"test":"SearchOutcomeTests.test_search_wires_opted_in_direct_engines","file":"tests/test_engines.py","error":"Default-enabled mwmbl produced an extra hit beyond the test legacy expected set","disposition":"resolved","rationale":"Task 1 updates the expected wired-engine set to include the intended default-enabled free providers"}'
  - '{"test":"SearchOutcomeTests.test_search_wires_opted_in_direct_engines","file":"tests/test_engines.py","error":"Default-enabled mwmbl produced an extra hit beyond the test''s legacy expected set","disposition":"resolved","rationale":"Task 1 updates the expected wired-engine set to include the intended default-enabled free providers"}'
  - '{"test":"pyright and rag_host warnings","file":"server/engines.py:420, server/cli.py, server/enforce.py:332, tests/test_search_core.py, server/rag_host.py:392","error":"All reproduce identically on the pre-phase baseline 78c07c4","disposition":"resolved","rationale":"Task 5 clears the listed warnings at the named locations after the Task 4 split relocates the engines.py site"}'
  - '{"test":"test_all_provider_failures_raise_network_error","file":"tests/test_engines.py","error":"AllProvidersFailed not raised. On baseline","disposition":"resolved","rationale":"Duplicate of the SearchOutcomeTests entry, fixed by the Task 1 config pinning and state reset"}'
  - '{"test":"test_blocked_duckduckgo_is_a_network_failure","file":"tests/test_engines.py","error":"AllProvidersFailed not raised. On baseline","disposition":"resolved","rationale":"Duplicate of the SearchOutcomeTests entry, fixed by the Task 1 config pinning and state reset"}'
  - '{"test":"test_disabled_engines_are_never_fallback_targets","file":"tests/test_engines.py","error":"Default Mwmbl and Wikipedia hits returned. On baseline","disposition":"resolved","rationale":"Duplicate of the SearchOutcomeTests entry, fixed by the Task 1 explicit provider config"}'
  - '{"test":"test_malformed_provider_shape_completes_future_with_error","file":"tests/test_engines.py","error":"AllProvidersFailed not raised. On baseline","disposition":"resolved","rationale":"Duplicate of the SearchOutcomeTests entry, fixed by the Task 1 config pinning"}'
  - '{"test":"test_merged_json_keeps_provider_provenance","file":"tests/test_engines.py","error":"Provenance from default providers. On baseline","disposition":"resolved","rationale":"Duplicate of the SearchOutcomeTests entry, fixed by the Task 1 cache reset and provider pinning"}'
  - '{"test":"test_partial_provider_failure_is_structured","file":"tests/test_engines.py","error":"SearXNG outcome ok instead of error. On baseline","disposition":"resolved","rationale":"Duplicate of the SearchOutcomeTests entry, fixed by the Task 1 state reset"}'
  - '{"test":"test_quality_gate_tags_tiers_and_diversity","file":"tests/test_enforce.py","error":"At index 1, confidence was primary but the test expects standard","disposition":"resolved","rationale":"Task 2 updates the tier expectation to match the shipped trust scoring that promotes Reuters to primary"}'
  - '{"test":"test_quality_gate_tags_tiers_and_diversity","file":"tests/test_enforce.py","error":"Reuters is tagged primary while the test expects standard, indicating a pre-existing trust-tier expectation mismatch","disposition":"resolved","rationale":"Task 2 updates the tier expectation to match the shipped trust scoring that promotes Reuters to primary"}'
  - '{"test":"test_quality_gate_tags_tiers_and_diversity","file":"tests/test_enforce.py","error":"Reuters primary, test expects standard. On baseline","disposition":"resolved","rationale":"Task 2 updates the tier expectation to match the shipped trust scoring that promotes Reuters to primary"}'
  - '{"test":"test_result_reference_survives_separate_cli_processes","file":"server/tests/test_search_api.py","error":"CLI subprocess cannot import bm25s, ModuleNotFoundError: No module named bm25s","disposition":"resolved","rationale":"Task 2 makes the CLI subprocess inherit the active interpreter environment, with a clean skip only when bm25s is absent from the running interpreter"}'
  - '{"test":"test_search_defaults_to_searxng_and_duckduckgo_only","file":"tests/test_engines.py","error":"Defaults differ from legacy expectation. On baseline","disposition":"resolved","rationale":"Duplicate of the SearchOutcomeTests entry, fixed by the Task 1 expectation update"}'
  - '{"test":"test_search_wires_opted_in_direct_engines","file":"tests/test_engines.py","error":"Default Mwmbl added an extra hit. On baseline","disposition":"resolved","rationale":"Duplicate of the SearchOutcomeTests entry, fixed by the Task 1 expectation update"}'
must_haves:
  truths:
    - "pytest tests/ server/tests/ passes with zero failures at the end of the round"
    - "server/engines.py is at or below 600 lines and each extracted module is below 400 lines, with no behavior change"
    - "The five new tests in tests/test_search_core.py live inside a unittest.TestCase class per CONV-010"
    - "SearchOutcomeTests hold under explicit provider config with per-test state reset, with no reliance on cross-test cache leakage"
    - "DEV-01 and DEV-07 are resolved by changed original plan files that record the actual approach and rationale"
  artifacts:
    - {path: "tests/test_engines.py", provides: "repaired SearchOutcomeTests", contains: "AllProvidersFailed"}
    - {path: "tests/test_search_core.py", provides: "CONV-010 compliant new tests", contains: "unittest.TestCase"}
    - {path: "server/library_engine.py", provides: "extracted library MCP client", contains: "def library"}
    - {path: "server/engine_pacing.py", provides: "extracted pacing, cooldown and cache state", contains: "_MIN_INTERVAL"}
    - {path: "server/direct_engines.py", provides: "extracted direct provider adapters and HTML parsers", contains: "def duckduckgo"}
    - {path: ".vbw-planning/phases/01-scientific-source-integration/01-01-PLAN.md", provides: "DEV-01 source-plan amendment", contains: "DEV-01"}
    - {path: ".vbw-planning/phases/01-scientific-source-integration/01-04-PLAN.md", provides: "DEV-07 source-plan amendment", contains: "server/tests/test_deep_context_search.py"}
  key_links:
    - {from: "server/engines.py", to: "server/library_engine.py", via: "import and re-export so existing callers and tests keep working"}
    - {from: "server/engines.py", to: "server/engine_pacing.py", via: "import and re-export of pacing and cooldown state"}
    - {from: "server/engines.py", to: "server/direct_engines.py", via: "import and re-export of direct provider adapters and parsers"}
    - {from: "tests/conftest.py", to: "server/engines.py", via: "autouse fixture resetting shared provider cache and engine state"}
    - {from: "R01 Task 1", to: "01-01-PLAN.md and 01-04-PLAN.md", via: "one atomic commit records both amendments and verifies both source plans changed"}
---
<objective>
Close the eight Phase 01 verification FAILs and every carried known issue. Task 1 amends both original phase plans with the actual approach and rationale, explicitly marks DEV-01 and DEV-07 resolved by amendment, and repairs the stale provider suite with state isolation. One commit converts the new search_core tests to the tests/ root unittest convention. One commit repairs trust-tier expectations and the CLI subprocess environment. One commit splits the oversized engines.py along its three natural seams. One commit clears the listed baseline pyright warnings. Full-suite verification must use the active interpreter environment and may not use a dependency-related skip as a shortcut to green.
</objective>
<context>
@/Users/michael/dev/skills/knowledge-based-search/.vbw-planning/phases/01-scientific-source-integration/01-VERIFICATION.md
@/Users/michael/dev/skills/knowledge-based-search/.vbw-planning/phases/01-scientific-source-integration/remediation/qa/round-01/R01-KNOWN-ISSUES.json
@/Users/michael/dev/skills/knowledge-based-search/.vbw-planning/conventions.json
@/Users/michael/dev/skills/knowledge-based-search/.claude/skills/python-testing-patterns/SKILL.md

Root-cause summary from research. Commit 78c07c4 added default-enabled free providers (mwmbl, wikipedia) and a shared short query cache with persistent cooldown state. Nine tests written against the old defaults now fail in two ways. Default providers satisfy searches that the tests expect to fail entirely. Shared module state also leaks between tests, so patched failures are bypassed by cached results. The verification confirmed all nine reproduce on the pre-phase baseline. These are stale tests and missing isolation, not product defects. The intended product behavior (free defaults on) stands. Tests move to it.

Database note: no database is involved in this round. All verification commands are read-only pytest and pyright runs.
</context>
<tasks>
<task type="auto">
  <name>Amend original plans and repair SearchOutcomeTests with explicit config and per-test state reset</name>
  <files>
    tests/test_engines.py
    tests/conftest.py
    .vbw-planning/phases/01-scientific-source-integration/01-01-PLAN.md
    .vbw-planning/phases/01-scientific-source-integration/01-04-PLAN.md
  </files>
  <action>
Use one atomic commit boundary for this task. First update 01-01-PLAN.md with the actual science_engines.py extraction approach, its cohesive adapter rationale, and its compatibility/import contract. Add an explicit DEV-01 record stating resolved by amendment. Update 01-04-PLAN.md to use server/tests/test_deep_context_search.py, record the CONV-010 path rationale, and add an explicit DEV-07 record stating resolved by amendment. Verify both original plan files changed. Do not claim frontmatter classification alone resolves either deviation. Then fix the failing SearchOutcomeTests in tests/test_engines.py: all_provider_failures, blocked_duckduckgo, disabled_engines_fallback, malformed_provider_shape, merged_json_provenance, partial_provider_failure, search_defaults, and wires_opted_in. Reset shared engines module state before each test, including the short query cache, engine_state, and persisted cooldown or block state introduced in 4db91fd and 78c07c4. Pass explicit provider config in each failure-path test that disables the default-enabled free providers (mwmbl, wikipedia). Only the patched providers may participate in those tests. For test_search_defaults_to_searxng_and_duckduckgo_only and test_search_wires_opted_in_direct_engines, update expected provider and hit sets to the current intentional default set. Keep unittest.TestCase style per CONV-010. Do not add sleeps or network calls.
  </action>
  <verify>
Run the repository diff whitespace check and inspect 01-01-PLAN.md and 01-04-PLAN.md to confirm both source plans changed and contain the DEV-01 and DEV-07 amendment records. Run python -m pytest tests/test_engines.py -q && python -m pytest tests/test_engines.py -q through the active interpreter environment to prove order independence. Both runs are green.
  </verify>
  <done>
Both original plans contain actual approach, rationale, and resolved-by-amendment records. All SearchOutcomeTests pass twice with isolated state and no network call. One commit: fix(tests): amend phase plans and repair provider outcome tests
  </done>
</task>
<task type="auto">
  <name>Fix trust-tier expectation and CLI subprocess environment</name>
  <files>
    tests/test_enforce.py
    server/tests/test_search_api.py
  </files>
  <action>
In tests/test_enforce.py update test_quality_gate_tags_tiers_and_diversity. Reuters is now a primary tier under the shipped trust scoring (a6a48e9). Update the expected confidence at the failing index to primary. If the diversity assertion needs a genuinely standard-tier source, swap that fixture entry to a domain trust.json leaves untiered. Do not weaken the assertion. In server/tests/test_search_api.py fix test_result_reference_survives_separate_cli_processes. The _run_cli helper at line 303 launches bin/kbs with a passed env that loses the active virtualenv. Build the subprocess env from os.environ overlaid with test-specific variables, preserving PATH, VIRTUAL_ENV, and declared dependencies, and invoke the CLI through the active interpreter environment. Keep the existing pytest.skip path for genuine network unavailability. A dependency-related skip is allowed only when bm25s is absent from the active interpreter itself, never when the subprocess merely failed to inherit that environment.
  </action>
  <verify>
python -m pytest tests/test_enforce.py server/tests/test_search_api.py -q with no failures. The subprocess test passes or skips only for a stated genuine environmental reason, never errors because the subprocess lost the active interpreter dependency environment.
  </verify>
  <done>
Both files green. One commit: fix(tests): align trust-tier expectation and CLI subprocess environment
  </done>
</task>
<task type="auto">
  <name>Convert the five new search_core tests to unittest style</name>
  <files>
    tests/test_search_core.py
  </files>
  <action>
Per CONV-010 the tests/ root uses unittest.TestCase style. Wrap the five phase-added bare functions in a single new unittest.TestCase class. The five are test_scientific_resolves_providers at line 107, test_library_hits_merge_and_outcomes at 136, test_library_error_is_structured_outcome at 195, test_platform_library_only at 223, and the phase-added test near 593. Replace the monkeypatch fixture parameter with pytest.MonkeyPatch context managers inside each method. Preserve every assertion exactly. Do not restyle the pre-existing bare functions in this file. DEV-04 covers only the five new tests. Restyling the rest is out of scope for this round.
  </action>
  <verify>
python -m pytest tests/test_search_core.py -q green, and grep confirms the five test names are methods of a unittest.TestCase subclass.
  </verify>
  <done>
Five tests run as TestCase methods with unchanged assertions. One commit: refactor(tests): move new search_core tests to unittest style per CONV-010
  </done>
</task>
<task type="auto">
  <name>Split engines.py along the library, pacing and direct-provider seams</name>
  <files>
    server/engines.py
    server/library_engine.py
    server/engine_pacing.py
    server/direct_engines.py
  </files>
  <action>
Task 4 performed a mechanical, behavior-preserving split of the historical 902-line `server/engines.py` host. Extract three cohesive seams.

First, move the library MCP client into a new `server/library_engine.py`. That covers library() plus its handshake, SSE and Bearer helpers. Second, move the pacing, short query cache, cooldown and persistent block state into a new `server/engine_pacing.py`. That state includes _MIN_INTERVAL and the 429 to ProviderBlocked mapping.

Third, move the direct provider adapter and parser cluster into a new `server/direct_engines.py`. Extract searxng, mwmbl, wikipedia, tavily, duckduckgo, google, bing, startpage and mojeek together with their provider-specific parser functions. Keep shared result, date, HTML and URL helpers in engines.py. Use a small lazy compatibility bridge for those helpers so the new module stays cohesive without a circular import or dense rewrite.

Re-export every moved public name from server/engines.py, including the direct provider functions, so existing imports and tests keep working unchanged. The direct-provider extraction must remove at least 303 physical lines from engines.py without dense rewriting. No logic edits in this task beyond module extraction and import wiring. If circular imports force a helper to stay, keep it and note the reason in the summary rather than restructuring further.

R05 marks the old Tavily host path as historical.

The current Tavily implementation is in `server/direct_engines.py`.
  </action>
  <verify>
python -m pytest tests/ server/tests/ -q green. wc -l server/engines.py server/library_engine.py server/engine_pacing.py server/direct_engines.py confirms server/engines.py is at or below 600 and all three extracted modules are below 400. LSP diagnostics show no new import errors.
  </verify>
  <done>
Suite green, size ceilings met, the direct-provider seam removes at least 303 lines, and no caller changed. One commit: refactor(engines): extract library client, pacing state and direct providers into modules
  </done>
</task>
<task type="auto">
  <name>Clear the listed baseline pyright warnings</name>
  <files>
    server/engines.py
    server/direct_engines.py
    server/cli.py
    server/enforce.py
    server/rag_host.py
    tests/test_search_core.py
  </files>
  <action>
Fix the carried pyright and rag_host warnings at the exact registry-listed locations. The historical Tavily warning reference was `server/engines.py:420`. Task 4 moved Tavily to `server/direct_engines.py` before Task 5 fixed it there. The remaining `server/engines.py` reference covers the host file and is unrelated to Tavily. Find any moved warning by its warning text. Fix each with a real type correction, narrowing, annotation, or guard, not a blanket ignore. If any single warning proves structurally unfixable without behavior change, leave it and state why in the summary. Report it as a discovered issue instead of suppressing it.

R05 amendment for MH-09. The live Tavily contract is `server/direct_engines.py`. The former `server/engines.py` path is historical evidence only. The moved-to trace appears above. This amendment corrects the contract. The completed implementation is unchanged.
  </action>
  <verify>
pyright over the five files reports none of the previously listed warnings. python -m pytest tests/ server/tests/ -q stays green.
  </verify>
  <done>
Named warning sites clean or explicitly reported as unfixable with rationale. One commit: fix(types): clear baseline pyright warnings at registry-listed sites
  </done>
</task>
</tasks>
<verification>
1. Run python -m pytest tests/ server/tests/ -q && python -m pytest tests/ server/tests/ -q with the active interpreter. Both runs exit 0 with zero failures.
2. Confirm the immediate repeat proves state isolation across ordering.
3. wc -l server/engines.py server/library_engine.py server/engine_pacing.py server/direct_engines.py confirms the 600-line host ceiling and 400-line ceiling for all three extracted modules.
4. grep -n "unittest.TestCase" tests/test_search_core.py shows the new class containing the five converted tests.
5. pyright on the five Task 5 files shows none of the registry-listed warnings.
</verification>
<success_criteria>
- Every DEV FAIL from 01-VERIFICATION.md is closed: DEV-02, DEV-03, DEV-04, DEV-05, DEV-06 and DEV-08 by code, DEV-01 and DEV-07 by changed original plan files that record approach, rationale, and resolved-by-amendment status.
- All 31 carried known issues carry a resolved disposition backed by a passing test or a clean pyright site.
- Full suite green twice in a row with no skipped-to-green shortcuts, with subprocess tests inheriting the active interpreter environment and no new network-touching tests.
- The engines.py split lands as its own commit with no behavior change mixed in.
</success_criteria>
<known_issue_workflow>
- Always include `known_issues_input` and `known_issue_resolutions` in frontmatter. If there are no carried known issues, set both to empty arrays: `known_issues_input: []` and `known_issue_resolutions: []`.
- Copy every carried known issue from the remediation input backlog into `known_issues_input` using the canonical `{test,file,error}` shape.
- Add a matching `known_issue_resolutions` entry for every carried known issue. Use `resolved` when this round fixes it, `accepted-process-exception` when QA should treat it as a verified non-blocking carryover for this phase, and `unresolved` only when the issue is intentionally carried into the next round.
- Do not omit a carried known issue from these arrays. The deterministic gate treats missing coverage as a failed remediation round.
</known_issue_workflow>
<output>
R01-SUMMARY.md
</output>
