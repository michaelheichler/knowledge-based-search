---
phase: 3
round: 5
plan: R05
title: Record the FAIL-02 resolution in 03-01-PLAN.md as a plan amendment
type: remediation
autonomous: true
effort_override: fast
skills_used: []
files_modified: [.vbw-planning/phases/03-module-size-refactor/03-01-PLAN.md]
forbidden_commands: []
fail_classifications:
  - {id: "FAIL-02", type: "plan-amendment", rationale: "FAIL-02 is the one failing row in R03-VERIFICATION.md. Its substance was settled in round 04: R02-SUMMARY.md had mislabeled a compliant verification gate (no edits specified, so no commit expected) as a deviation, and round 04 corrected both mislabeled locations in place with the originals preserved as quotations. R04-VERIFICATION.md verified that correction at PASS with zero FAILs. What remains is the phase-level record. A code-fix classification is impossible because closing this FAIL requires no executable, config, or test change and this round must not make one. The correct closure is amending the phase's original plan, 03-01-PLAN.md, with a short factual note marking FAIL-02 resolved-by-amendment and citing the round 04 correction and its verification. Round 04's gate rejection was schema conformance, not substance: it declared the historical name R02-DEV-02 instead of the source verification row ID and named a remediation summary as source_plan. This entry uses the row ID as written in R03-VERIFICATION.md and names the original plan.", source_plan: "03-01-PLAN.md"}
known_issues_input: []
known_issue_resolutions: []
must_haves:
  truths:
    - "The context block of 03-01-PLAN.md carries an Amendment (R05) note that marks FAIL-02, carried across rounds as R02-DEV-02, resolved-by-amendment, states that the mislabeled entry recorded compliant gate behavior as a deviation, and cites R02-SUMMARY.md's Amendment (R04) correction with commit a3e932b and the PASS result in R04-VERIFICATION.md"
    - "Nothing else in 03-01-PLAN.md changes: frontmatter, tasks, verification, success criteria, and every earlier amendment note stay byte-identical"
    - "No round 01 through round 04 artifact is edited and no file outside .vbw-planning/ is modified by this round"
    - "No hook-suppression token of any kind is added to any file"
    - "The known-issues registry stays empty: this plan carries known_issues_input: [] and known_issue_resolutions: []"
  artifacts:
    - {path: ".vbw-planning/phases/03-module-size-refactor/03-01-PLAN.md", provides: "phase-level record that FAIL-02 is resolved-by-amendment, closing the loop the round 04 gate rejection left open", contains: "Amendment (R05)"}
  key_links:
    - {from: ".vbw-planning/phases/03-module-size-refactor/03-01-PLAN.md", to: ".vbw-planning/phases/03-module-size-refactor/remediation/qa/round-02/R02-SUMMARY.md", via: "the Amendment (R05) note cites the Amendment (R04) correction and its commit a3e932b"}
---
<objective>
Close the last open item from R03-VERIFICATION.md by recording its resolution where the gate requires it: in the phase's original plan. The code has been correct and verified since round 01. The substantive fix for FAIL-02 shipped in round 04 and passed QA at 15 of 16 with zero FAILs. The deterministic gate still returned REMEDIATION_REQUIRED. R04-PLAN.md declared the classification under the historical name R02-DEV-02 instead of the source verification row ID FAIL-02. It also named a remediation summary as source_plan where the gate requires an original phase plan.

This round adds one short amendment note to 03-01-PLAN.md, the phase's only original plan, marking FAIL-02 resolved-by-amendment and citing the already verified round 04 correction. It re-argues nothing, reverts nothing round 04 did, touches no code, and adds no suppression marker. The classification above uses the row ID exactly as it appears in R03-VERIFICATION.md. It names 03-01-PLAN.md as source_plan, and this round's recorded paths cover that file.

This plan states only what must be true for the work to be correct. It makes no prediction about commit counts, tracking state, or diff contents beyond the constraints its checks require. The gate task specifies verification only, so its absent commit is compliant execution. Neither this plan nor the R05 summary frames it as a deviation.
</objective>
<context>
@.vbw-planning/phases/03-module-size-refactor/remediation/qa/round-03/R03-VERIFICATION.md
@.vbw-planning/phases/03-module-size-refactor/remediation/qa/round-04/R04-VERIFICATION.md
@.vbw-planning/phases/03-module-size-refactor/remediation/qa/round-02/R02-SUMMARY.md
@.vbw-planning/phases/03-module-size-refactor/03-01-PLAN.md

Hard constraints. Edit only 03-01-PLAN.md. Within it, add only the one amendment note task 1 specifies.
Do not edit any round 01 through round 04 artifact. Do not edit 03-01-SUMMARY.md. Do not edit any file outside .vbw-planning/.
Do not add any hook-suppression token. Do not reintroduce known-issue registry entries.
In the R05 summary, declare a deviation only for a genuine departure from a task's action text. The gate task executing with no commit is not one.
</context>
<tasks>
<task type="auto">
  <name>Add the Amendment (R05) note to 03-01-PLAN.md</name>
  <files>
    .vbw-planning/phases/03-module-size-refactor/03-01-PLAN.md
  </files>
  <action>
In the context block of 03-01-PLAN.md, immediately after the last line of the Amendment (R02) block ("No artifact edit can undo it."), insert a blank line followed by this note, verbatim:

Amendment (R05): R03-VERIFICATION.md FAIL-02, carried across rounds as R02-DEV-02, is resolved-by-amendment. R02-SUMMARY.md had recorded as a deviation that its task 3 produced no commit. That task was a verification gate whose action said fix nothing here and specified no edits, so the absent commit was the specified behavior, not a departure. Round 04 corrected both mislabeled locations in R02-SUMMARY.md in place, preserving each original as a quotation introduced with "originally read:" (commit a3e932b). R04-VERIFICATION.md verified that correction as the in-place non-erasing fix R03-VERIFICATION.md named, result PASS with zero FAILs.

Change nothing else in the file. Every other line, including the frontmatter, the earlier amendment notes, all tasks, verification, and success criteria, stays byte-identical.

Commit as one atomic docs commit (type docs, scope planning).
  </action>
  <verify>
grep -c "Amendment (R05)" 03-01-PLAN.md returns 1. grep "resolved-by-amendment" matches a line naming FAIL-02.
The note sits in the context block after the Amendment (R02) block. It cites a3e932b and R04-VERIFICATION.md.
git diff for this task names no file other than 03-01-PLAN.md. The diff shows only the inserted note and its preceding blank line.
  </verify>
  <done>
03-01-PLAN.md carries the phase-level record that FAIL-02 is closed. The substance is cited from round 04 rather than re-argued. No other line in the file changed.
  </done>
</task>
<task type="auto">
  <name>Gate: single-file round with untouched code and a clear registry</name>
  <files>
    .vbw-planning/phases/03-module-size-refactor/03-01-PLAN.md
  </files>
  <action>
Run the gate in one pass and record outputs for R05-SUMMARY.md. Fix nothing here: any failure belongs to task 1. This task specifies verification only, so the R05 summary records it as executed and does not describe its outcome as a deviation.

(1) The round's cumulative diff names no path other than 03-01-PLAN.md and no path outside .vbw-planning/. git status --porcelain shows no modified tracked file outside .vbw-planning/.
(2) grep -rnE "craftsman[-]ignore" server/ tests/ benchmark/ returns nothing. The amended 03-01-PLAN.md introduces no suppression instruction.
(3) The behavioral baseline holds at the untouched code state. pytest tests/ server/tests/ reports 316 passed, 1 skipped. ruff check server/ tests/ is clean.
(4) This plan's frontmatter carries known_issues_input: [] and known_issue_resolutions: [], so the deterministic registry gate sees a clear registry with no new entries.
(5) This plan's fail_classifications entry uses id FAIL-02, matching the ID column of the failing row in R03-VERIFICATION.md. It names source_plan 03-01-PLAN.md. The round's recorded paths include that file.
  </action>
  <verify>
All five checks pass in one fresh run. Command outputs are captured for R05-SUMMARY.md.
  </verify>
  <done>
The round is confined to 03-01-PLAN.md. No suppression token exists. The suite is green at the unchanged code state, the known-issues registry remains empty, and the classification matches the source verification row ID and an original plan artifact.
  </done>
</task>
</tasks>
<verification>
1. 03-01-PLAN.md contains exactly one Amendment (R05) note, placed in the context block after the Amendment (R02) block, marking FAIL-02 resolved-by-amendment, stating that the mislabeled entry recorded compliant gate behavior as a deviation, and citing commit a3e932b and the PASS result in R04-VERIFICATION.md.
2. Every other line of 03-01-PLAN.md is unchanged, and no round 01 through round 04 artifact, no 03-01-SUMMARY.md line, and no file outside .vbw-planning/ is modified by this round.
3. grep -rnE "craftsman[-]ignore" server/ tests/ benchmark/ returns nothing.
4. pytest tests/ server/tests/ reports 316 passed, 1 skipped, and ruff check server/ tests/ is clean.
5. R05-PLAN.md frontmatter classifies FAIL-02 as plan-amendment with source_plan 03-01-PLAN.md, its files_modified includes 03-01-PLAN.md, and it carries empty known_issues_input and known_issue_resolutions arrays.
6. Nothing in this plan or the amendment text predicts commit counts, tracking state, or diff contents beyond the constraints named in checks 1 through 3, and the R05 summary declares no deviation for the gate task's absent commit.
</verification>
<success_criteria>
- The phase's original plan carries the record that FAIL-02 is closed, citing the verified round 04 correction, so the deterministic gate's classification checks (row ID match, original-plan source_plan, and path coverage) are all satisfiable against this round.
- Round 04's work stands untouched: no round 02 through round 04 artifact is re-edited and no code changes.
- The round adds no suppression token, no known-issue registry entry, no declared deviation, and no factual claim a verifier could catch being false in a later round.
</success_criteria>
<known_issue_workflow>
- Always include `known_issues_input` and `known_issue_resolutions` in frontmatter. If there are no carried known issues, set both to empty arrays: `known_issues_input: []` and `known_issue_resolutions: []`.
- Copy every carried known issue from the remediation input backlog into `known_issues_input` using the canonical `{test,file,error}` shape.
- Add a matching `known_issue_resolutions` entry for every carried known issue. Use `resolved` when this round fixes it, `accepted-process-exception` when QA should treat it as a verified non-blocking carryover for this phase, and `unresolved` only when the issue is intentionally carried into the next round.
- Do not omit a carried known issue from these arrays. The deterministic gate treats missing coverage as a failed remediation round.
</known_issue_workflow>
<output>
R05-SUMMARY.md
</output>
