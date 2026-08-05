---
phase: 3
round: 2
plan: R02
title: Amend the 03-01 verbatim-move contract to authorize the PY002-forced extractions and correct the overclaiming record
type: remediation
autonomous: true
effort_override: balanced
skills_used: [refactoring-patterns]
files_modified: [.vbw-planning/phases/03-module-size-refactor/03-01-PLAN.md, .vbw-planning/phases/03-module-size-refactor/03-01-SUMMARY.md]
forbidden_commands: []
fail_classifications:
  - {id: "ORIG-MH-02", type: "plan-amendment", rationale: "MH-02 demands an import-and-prefix-only cli.py diff against 48187ba, but restoring _dispatch_query's verbatim body puts it at about 34 lines and PY002 blocks any function over 25 lines (craftsman/4.2.0/packs/python/hooks/python-validator.sh:62). The pre-round-01 state passed PY002 only through a 160-char reflow that violated the same contract from the other direction, so no reachable state satisfies MH-02 as written. QA confirmed the _validate_platform_args extraction is behavior-identical (AP-03) with byte-identical moved lines. The user decided to keep the code and amend the contract, so the fix is rewriting MH-02 to authorize the named PY002-forced extraction while still constraining everything else in the diff.", source_plan: "03-01-PLAN.md"}
  - {id: "ORIG-MH-05", type: "plan-amendment", rationale: "MH-05 requires every moved function to keep its exact body and limits the phase to Extract Class moves. Verbatim restoration of _gather_pool lands at about 29 lines, over the PY002 ceiling, and the only PY002-passing alternative to extraction was the 131 and 173 char reflows that MH-05 also forbids. The contract is unsatisfiable, not the code wrong: QA verified the 13 moved lines in _build_search_request are line-for-line identical to 48187ba:server/search_core.py:732-744 and behavior is unchanged on every path (AP-03). Per the user decision the fix is amending MH-05 to authorize the two named Extract Function seams where PY002 forces them, keeping moved-line text and behavior as the binding guarantee.", source_plan: "03-01-PLAN.md"}
  - {id: "R01-DEV-01", type: "process-exception", rationale: "R01-PLAN.md's context block instructed Dev to stop and report a blocker if a hook still fired after the restore. Dev extracted instead, and the orchestrator explicitly authorized that extraction mid-execution, overriding the plan's own escape hatch. The breach is historical fact: no code edit can un-happen it (the resulting code is correct and the user decided to keep it), and no phase-03 plan amendment changes what occurred during round 01. The R01-SUMMARY deviation entry and the orchestrator's on-record acceptance of responsibility are the complete and only possible resolution. Non-fixable by artifact change, so process-exception."}
  - {id: "R01-ACC-01", type: "plan-amendment", rationale: "The R01 amendment note at 03-01-PLAN.md:66 states the verbatim-move must_haves hold at HEAD. That sentence is false: MH-05's exact-body condition does not hold because _gather_pool's body at HEAD delegates to _build_search_request, and the note never mentions either extraction. The artifact check fails on the artifact's own text, so the fix is rewriting the note to state the extractions plainly and to claim only what is true, namely that moved lines are byte-identical and behavior is unchanged under the amended contract.", source_plan: "03-01-PLAN.md"}
  - {id: "R-MH-01", type: "plan-amendment", rationale: "R01 truth 1 restates ORIG-MH-02's import-and-prefix-only condition and fails for the identical reason: the diff carries the _validate_platform_args hunk that PY002 forced. The multi-line restoration half already passes (server/cli.py:350-360 matches 48187ba one argument per line). The condition inherits the unsatisfiable source contract, so it is resolved by the same MH-02 amendment in 03-01-PLAN.md that ratifies the named extraction. R01 is a closed round and its plan file is not edited retroactively.", source_plan: "03-01-PLAN.md"}
  - {id: "R-MH-02", type: "plan-amendment", rationale: "R01 truth 2 requires _gather_pool to call _resolve_sources and _SearchRequest in their exact pre-move shape. The line-width half passes (zero lines over 100 chars). The shape half fails because both calls now live in _build_search_request at server/search_context.py:202-217, where QA verified they match 48187ba:server/search_core.py:732-744 line for line. Same inherited unsatisfiability as its source condition ORIG-MH-05, resolved by the MH-05 amendment authorizing that seam.", source_plan: "03-01-PLAN.md"}
known_issues_input: []
known_issue_resolutions: []
must_haves:
  truths:
    - "03-01-PLAN.md's MH-02 and MH-05 truths name _validate_platform_args and _build_search_request as PY002-forced Extract Function seams and record the PY002 conflict as the reason. They still require moved lines byte-identical to their 48187ba source with behavior, error messages, and call ordering unchanged. QA can therefore fail any future edit that alters moved-line text or behavior"
    - "03-01-PLAN.md no longer claims the verbatim-move must_haves hold at HEAD in their original form. Its R02 amendment note states both extractions plainly, with the resolved-by-amendment marker for ORIG-MH-02, ORIG-MH-05, R-MH-01, R-MH-02, and R01-ACC-01"
    - "03-01-SUMMARY.md's deviation and evidence records name both extracted helpers instead of describing the R01 fix as a pure reflow revert"
    - "git diff 07ec48e94002f808f594b5c6857ea1878ca7fab7 HEAD touches no file outside .vbw-planning/, confirming this round is documentation-only"
    - "No hook-suppression token of any kind is added to any file"
    - "The known-issues registry stays empty: this plan carries no known_issues_input and no resolutions"
  artifacts:
    - {path: ".vbw-planning/phases/03-module-size-refactor/03-01-PLAN.md", provides: "amended MH-02 and MH-05 contract authorizing the PY002-forced seams", contains: "_build_search_request"}
    - {path: ".vbw-planning/phases/03-module-size-refactor/03-01-SUMMARY.md", provides: "deviation record naming both extractions plainly", contains: "_validate_platform_args"}
  key_links:
    - {from: ".vbw-planning/phases/03-module-size-refactor/03-01-PLAN.md", to: ".vbw-planning/phases/03-module-size-refactor/03-01-SUMMARY.md", via: "matching accounts of the two R01 extractions, both naming _validate_platform_args and _build_search_request"}
---
<objective>
Close the six remaining FAILs from R01-VERIFICATION.md without touching code. The root cause is a contract conflict, not a code defect: MH-05 requires verbatim moved bodies and Extract Class moves only, while the repo's PY002 hook (craftsman/4.2.0/packs/python/hooks/python-validator.sh:62) blocks any function over 25 lines. Verbatim restoration puts _dispatch_query at about 34 lines and _gather_pool at about 29, so the hook blocks it. The pre-round-01 state passed PY002 only because three call sites had been reflowed into 131, 160, and 173 character lines, which violated the same verbatim contract from the other direction. No reachable state satisfies both must_haves as written.

The user has decided the route and it is not up for reconsideration: amend the contract, keep the code. Round 01's two extractions, _validate_platform_args (server/cli.py:324-334) and _build_search_request (server/search_context.py:202-217), stay. QA already verified them behavior-identical on every path with byte-identical moved lines (R01-VERIFICATION AP-03). The suite sits at 316 passed 1 skipped, ruff is clean, and pyright is at the 9-finding baseline. This round therefore does three things. It amends MH-02 and MH-05 in 03-01-PLAN.md to state what the phase actually requires and can satisfy. It corrects the two overclaiming sentences QA flagged (03-01-PLAN.md:66 and 03-01-SUMMARY.md:15). It gates on the round producing zero code changes and zero suppression tokens. R01-DEV-01 is the one FAIL no artifact edit can fix. The escape-hatch bypass happened and was orchestrator-authorized mid-execution, so it is carried as a process-exception with that record as its resolution.
</objective>
<context>
@.vbw-planning/phases/03-module-size-refactor/remediation/qa/round-01/R01-VERIFICATION.md
@.vbw-planning/phases/03-module-size-refactor/remediation/qa/round-01/R01-PLAN.md
@.vbw-planning/phases/03-module-size-refactor/remediation/qa/round-01/R01-SUMMARY.md
@.vbw-planning/phases/03-module-size-refactor/03-01-PLAN.md
@.vbw-planning/phases/03-module-size-refactor/03-01-SUMMARY.md
@/Users/michael/.claude/skills/refactoring-patterns/SKILL.md

The amended contract must stay falsifiable. Do not replace MH-05 with a vague behavior-preservation statement. The enforceable guarantee is threefold and QA must be able to check each part mechanically. First, every line moved out of 48187ba is byte-identical to its source apart from module-prefix changes. That is verifiable by comparing _build_search_request against 48187ba:server/search_core.py:732-744 and the restored dispatch call against 48187ba:server/cli.py:343-353. Second, the only structural departures from Extract Class are the two named Extract Function seams, so any third extraction or any body edit inside a moved function fails the amended contract. Third, behavior is unchanged: same error types, message strings, and call ordering, backed by the green 316-test suite.

Hard constraints for this round: do not revert either extraction, do not add any hook-suppression token, do not edit any file outside .vbw-planning/, and do not reintroduce known-issue registry entries.

Amendment (R03): originally read: "Planning artifacts are untracked, so this round produces edits only, no commits."
The two files this round edited, 03-01-PLAN.md and 03-01-SUMMARY.md, are tracked.
Tasks 1 and 2 each produced a commit, 5ee90e0 and 5c99261.
They followed the project's one-commit-per-task rule.
Those commits carry only .vbw-planning paths.
They broke no must_have truth.
R02-VERIFICATION.md check R02-DEV-01 says the false premise was due for correction before execution.
It should not have been overridden during execution.
R02-DEV-01 is resolved-by-amendment by this note.

If any check in task 3 fails, the fix belongs in task 1 or 2.
</context>
<tasks>
<task type="auto">
  <name>Amend MH-02 and MH-05 in 03-01-PLAN.md and rewrite the amendment note</name>
  <files>
    .vbw-planning/phases/03-module-size-refactor/03-01-PLAN.md
  </files>
  <action>
Rewrite must_haves truth 2 (MH-02) to: git diff against 48187ba on server/cli.py shows only import lines, module-prefix changes on existing call sites, and the R01 extraction of _validate_platform_args from _dispatch_query. The extraction's moved lines are byte-identical to their 48187ba source, and its BadArgsError paths keep their original trigger conditions, ordering, and exact message strings. No CLI command name, flag, or JSON output shape changes.

Rewrite must_haves truth 5 (MH-05) to: every moved line keeps its exact text apart from module-prefix changes, and every moved function keeps its exact signature. The phase is Extract Class moves plus exactly two Extract Function seams that PY002's 25-line ceiling forces where verbatim inline restoration is impossible: _validate_platform_args in server/cli.py and _build_search_request in server/search_context.py. The latter's body matches 48187ba:server/search_core.py:732-744 line for line. Any further extraction, any edit to moved-line text, or any behavior change (error types, message strings, call ordering, output shapes) violates this contract.

Replace the sentence at line 66 ("R01 restored the three reflowed call sites. The verbatim-move must_haves hold at HEAD.") with an Amendment (R02) note recording three things in order. First, the PY002 conflict: cite craftsman/4.2.0/packs/python/hooks/python-validator.sh:62 and the approximate 34-line and 29-line verbatim sizes of _dispatch_query and _gather_pool. Record that the pre-round-01 state passed PY002 only via 131, 160, and 173 character reflows that violated the verbatim contract from the other direction, so no state satisfied MH-02 and MH-05 as originally written. Second, what R01 did: it restored the three reflowed call sites to their 48187ba shapes and additionally extracted _validate_platform_args and _build_search_request as PY002-forced seams with byte-identical moved lines and verified-unchanged behavior. Third, the resolution: by user decision the contract is amended to authorize those two named seams, and ORIG-MH-02, ORIG-MH-05, R-MH-01, R-MH-02, and R01-ACC-01 are resolved-by-amendment. R01-DEV-01 is carried as a process-exception because the R01 escape-hatch bypass was orchestrator-authorized mid-execution and cannot be undone by any artifact edit.
  </action>
  <verify>
grep -c "_build_search_request" 03-01-PLAN.md returns at least 2 (the MH-05 truth and the amendment note). grep -c "_validate_platform_args" returns at least 2. grep "resolved-by-amendment" matches a line naming ORIG-MH-02 and ORIG-MH-05. grep "must_haves hold at HEAD" returns nothing. grep "python-validator.sh" matches the amendment note. The MH-05 truth still contains a falsifiable clause forbidding further extraction and moved-line edits (grep for "Any further extraction").
  </verify>
  <done>
03-01-PLAN.md's MH-02 and MH-05 authorize exactly the two named seams with the PY002 conflict as recorded cause, the false hold-at-HEAD claim is gone, and the amendment note marks the five plan-amendment FAILs resolved-by-amendment while binding future edits to a checkable byte-identity and behavior guarantee.
  </done>
</task>
<task type="auto">
  <name>Correct the overclaiming deviation record in 03-01-SUMMARY.md</name>
  <files>
    .vbw-planning/phases/03-module-size-refactor/03-01-SUMMARY.md
  </files>
  <action>
Rewrite deviation 2 (line 15), which currently says R01 reverted the three call-site reflows so the verbatim-move contract now holds. Replace it with a statement of what actually happened. R01 reverted the three reflows and also extracted _validate_platform_args (server/cli.py) and _build_search_request (server/search_context.py) because PY002 blocks the verbatim inline bodies at about 34 and 29 lines. The moved lines are byte-identical to 48187ba and behavior is unchanged. The contract holds under the R02 amendment of MH-02 and MH-05, which authorizes exactly these two seams (resolved-by-amendment, see the Amendment (R02) note in 03-01-PLAN.md).

Update the ac_results evidence for the partial "CLI command names, flags, and JSON output shapes do not change" criterion (line 34). The evidence must name the _validate_platform_args extraction hunk alongside the imports, prefixes, and restored multi-line formatting, and state the verdict rationale under the amended MH-02: the diff contains exactly the authorized elements. Update the "Moved functions preserve signatures and behavior" evidence (line 43) to note that _gather_pool delegates its request construction to _build_search_request, whose moved lines match 48187ba line for line, per the amended MH-05. Touch nothing else in the file: no changes to pre_existing_issues, commit_hashes, or the remaining deviations.
  </action>
  <verify>
grep -c "_validate_platform_args" 03-01-SUMMARY.md returns at least 2 (deviation 2 and the ac_results evidence). grep "_build_search_request" matches deviation 2. grep "verbatim-move contract now holds" returns nothing. grep "Amendment (R02)" matches deviation 2, tying the summary to the plan's amendment note. pre_existing_issues still lists exactly 9 entries.
  </verify>
  <done>
03-01-SUMMARY.md states both extractions plainly, its deviation record points at the R02 amendment as the resolution, its evidence lines no longer omit the extraction hunks, and nothing outside the named lines changed.
  </done>
</task>
<task type="auto">
  <name>Gate: documentation-only round with a clear registry and no suppressions</name>
  <files>
    .vbw-planning/phases/03-module-size-refactor/03-01-PLAN.md
    .vbw-planning/phases/03-module-size-refactor/03-01-SUMMARY.md
  </files>
  <action>
Run the full gate in one pass at HEAD and record outputs for R02-SUMMARY.md. Fix nothing here: any failure belongs to task 1 or 2.

(1) git diff --name-only 07ec48e94002f808f594b5c6857ea1878ca7fab7 HEAD returns no path outside .vbw-planning/, and git status shows no modified tracked file under server/, tests/, or benchmark/. The round changed documentation only. (2) grep -rnE "craftsman[-]ignore" server/ tests/ benchmark/ returns nothing, and neither amended planning file introduces a suppression instruction. (3) The two amended files agree: both name _validate_platform_args and _build_search_request, and the summary's Amendment (R02) pointer resolves to the note present in the plan. (4) The behavioral baseline still holds untouched: pytest tests/ server/tests/ reports 316 passed, 1 skipped, confirming the round did not disturb the code it promises not to touch. (5) This plan's frontmatter carries known_issues_input: [] and known_issue_resolutions: [], so the deterministic registry gate sees a clear registry with no new entries.
  </action>
  <verify>
All five checks pass in a single fresh run at HEAD with command outputs captured for the R02 SUMMARY.
  </verify>
  <done>
The round is demonstrably documentation-only, the extractions stand unreverted, no suppression token exists, plan and summary tell the same amended story, the suite is green at the unchanged 07ec48e code state, and the known-issues registry remains empty.
  </done>
</task>
</tasks>
<verification>
1. 03-01-PLAN.md's MH-02 and MH-05 truths name _validate_platform_args and _build_search_request and cite PY002 as the forcing constraint. They retain falsifiable clauses (byte-identical moved lines, no further extraction, unchanged behavior) that a future body edit would fail.
2. 03-01-PLAN.md contains no claim that the verbatim-move must_haves hold at HEAD in their original form. Its Amendment (R02) note marks ORIG-MH-02, ORIG-MH-05, R-MH-01, R-MH-02, and R01-ACC-01 resolved-by-amendment, with R01-DEV-01 recorded as a process-exception.
3. 03-01-SUMMARY.md deviation 2 and the two updated ac_results evidence lines state both extractions plainly and reference the R02 amendment.
4. git diff 07ec48e HEAD touches no file outside .vbw-planning/ and grep -rnE "craftsman[-]ignore" server/ tests/ benchmark/ returns nothing.
5. pytest tests/ server/tests/ reports 316 passed, 1 skipped at HEAD.
6. R02-PLAN.md frontmatter carries all six fail_classifications and empty known_issues_input and known_issue_resolutions arrays.
</verification>
<success_criteria>
- The 03-01 contract is satisfiable and satisfied at HEAD: the amended MH-02 and MH-05 describe exactly the code QA verified, and QA can re-derive PASS for all six former FAILs from the amended text plus the unchanged code.
- The record stops overclaiming: plan and summary name both extractions, agree with each other, and tie every resolution to either the R02 amendment or the R01-DEV-01 process-exception.
- The round adds no code change, no suppression token, and no known-issue registry entry.
</success_criteria>
<known_issue_workflow>
- Always include `known_issues_input` and `known_issue_resolutions` in frontmatter. If there are no carried known issues, set both to empty arrays: `known_issues_input: []` and `known_issue_resolutions: []`.
- Copy every carried known issue from the remediation input backlog into `known_issues_input` using the canonical `{test,file,error}` shape.
- Add a matching `known_issue_resolutions` entry for every carried known issue. Use `resolved` when this round fixes it, `accepted-process-exception` when QA should treat it as a verified non-blocking carryover for this phase, and `unresolved` only when the issue is intentionally carried into the next round.
- Do not omit a carried known issue from these arrays. The deterministic gate treats missing coverage as a failed remediation round.
</known_issue_workflow>
<output>
R02-SUMMARY.md
</output>
